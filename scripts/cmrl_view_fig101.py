# -*- coding: utf-8 -*-
"""查看 fig10-1 图体标注（Graphviz 节点）与 ch10 图注"""
import re
from pathlib import Path

# 1) fig10-1 Graphviz 生成脚本
for name in ('gen_ch_graphviz_redraw.py', 'gen_ch10_figures_feynman.py'):
    p = Path(r'C:\Users\DELL\textbook-project\drafts\cmrl\figures') / name
    if not p.exists():
        continue
    t = p.read_text(encoding='utf-8')
    m = re.search(r'fig10_1.*?(?=\ndef |\Z)', t, re.S)
    if not m:
        m = re.search(r'fig10-1.*?(?=\ndef |\Z)', t, re.S)
    if m:
        print(f'=== {name} fig10-1 段 ===')
        labels = re.findall(r'label=([\"\'])(.*?)\1', m.group(0), re.S)
        for _, l in labels[:20]:
            print('节点:', l.replace('\\n', ' / ').replace('<BR/>', ' / ')[:70])
        break

# 2) ch10 图注（fig10-1 对应）
print('\n=== ch10 fig10-1 图注 ===')
d = Path(r'C:\Users\DELL\textbook-project\drafts\cmrl\ch10')
for f in sorted(d.glob('0*-1.*.md')):
    for ln in f.read_text(encoding='utf-8').splitlines():
        if ln.strip().startswith('图注：') and '10-1' in ln:
            print(f'({f.name}):')
            print(ln.strip())
