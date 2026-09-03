# -*- coding: utf-8 -*-
"""检查 45 条图注颜色词 vs 图体实际点缀色（对齐性诊断）"""
import re
from pathlib import Path
from PIL import Image

D = Path(r'C:\Users\DELL\textbook-project\drafts\cmrl')
F = D / 'figures'
COLORS = {'蓝': 'blue', '绿': 'green', '橙': 'orange', '红': 'red',
          '紫': 'purple', '黄': 'yellow', '灰': 'gray', '黑': 'black'}

color_words = []
for ch in range(1, 11):
    for f in sorted((D / f'ch{ch:02d}').glob('0*-1.*.md')):
        for ln in f.read_text(encoding='utf-8').splitlines():
            s = ln.strip()
            if not s.startswith('图注：'):
                continue
            # 找图注对应的图文件（md 里 ![ ](figures/chNN/figN-X.png)）
            fig = None
            for ln2 in f.read_text(encoding='utf-8').splitlines():
                m = re.search(r'figures/ch\d+/(fig\d+-\d+\.png)', ln2)
                if m:
                    fig = m.group(1)
                    break
            found = [c for c in COLORS if c in s]
            color_words.append((ch, f.name, fig, found))

print(f'{"章":<4}{"图":<14}{"图注颜色词":<20}{"图体彩色%"}')
print('-' * 60)
for ch, fname, fig, found in color_words:
    if not found:
        continue
    ratio = 0.0
    if fig:
        p = F / f'ch{ch:02d}' / fig
        if p.exists():
            img = Image.open(p).convert('RGB')
            px = img.resize((200, 200)).getdata()
            ratio = sum(1 for r, g, b in px if max(r, g, b) - min(r, g, b) > 40) / (200 * 200) * 100
    print(f'ch{ch:<3}{fig or fname:<14}{"/".join(found):<20}{ratio:.1f}%')
