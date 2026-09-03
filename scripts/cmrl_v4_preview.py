# -*- coding: utf-8 -*-
"""cmrl v4 目录结构预览：章/节/小节三级 + 字数预算（toc_rows() 输出）"""
import sys
from pathlib import Path

HERE = Path(r'C:\Users\DELL\textbook-project\scripts')
sys.path.insert(0, str(HERE))
from rl_v4_toc import toc_rows  # noqa: E402

rows = toc_rows()
print(f'总行数: {len(rows)}')
for r in rows:
    lvl, code, title = r[0], r[1], r[2]
    words = r[4]
    if lvl == '章':
        print(f"\n# {code} {title}  —— 预算 {words} 字")
    elif lvl == '节':
        print(f"    {code} {title}  ({words}字)")
    elif lvl == '小节':
        print(f"        {code} {title}  ({words}字)")
