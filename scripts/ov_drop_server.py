"""ov_drop_server.py — 内网临时分发/回收服务（端口 8099，仅局域网）

GET  /bootstrap_desktop.ps1            -> 自举脚本
GET  /ov_custom_connectivity_test.py   -> 25 用例模板
GET  /llama_cpp_python-...whl          -> 离线 wheel（绕开被墙的 GitHub）
POST /upload/<filename>                -> 目标机回传报告/日志，落到桌面

白名单是 name -> 绝对路径 的显式映射：只有这三个名字可取，天然免疫路径穿越。
"""
import os
import sys
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPEC = {
    "bootstrap_desktop.ps1": os.path.join(REPO, "scripts", "bootstrap_desktop.ps1"),
    "connect_hermes_desktop.ps1": os.path.join(REPO, "scripts", "connect_hermes_desktop.ps1"),
    "ov_custom_connectivity_test.py": os.path.join(REPO, "scripts", "ov_custom_connectivity_test.py"),
    "llama_cpp_python-0.3.36-py3-none-win_amd64.whl":
        os.path.join(REPO, "deps", "ov", "llama_cpp_python-0.3.36-py3-none-win_amd64.whl"),
}
DROP = os.path.join(os.path.expanduser("~"), "Desktop")
PORT = 8099


class H(BaseHTTPRequestHandler):
    server_version = "ovdrop/1.0"

    def log_message(self, fmt, *args):
        line = "%s  %s\n" % (datetime.now().strftime("%H:%M:%S"), fmt % args)
        sys.stdout.write(line)
        sys.stdout.flush()
        try:
            with open(os.path.join(DROP, "ov_drop_access.log"), "a", encoding="utf-8") as f:
                f.write(line)
        except OSError:
            pass

    def _ok(self, data, body=True):
        self.send_response(200)
        self.send_header("Content-Type", "application/octet-stream")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        if body:
            self.wfile.write(data)

    def do_GET(self):
        self._serve(True)

    def do_HEAD(self):
        self._serve(False)

    def _serve(self, body):
        name = self.path.lstrip("/").split("?")[0]
        path = SPEC.get(name)
        if not path or not os.path.isfile(path):
            self.send_error(404, "not allowed")
            return
        with open(path, "rb") as f:
            self._ok(f.read(), body)

    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        name = os.path.basename(self.path.lstrip("/").split("?")[0]) or "upload.bin"
        out = os.path.join(DROP, "ov_drop_" + name)
        with open(out, "wb") as f:
            f.write(self.rfile.read(n) if n else b"")
        sys.stdout.write("RECV %s (%d bytes) -> %s\n" % (name, n, out))
        sys.stdout.flush()
        self._ok(b"OK")


if __name__ == "__main__":
    missing = [k for k, v in SPEC.items() if not os.path.isfile(v)]
    print("serving on 0.0.0.0:%d   drop -> %s" % (PORT, DROP))
    for k, v in SPEC.items():
        print("  %-40s %s" % (k, "OK" if os.path.isfile(v) else "MISSING: " + v))
    if missing:
        sys.exit("refusing to start, missing: %s" % missing)
    ThreadingHTTPServer(("0.0.0.0", PORT), H).serve_forever()
