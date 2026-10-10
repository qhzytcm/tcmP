# -*- coding: utf-8 -*-
"""归档 docs/视频 中残留的 素问*-SW*.mp4（旧命名）到 _legacy_bak"""
import re
import sys
from pathlib import Path

sys.path.insert(0, r"C:\Users\DELL\tcmP\scripts")
from ch_names_81 import CH_NAMES_81

VD = Path(r"C:\Users\DELL\tcmP\docs\视频")
BAK = VD / "_legacy_bak"
BAK.mkdir(exist_ok=True)
moved = []
for f in sorted(VD.glob("素问*-SW*.mp4")):
    m = re.match(r"^素问(\d+)-SW\d+\.mp4$", f.name)
    if not m:
        continue
    ch = int(m.group(1))
    new = VD / f"素问{ch:02d}-{CH_NAMES_81[ch]}.mp4"
    if not new.exists():
        print(f"⚠ {f.name} 无规范名对应, 跳过")
        continue
    dst = BAK / (f.stem + "_旧SW版.mp4")
    if dst.exists():
        dst = BAK / (f.stem + "_旧SW版2.mp4")
    f.replace(dst)
    moved.append(f.name)
print(f"归档 {len(moved)} 个: {moved}")
# 复查
left = [f.name for f in VD.glob("素问*-SW*.mp4")]
print("残留:", left or "无 ✓")
