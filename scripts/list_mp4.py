# -*- coding: utf-8 -*-
"""找出 docs/视频 中所有 mp4 并标记非规范名"""
import sys, re
from pathlib import Path
sys.path.insert(0, r"C:\Users\DELL\tcmP\scripts")
from ch_names_81 import CH_NAMES_81

VD = Path(r"C:\Users\DELL\tcmP\docs\视频")
for f in sorted(VD.glob("素问*.mp4")):
    m = re.match(r"^素问0?(\d+)-(.+)\.mp4$", f.name)
    ok = False
    if m:
        ch = int(m.group(1))
        expect = f"素问{ch:02d}-{CH_NAMES_81.get(ch, '?')}.mp4"
        ok = f.name == expect
    print(("OK  " if ok else "BAD ") + f.name + f"  ({f.stat().st_size} B)")
