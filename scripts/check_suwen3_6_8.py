# -*- coding: utf-8 -*-
"""检查素问3 段6/8 talk 实际内容 + 总结结构"""
import json
import re
from pathlib import Path

import pandas as pd

segs = json.loads(Path(r'C:\Users\DELL\tcmP\docs\视频\segs_suwen3.json').read_text(encoding='utf-8'))
for i in (6, 8):
    s = segs[i - 1]
    print(f'段{i} [{s["title"]}] 原文{len(s["orig"])} 讲解{len(s["talk"])}: {s["talk"][:80]}')

# 看总结
df = pd.read_excel(r'C:\Users\DELL\Desktop\HDNJ音频理解(2).xls', sheet_name='3-生气通天论')
for v in df['文本内容'].dropna():
    t = str(v).strip()
    if t.startswith('总结-'):
        print('\n总结长度:', len(t))
        print(t[:400])
        break
