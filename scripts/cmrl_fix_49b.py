# -*- coding: utf-8 -*-
"""压缩合并后的首段: 只保留 P1 定位句(前 60 字), 删除 P1 其余 → 400-600 字"""
from pathlib import Path
import re

D = Path(r'C:\Users\DELL\textbook-project\drafts\cmrl')
for ch in (1, 2, 3):
    f = D / f'ch{ch:02d}' / '01-1.1.md'
    lines = f.read_text(encoding='utf-8').splitlines()
    # 当前 P1 已被并入 P2: 找以【上编 开头的正文段（即合并后的 P2）
    for i, ln in enumerate(lines):
        s = ln.strip()
        if s.startswith('【上编'):
            # 截取定位句: 前 60 字
            loc = s[:60]
            rest = s[60:].lstrip(' ')
            # 找原 P2 起点: rest 中第一个句号后的内容即原 P2? 简单: 定位句 + 原 P2
            # 原 P2 = rest（保留, 但总长需 <=600）
            merged = loc + rest
            if len(merged) > 620:
                # 仍超长: 截 rest 至 600 字
                merged = loc + rest[:600 - len(loc) - 3] + '……'
            lines[i] = merged
            print(f'ch{ch:02d}: 定位句({len(loc)}字) + 原段, 现 {len(merged)} 字')
            break
    f.write_text('\n'.join(lines), encoding='utf-8')

# 验证段数与字数
for ch in (1, 2, 3):
    f = D / f'ch{ch:02d}' / '01-1.1.md'
    n = 0
    lens = []
    for ln in f.read_text(encoding='utf-8').splitlines():
        s = ln.strip()
        if not s or s.startswith(('#', '**图', '![', '图注：', '【图', '|')):
            continue
        if re.match(r'^###? ', s):
            continue
        n += 1
        lens.append(len(s))
    print(f'ch{ch:02d} 01-1.1.md: {n} 段, 字长={lens}')
