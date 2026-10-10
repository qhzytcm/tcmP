#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""服务端幂等注入：把 /semtensor/* 挂进 sage-api/main.py（可重复执行）。"""
import datetime
import re
import shutil
import sys
from pathlib import Path

MAIN = Path("/var/www/tcm-dashboard/sage-api/main.py")
MARK = "semtensor_router"
BLOCK = '''
# ── 语义张量：/semtensor/* ─────────────────────────────────────────────
try:
    from semtensor_router import router as _semtensor_router
    app.include_router(_semtensor_router)
except Exception as _e:
    import logging
    logging.getLogger("uvicorn").warning(f"semtensor not mounted: {_e}")
# ──────────────────────────────────────────────────────────────────────

'''


def main() -> int:
    if not MAIN.exists():
        print("[x] not found: %s" % MAIN); return 1
    src = MAIN.read_text(encoding="utf-8")
    if MARK in src:
        print("[=] mount block already present (idempotent, skip)"); return 0
    m = re.search(r'^if __name__ == ["\']__main__["\']\s*:', src, re.M)
    if not m:
        print("[x] anchor 'if __name__' not found"); return 1
    bak = MAIN.with_suffix(".bak.sem.%s" % datetime.datetime.now().strftime("%Y%m%d%H%M%S"))
    shutil.copy2(MAIN, bak)
    MAIN.write_text(src[:m.start()] + BLOCK + src[m.start():], encoding="utf-8")
    print("[+] injected (backup=%s)" % bak.name)
    return 0


if __name__ == "__main__":
    sys.exit(main())