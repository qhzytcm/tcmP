# -*- coding: utf-8 -*-
"""验证 45 幅 GIF 已插入 Excel（media 计数 + 各 sheet 图片数）"""
import zipfile
from pathlib import Path
from openpyxl import load_workbook

X = Path(r'C:\Users\DELL\Desktop\强化学习的数学原理-赵世钰.xlsx')

with zipfile.ZipFile(X) as z:
    gifs = [n for n in z.namelist() if n.startswith('xl/media/') and n.endswith('.gif')]
    pngs = [n for n in z.namelist() if n.startswith('xl/media/') and n.endswith('.png')]
print(f'xl/media: GIF={len(gifs)} PNG={len(pngs)}')
for n in gifs[:5]:
    print(' ', n)

wb = load_workbook(X)
sheets = ['1cmrl-conceptions', '2cmrl-bellman', '3cmrl-optimality', '4cmrl-iteration',
          '5cmrl-montecarlo', '6cmrl-approximation', '7cmrl-tdlearning',
          '8cmrl-valuefunction', '9cmrl-policygradient', '10cmrl-acloop']
total = 0
for sn in sheets:
    n = len(getattr(wb[sn], '_images', None) or [])
    total += n
    print(f'{sn}: {n} 幅')
wb.close()
print(f'合计: {total} 幅 {"✅ 45/45" if total == 45 else f"⚠ {total}/45"}')
