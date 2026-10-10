# -*- coding: utf-8 -*-
"""核验 63-80 重建产物：docs/video 成片、旧 SW 归档、时长、docs 残留"""
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, r"C:\Users\DELL\tcmP\scripts")
from ch_names_81 import CH_NAMES_81

VD = Path(r"C:\Users\DELL\tcmP\docs\视频")
VIDEO = Path(r"C:\Users\DELL\textbook-project\drafts\cmrl\figures\book\video")
FF = r"C:\Tools\ffmpeg.exe"


def dur(p):
    try:
        r = subprocess.run([FF, "-i", str(p)], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=60)
        for line in ((r.stdout or "") + (r.stderr or "")).splitlines():
            if "Duration" in line:
                return line.split("Duration:")[1].split(",")[0].strip()
    except Exception:
        pass
    return "?"


print("篇  | docs成片(名/大小/时长)            | video新名 | 旧SW归档 | 残留SW")
ok = 0
for i in range(63, 81):
    name = CH_NAMES_81[i]
    d_mp4 = VD / f"素问{i:02d}-{name}.mp4"
    v_mp4 = VIDEO / f"素问{i:02d}-{name}.mp4"
    v_video = VIDEO / f"素问{i:02d}-{name}.video"
    old1 = VIDEO / "_legacy_sw" / f"素问{i}-SW{i}.mp4"
    old2 = VIDEO / "_legacy_sw" / f"素问{i}-SW{i}.video"
    resid = list(VD.glob(f"素问{i}*-SW*.mp4"))
    line = (f"{i:3d} | {d_mp4.name[:26]:26s} {d_mp4.stat().st_size//1048576 if d_mp4.exists() else 0:>3d}MB "
            f"{dur(d_mp4) if d_mp4.exists() else '—':>10s} | "
            f"{'✓' if v_mp4.exists() and v_video.exists() else '✗':^9s} | "
            f"{'✓' if old1.exists() and old2.exists() else '✗':^8s} | {resid or '无'}")
    print(line)
    if d_mp4.exists() and v_mp4.exists() and old1.exists() and not resid:
        ok += 1
print(f"\n完整篇数: {ok}/18")
