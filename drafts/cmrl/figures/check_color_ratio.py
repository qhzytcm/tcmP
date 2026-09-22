# -*- coding: utf-8 -*-
"""v4 颜色对齐后：统计 13 幅图彩色像素占比（口径 sat=max(r,g,b)-min(r,g,b)）"""
import numpy as np
import matplotlib.image as mpimg
import os

BASE = r'C:\Users\DELL\textbook-project\drafts\cmrl\figures'
files = [
    ('ch01', ['fig1-1.png', 'fig1-2.png', 'fig1-3.png', 'fig1-5.png', 'fig1-6.png']),
    ('ch02', ['fig2-1.png', 'fig2-2.png', 'fig2-3.png', 'fig2-4.png']),
    ('ch03', ['fig3-2.png', 'fig3-5.png', 'fig3-8.png', 'fig3-9.png']),
]

print(f"{'图':<12}{'尺寸(px)':<18}{'彩像>10':<12}{'占比>10%':<12}{'占比>20%':<12}")
print('-' * 66)
all_ok = True
for ch, fnames in files:
    for fn in fnames:
        path = os.path.join(BASE, ch, fn)
        img = mpimg.imread(path)
        if img.ndim == 3 and img.shape[2] == 4:
            alpha = img[:, :, 3]
            rgb = img[:, :, :3]
            mask = alpha > 0.5
        else:
            rgb = img[:, :, :3]
            mask = np.ones(rgb.shape[:2], dtype=bool)
        r = rgb[:, :, 0][mask]; g = rgb[:, :, 1][mask]; b = rgb[:, :, 2][mask]
        sat = np.maximum(np.maximum(r, g), b) - np.minimum(np.minimum(r, g), b)
        total = int(mask.sum())
        c10 = int((sat > 0.10).sum())
        c20 = int((sat > 0.20).sum())
        p10 = c10 / total * 100
        p20 = c20 / total * 100
        flag = 'OK' if p10 < 5.0 else '!!OVER!!'
        if p10 >= 5.0:
            all_ok = False
        h, w = img.shape[:2]
        print(f"{ch}/{fn:<9}{w}x{h:<14}{c10:<12}{p10:<12.3f}{p20:<12.3f}{flag}")

print('-' * 66)
print('彩色占比 <5% 校验:', '全部通过' if all_ok else '存在超限，需调整')
