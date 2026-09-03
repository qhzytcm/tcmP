# -*- coding: utf-8 -*-
"""诊断 ch01-03 的 49 段: 找出多出的一段（对照 24 小节×2 段结构）"""
import re
from pathlib import Path

D = Path(r'C:\Users\DELL\textbook-project\drafts\cmrl')
for ch in (1, 2, 3):
    files = sorted((D / f'ch{ch:02d}').glob('0*-1.*.md'))
    total = 0
    print(f'===== ch{ch:02d} =====')
    for f in files:
        lines = f.read_text(encoding='utf-8').splitlines()
        paras = []
        for ln in lines:
            s = ln.strip()
            if not s or s.startswith(('#', '**图', '![', '图注：', '【图', '|')):
                continue
            if re.match(r'^###? ', s):
                continue
            paras.append(s)
        total += len(paras)
        if len(paras) != 6:   # 3 小节 × 2 段 = 6
            print(f'  {f.name}: {len(paras)} 段 (预期 6)')
            # 打印段落首 20 字找多出的
            for i, p in enumerate(paras, 1):
                print(f'    P{i}: {p[:28]}')
    print(f'  合计: {total} 段')
