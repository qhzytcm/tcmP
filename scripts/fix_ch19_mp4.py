# -*- coding: utf-8 -*-
"""修复素问19 mp4：归档 12.4MB 旧版玉机真藏论.mp4，将 17.5MB 正式 SW19.mp4 正名"""
from pathlib import Path

VD = Path(r"C:\Users\DELL\tcmP\docs\视频")
BAK = VD / "_legacy_bak"
src_old = VD / "素问19-玉机真藏论.mp4"      # 12.4MB 09-01 旧独立文件
src_sw = VD / "素问19-SW19.mp4"             # 17.5MB batch 正式产物
dst = VD / "素问19-玉机真藏论.mp4"

if src_sw.exists() and src_old.exists():
    if src_old.stat().st_size < src_sw.stat().st_size:
        BAK.mkdir(exist_ok=True)
        src_old.rename(BAK / "素问19-玉机真藏论_旧独立版.mp4")
        src_sw.rename(dst)
        print("完成: 旧版归档, 正式版正名")
    else:
        print("意外: 旧版比 SW19 大, 未处理, 请人工核查")
else:
    print("文件状态异常:", src_sw.exists(), src_old.exists())
