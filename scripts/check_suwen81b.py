# -*- coding: utf-8 -*-
"""检查 81 新 segs: 原文/讲解是否仍有异常"""
import json
from pathlib import Path

segs = json.loads(Path(r'C:\Users\DELL\tcmP\docs\视频\segs_suwen81.json').read_text(encoding='utf-8'))
for i, s in enumerate(segs, 1):
    print(f'{i}. 原文{len(s["orig"])}字 讲解{len(s["talk"])}字 | {s["talk"][:40]}')
