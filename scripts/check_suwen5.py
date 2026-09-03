# -*- coding: utf-8 -*-
"""检查 segs_suwen5 讲解质量"""
import json
from pathlib import Path

segs = json.loads(Path(r'C:\Users\DELL\tcmP\docs\视频\segs_suwen5.json').read_text(encoding='utf-8'))
for i, s in enumerate(segs, 1):
    flag = '⚠占位' if '（讲解）' in s['talk'] or len(s['talk']) < 50 else 'OK'
    print(f'{i}. {s["title"]} 原文{len(s["orig"])}字 讲解{len(s["talk"])}字 {flag}')
    if flag != 'OK':
        print('   talk:', s['talk'][:60])
