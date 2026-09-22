# -*- coding: utf-8 -*-
"""Graphviz 重绘 5 幅结构图验证：尺寸 ≥600px 宽 + 彩色占比 <5%（口径 sat>0.10）"""
import os
import numpy as np
from PIL import Image

BASE = r'C:\Users\DELL\textbook-project\drafts\cmrl\figures'
files = [
    ('ch01', 'fig1-6.png', '双向映射环'),
    ('ch02', 'fig2-1.png', '五元组环+诊疗循环'),
    ('ch05', 'fig5-3.png', '策略迭代循环'),
    ('ch05', 'fig5-5.png', '统一算法循环'),
    ('ch06', 'fig6-4.png', '进化闭环'),
]

print(f"{'图':<10}{'尺寸(px)':<16}{'宽≥600':<10}{'彩像sat>0.10':<14}{'占比>10%':<12}{'占比>20%':<12}{'结果':<8}")
print('-' * 82)
all_ok = True
for ch, fn, name in files:
    path = os.path.join(BASE, ch, fn)
    im = Image.open(path)
    arr = np.asarray(im.convert('RGBA'))
    w, h = im.size
    alpha = arr[:, :, 3]
    rgb = arr[:, :, :3].astype(float) / 255.0
    mask = alpha > 0.5
    r = rgb[:, :, 0][mask]; g = rgb[:, :, 1][mask]; b = rgb[:, :, 2][mask]
    sat = np.maximum(np.maximum(r, g), b) - np.minimum(np.minimum(r, g), b)
    total = int(mask.sum())
    c10 = int((sat > 0.10).sum())
    c20 = int((sat > 0.20).sum())
    p10 = c10 / total * 100 if total else 0
    p20 = c20 / total * 100 if total else 0
    wok = w >= 600
    pok = p10 < 5.0
    ok = wok and pok
    if not ok:
        all_ok = False
    print(f"{ch}/{fn:<7}{w}x{h:<12}{'✓' if wok else '✗':<10}{c10:<14}{p10:<12.3f}{p20:<12.3f}{'OK' if ok else '!!FAIL!!'}")

print('-' * 82)
print('验证结论:', '全部通过' if all_ok else '存在未达标项')
