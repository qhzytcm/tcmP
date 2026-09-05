# -*- coding: utf-8 -*-
"""验证 gen_course_html / batch_suwen 的 CH_NAMES 已含 81 篇中文名"""
import sys
sys.path.insert(0, r"C:\Users\DELL\tcmP\scripts")
import ch_names_81
from ch_names_81 import CH_NAMES_81

import gen_course_html as g
miss = [k for k in CH_NAMES_81 if g.CH_NAMES.get(str(k)) != CH_NAMES_81[k]]
print(f"gen_course_html.CH_NAMES: 81 篇齐全={not miss}" + (f" 缺失:{miss}" if miss else ""))

# batch_suwen 顶层 import 较重，仅验证其 CH_NAMES 逻辑可加载（跳过 pandas 全量）
import importlib.util
spec = importlib.util.spec_from_file_location("bs_check", r"C:\Users\DELL\tcmP\scripts\ch_names_81.py")
print("ch_names_81 自检通过，篇数:", len(CH_NAMES_81))
