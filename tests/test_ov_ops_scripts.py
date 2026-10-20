# -*- coding: utf-8 -*-
"""OpenViking 运维脚本的契约测试（ov_drop_server 分发服务 + 两个 PowerShell 自举脚本）。

这两类文件此前只能靠手工 shell 命令验证，pytest 覆盖不到，故这里补上：
- ov_drop_server：白名单、路径穿越拦截、POST 落盘（真起一个临时 HTTP 服务）
- *.ps1：语法解析（调 PowerShell Parser）+ 关键不变量（BOM-less、trap、幂等 .env…）
"""
import http.client
import importlib.util
import sys
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
SCRIPTS = REPO / "scripts"
SERVER_PY = SCRIPTS / "ov_drop_server.py"


def _load_server():
    spec = importlib.util.spec_from_file_location("ov_drop_server_under_test", SERVER_PY)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def srv_mod():
    assert SERVER_PY.exists(), SERVER_PY
    return _load_server()


@pytest.fixture()
def live(srv_mod, tmp_path, monkeypatch):
    """临时起一个只读分发服务；DROP 指向 tmp_path，日志静音。"""
    monkeypatch.setattr(srv_mod, "DROP", str(tmp_path))
    monkeypatch.setattr(srv_mod.H, "log_message", lambda *a, **k: None)
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), srv_mod.H)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    try:
        yield httpd.server_address[1], srv_mod
    finally:
        httpd.shutdown()
        httpd.server_close()


def _get(port, path):
    c = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
    try:
        c.request("GET", path)
        r = c.getresponse()
        return r.status, r.read()
    finally:
        c.close()


# ---------- ov_drop_server ----------

def test_spec_whitelist_all_exist(srv_mod):
    assert srv_mod.SPEC, "SPEC 不能为空"
    missing = [n for n, p in srv_mod.SPEC.items() if not Path(p).is_file()]
    assert not missing, f"白名单里的文件不存在: {missing}"


def test_spec_covers_both_bootstraps(srv_mod):
    assert "bootstrap_desktop.ps1" in srv_mod.SPEC
    assert "connect_hermes_desktop.ps1" in srv_mod.SPEC


@pytest.mark.parametrize("name", ["bootstrap_desktop.ps1",
                                 "connect_hermes_desktop.ps1",
                                 "ov_custom_connectivity_test.py"])
def test_serve_allowed(live, name):
    port, mod = live
    status, body = _get(port, "/" + name)
    assert status == 200
    assert len(body) == Path(mod.SPEC[name]).stat().st_size


def test_serve_unknown_404(live):
    port, _ = live
    assert _get(port, "/hosts")[0] == 404


def test_serve_traversal_blocked(live):
    port, _ = live
    assert _get(port, "/../scripts/ov_drop_server.py")[0] == 404
    assert _get(port, "/..%2f..%2fetc%2fpasswd")[0] == 404


def test_post_roundtrip(live, tmp_path):
    port, _ = live
    payload = b"xlsx-bytes\x00\x01"
    c = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
    try:
        c.request("POST", "/upload/OV-test-probe.xlsx", body=payload)
        assert c.getresponse().status == 200
    finally:
        c.close()
    saved = tmp_path / "ov_drop_OV-test-probe.xlsx"
    assert saved.exists() and saved.read_bytes() == payload


# ---------- PowerShell 脚本 ----------

PS_SCRIPTS = [SCRIPTS / "bootstrap_desktop.ps1", SCRIPTS / "connect_hermes_desktop.ps1"]


@pytest.mark.skipif(sys.platform != "win32", reason="需要 PowerShell 解析器")
@pytest.mark.parametrize("ps", PS_SCRIPTS, ids=lambda p: p.name)
def test_ps_parses_without_errors(ps):
    import subprocess
    assert ps.exists(), ps
    cmd = (
        "$e=$null;"
        f"[System.Management.Automation.Language.Parser]::ParseFile('{ps}',[ref]$null,[ref]$e)|Out-Null;"
        "if($e.Count){$e|%{$_.Message};exit 1}else{'OK'}"
    )
    r = subprocess.run(["powershell", "-NoProfile", "-Command", cmd],
                       capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, r.stdout + r.stderr


def test_bootstrap_invariants():
    s = (SCRIPTS / "bootstrap_desktop.ps1").read_text(encoding="utf-8")
    # ov.conf 必须写成无 BOM，否则 OpenViking 报 "expected value at line 1 column 1"
    assert "[System.IO.File]::WriteAllText" in s
    assert "UTF8Encoding($false)" in s
    assert 'Set-Content -Path (Join-Path $ovDir "ov.conf")' not in s
    # 写盘后必须自检 JSON，失败即 die（别等 3 分钟才在 server log 里发现）
    assert "CONF_JSON_OK" in s and "is not valid JSON" in s
    # 兜底：任何终止性错误都要带行号并回传日志
    assert "trap {" in s and "UNHANDLED ERROR" in s
    assert "function UploadLog" in s
    # 服务起不来时快速失败，而不是干等满轮询
    assert "server process exited at attempt" in s
    # Hermes 接入必须委托给 connect_hermes_desktop.ps1，逻辑只留一份（否则两边会分叉）
    assert "connect_hermes_desktop.ps1" in s
    assert "delegating memory wiring" in s


def test_connect_invariants():
    s = (SCRIPTS / "connect_hermes_desktop.ps1").read_text(encoding="utf-8")
    assert '@("config","set","memory.provider","openviking")' in s
    for k in ("OPENVIKING_ENDPOINT", "OPENVIKING_ACCOUNT", "OPENVIKING_USER", "OPENVIKING_AGENT"):
        assert k in s, k
    assert "ENV ALREADY_PRESENT" in s          # 幂等追加
    assert "bak.$stamp" in s                   # 改配置前备份
    assert r"Provider:\s*openviking" in s      # 自验证，不通过就停
    assert "trap {" in s and "function UploadLog" in s
