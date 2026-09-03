# -*- coding: utf-8 -*-
"""ch01-03 章首定位段并入 1.1 小节首段（恢复 48 段结构, 保留编级定位）"""
from pathlib import Path

D = Path(r'C:\Users\DELL\textbook-project\drafts\cmrl')
for ch in (1, 2, 3):
    f = D / f'ch{ch:02d}' / '01-1.1.md'
    lines = f.read_text(encoding='utf-8').splitlines()
    # 找 P1（【上编·提高认知】开头段）与 P2（其后第一个正文段）
    p1_idx = None
    p2_idx = None
    paras = []
    for i, ln in enumerate(lines):
        s = ln.strip()
        if not s or s.startswith(('#', '**图', '![', '图注：', '【图', '|')):
            continue
        paras.append((i, s))
    # paras[0] = P1, paras[1] = P2（若 P1 以【上编 开头）
    if paras and paras[0][1].startswith('【上编'):
        p1_idx, p1 = paras[0]
        p2_idx, p2 = paras[1]
        merged = p1 + ' ' + p2
        # 替换 P2 行内容为合并文本, 删除 P1 行
        lines[p2_idx] = merged
        lines[p1_idx] = ''
        f.write_text('\n'.join(lines), encoding='utf-8')
        print(f'ch{ch:02d}: P1({len(p1)}字) 并入 P2, 现 {len(merged)} 字')
    else:
        print(f'ch{ch:02d}: 未找到章首定位段')

# 验证段数
import re
for ch in (1, 2, 3):
    f = D / f'ch{ch:02d}' / '01-1.1.md'
    n = 0
    for ln in f.read_text(encoding='utf-8').splitlines():
        s = ln.strip()
        if not s or s.startswith(('#', '**图', '![', '图注：', '【图', '|')):
            continue
        if re.match(r'^###? ', s):
            continue
        n += 1
    print(f'ch{ch:02d} 01-1.1.md: {n} 段')
