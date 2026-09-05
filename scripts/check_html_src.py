# -*- coding: utf-8 -*-
"""html 视频引用检查：轻量版 <source src=mp4> 文件存在性；授课版 data URI + fallback"""
import re
from pathlib import Path
import sys
sys.path.insert(0, r"C:\Users\DELL\tcmP\scripts")
from ch_names_81 import CH_NAMES_81

VD = Path(r"C:\Users\DELL\tcmP\docs\视频")
bad = []
n_light = n_teach = 0
for i in range(1, 82):
    ch = f"{i:02d}"
    name = CH_NAMES_81[i]
    light = VD / f"素问{ch}-{name}-视频课程.html"
    teach = VD / f"素问{ch}-{name}-视频授课.html"
    if not light.exists() or not teach.exists():
        bad.append((f"素问{ch}", "缺文件"))
        continue
    n_light += 1
    n_teach += 1
    lt = light.read_text(encoding="utf-8", errors="ignore")
    m = re.search(r'<source src="([^"]+\.mp4)" type="video/mp4">', lt)
    if not m:
        bad.append((f"素问{ch} 轻量", "无 source"))
        continue
    ref = m.group(1)
    if not (VD / ref).exists():
        bad.append((f"素问{ch} 轻量", f"断链: {ref}"))
    tt = teach.read_text(encoding="utf-8", errors="ignore")
    if "data:video/mp4;base64," not in tt:
        bad.append((f"素问{ch} 授课", "无 data URI"))
    # fallback 外链存在?
    mf = re.findall(r'<source src="([^"]+\.mp4)" type="video/mp4">', tt)
    for ref2 in mf:
        if ref2.startswith("data:"):
            continue
        if not (VD / ref2).exists():
            bad.append((f"素问{ch} 授课", f"断链: {ref2}"))
print(f"轻量版检查 {n_light} 个, 授课版检查 {n_teach} 个")
print("问题:", bad if bad else "全部通过 ✓")
