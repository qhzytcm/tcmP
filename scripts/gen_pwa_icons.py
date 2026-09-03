# -*- coding: utf-8 -*-
"""生成 PWA 图标（192/512 PNG）"""
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

OUT = Path(r'C:\Users\DELL\tcmP\docs\视频\icons')
OUT.mkdir(exist_ok=True)
FONT = r'C:\Windows\Fonts\msyhbd.ttc'

for size in (192, 512):
    img = Image.new('RGBA', (size, size), '#1e8449')
    d = ImageDraw.Draw(img)
    # 圆角背景
    mask = Image.new('L', (size, size), 0)
    md = ImageDraw.Draw(mask)
    md.rounded_rectangle([0, 0, size, size], radius=size // 5, fill=255)
    img.putalpha(mask)
    # "素问" 文字
    f = ImageFont.truetype(FONT, int(size * 0.42))
    t1 = '素问'
    t2 = '上古天真论'
    f2 = ImageFont.truetype(FONT, int(size * 0.13))
    w1 = d.textlength(t1, font=f)
    d.text(((size - w1) / 2, size * 0.28), t1, font=f, fill='#fdf9ef')
    w2 = d.textlength(t2, font=f2)
    d.text(((size - w2) / 2, size * 0.72), t2, font=f2, fill='#cfe8d8')
    img.save(OUT / f'icon-{size}.png')
    print(f'图标 {size}: OK')
