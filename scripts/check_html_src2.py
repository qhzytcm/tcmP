# -*- coding: utf-8 -*-
"""html 视频引用检查 v2（授课版大文件仅读头部，避免超时）"""
import re
import sys
from pathlib import Path

sys.path.insert(0, r"C:\Users\DELL\tcmP\scripts")
from ch_names_81 import CH_NAMES_81

VD = Path(r"C:\Users\DELL\tcmP\docs\视频")
bad = []


def head(p, n=12000):
    with open(p, "r", encoding="utf-8", errors="ignore") as fh:
        return fh.read(n)


for i in range(1, 82):
    ch, name = f"{i:02d}", CH_NAMES_81[i]
    light = VD / f"素问{ch}-{name}-视频课程.html"
    teach = VD / f"素问{ch}-{name}-视频授课.html"
    if not (light.exists() and teach.exists()):
        bad.append((f"素问{ch}", "缺文件"))
        continue
    lt = light.read_text(encoding="utf-8", errors="ignore")
    m = re.search(r'<source src="([^"]+\.mp4)" type="video/mp4">', lt)
    if not m:
        bad.append((f"素问{ch} 轻量", "无 mp4 source"))
    elif not (VD / m.group(1)).exists():
        bad.append((f"素问{ch} 轻量", f"断链 {m.group(1)}"))
    # 授课版：头部含 data URI 与 fallback mp4 引用
    th = head(teach)
    if "data:video/mp4;base64," not in th:
        bad.append((f"素问{ch} 授课", "头部无 data URI"))
    mf = re.findall(r'<source src="([^"]+\.mp4)" type="video/mp4">', th)
    for ref in mf:
        if not (VD / ref).exists():
            bad.append((f"素问{ch} 授课", f"断链 {ref}"))

print(f"检查 81 篇 × 2 版本")
print("问题:", bad if bad else "全部通过 ✓")
