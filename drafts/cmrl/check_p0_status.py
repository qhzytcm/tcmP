# -*- coding: utf-8 -*-
"""P0 9 项现状核查（压缩期部分已修订, 查残留）"""
import re
from pathlib import Path

CMRL = Path(r'C:\Users\DELL\textbook-project\drafts\cmrl')


def grep(pattern, root=CMRL, name_filter='', maxhits=3):
    hits = []
    for f in sorted(root.rglob('*.md')):
        if name_filter and name_filter not in f.name:
            continue
        try:
            txt = f.read_text(encoding='utf-8', errors='ignore')
        except Exception:
            continue
        for m in re.finditer(pattern, txt):
            s = max(0, m.start() - 25)
            hits.append((str(f.relative_to(CMRL)), txt[s:m.end() + 25].replace('\n', ' ')[:80]))
            if len(hits) >= maxhits:
                return hits
    return hits


print('P0-1 ch05 例5.6 乙回报 1.71 残留?')
for h in grep(r'1\.71'):
    print('   ', h)

print('\nP0-2 ch06 例6.1 0.0261 残留?')
for h in grep(r'0\.0261'):
    print('   ', h)

print('\nP0-3 ch07 失眠加权 0.78 残留?')
for h in grep(r'0\.78', name_filter='ch07'):
    print('   ', h)

print('\nP0-4 ch03 麻黄汤约87% 残留?')
for h in grep(r'87%|约87'):
    print('   ', h)

print('\nP0-5 ch04 4.3.1 风热+麻黄汤 残留?')
for h in grep(r'风热[^。]{0,20}麻黄汤|麻黄汤[^。]{0,15}风热'):
    print('   ', h)

print('\nP0-6 三种最适度英文 individual positioning 使用:')
for h in grep(r'individual positioning|individualized positioning|individual positioning|optimal adaptation', maxhits=6):
    print('   ', h)

print('\nP0-7 ch05 例5.4 s6 向右 残留?')
for h in grep(r's6[^。]{0,12}向右|向右[^。]{0,12}s6|s6[^。]{0,15}下'):
    print('   ', h)

print('\nP0-8 ch03 例3.6 存在?')
for h in grep(r'例3\.6', maxhits=5):
    print('   ', h)

print('\nP0-9 ch09 9.2.2 梯度口径:')
for h in grep(r'0\.495|0\.494|0\.5[0-9]0', name_filter='ch09', maxhits=8):
    print('   ', h)
