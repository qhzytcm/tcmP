# -*- coding: utf-8 -*-
"""【在服务器上运行】把中医知识树路由幂等注入 sage-api/main.py 并重启服务。
用法（华为云）：/root/.local/share/uv/tools/hermes-agent/bin/python3 /tmp/_server_mount_tree.py
"""
from __future__ import annotations

import shutil
import subprocess
import time
from pathlib import Path

BASE = Path("/var/www/tcm-dashboard")
MAIN = BASE / "sage-api" / "main.py"
PY = "/root/.local/share/uv/tools/hermes-agent/bin/python3"

BLOCK = """
# ── 中医知识树挂载（由 scripts/build_knowledge_tree.py 生成，幂等且失败不阻断）──
try:
    from tree_router import router as _tree_router
    app.include_router(_tree_router)
    print("🌳 中医知识树已挂载: /tree/*")
except Exception as _e:  # noqa: BLE001
    import logging
    logging.getLogger("uvicorn").warning(f"knowledge-tree not mounted: {_e}")

"""


def main() -> int:
    if not MAIN.exists():
        print("!! main.py 不存在：", MAIN)
        return 1
    src = MAIN.read_text(encoding="utf-8")
    if "tree_router" in src:
        print("main.py 已含中医知识树挂载块，跳过注入")
    else:
        bak = MAIN.with_suffix(f".py.bak.tree.{time.strftime('%Y%m%d%H%M%S')}")
        shutil.copy2(MAIN, bak)
        for marker in ("# ── 启动 ──", "if __name__"):
            if marker in src:
                src = src.replace(marker, BLOCK + marker, 1)
                break
        else:
            src = src + BLOCK
        MAIN.write_text(src, encoding="utf-8")
        print(f"main.py 已注入挂载块（备份 {bak.name}）")

    r = subprocess.run([PY, "-m", "py_compile", str(MAIN)], capture_output=True, text=True)
    print("py_compile rc:", r.returncode, (r.stderr or "")[-400:])
    if r.returncode != 0:
        return 2

    subprocess.run(["systemctl", "restart", "sage-api"])
    time.sleep(3)
    st = subprocess.run(["systemctl", "is-active", "sage-api"], capture_output=True, text=True)
    print("sage-api active:", st.stdout.strip())
    lg = subprocess.run(["bash", "-lc", "tail -n 8 /var/log/sage-api.log"], capture_output=True, text=True)
    print("--- sage-api.log tail ---")
    print(lg.stdout)
    return 0 if st.stdout.strip() == "active" else 3


if __name__ == "__main__":
    raise SystemExit(main())
