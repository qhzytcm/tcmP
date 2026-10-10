#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""服务端幂等注入：把 /informatics/* 挂进 sage-api/main.py（可重复执行）。"""
import datetime
import re
import shutil
import sys
from pathlib import Path

MAIN = Path("/var/www/tcm-dashboard/sage-api/main.py")
MARK = "informatics_router"

BLOCK = '''
# ── 中医信息学：/informatics/* ─────────────────────────────────────────
try:
    from informatics_router import router as _informatics_router
    app.include_router(_informatics_router)
except Exception as _e:
    import logging
    logging.getLogger("uvicorn").warning(f"informatics not mounted: {_e}")
# ──────────────────────────────────────────────────────────────────────

'''


def main() -> int:
    if not MAIN.exists():
        print(f"[x] not found: {MAIN}")
        return 1
    src = MAIN.read_text(encoding="utf-8")
    if MARK in src:
        print("[=] mount block already present (idempotent, skip)")
        return 0
    anchor = re.search(r'^if __name__ == ["\']__main__["\']\s*:', src, re.M)
    if not anchor:
        print("[x] anchor 'if __name__' not found")
        return 1
    bak = MAIN.with_suffix(f".bak.info.{datetime.datetime.now():%Y%m%d%H%M%S}")
    shutil.copy2(MAIN, bak)
    new = src[:anchor.start()] + BLOCK + src[anchor.start():]
    MAIN.write_text(new, encoding="utf-8")
    print(f"[+] injected (backup={bak.name})")
    return 0


if __name__ == "__main__":
    sys.exit(main())