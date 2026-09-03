# -*- coding: utf-8 -*-
"""检查 segs_suwen81 内容质量"""
import json
from pathlib import Path

segs = json.loads(Path(r'C:\Users\DELL\tcmP\docs\视频\segs_suwen81.json').read_text(encoding='utf-8'))
for i, s in enumerate(segs, 1):
    print(f'{i}. [{s["title"]}] 原文{len(s["orig"])}字 讲解{len(s["talk"])}字')
    if i <= 3:
        print(f'   原文: {s["orig"][:60]}')
        print(f'   讲解: {s["talk"][:60]}')
