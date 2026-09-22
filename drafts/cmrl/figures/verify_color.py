# -*- coding: utf-8 -*-
"""彩色像素占比校验：图注颜色对齐后，每幅图彩色像素占比 <5%。
判定：HSV 饱和度 S>0.12 且亮度 V>0.15 的像素视为彩色像素。
用法：python verify_color.py [目录...]  默认校验 ch07~ch10
"""
import os
import sys
from PIL import Image

ROOT = os.path.dirname(os.path.abspath(__file__))
CHS = ['ch07', 'ch08', 'ch09', 'ch10'] if len(sys.argv) < 2 else sys.argv[1:]


def sat_ratio(path, s_th=0.12, v_min=0.15):
    im = Image.open(path).convert('RGB')
    im = im.resize((im.width // 2, im.height // 2))
    hsv = im.convert('HSV')
    px = list(hsv.getdata())
    total = len(px)
    color = sum(1 for h, s, v in px if s > s_th * 255 and v > v_min * 255)
    return 100.0 * color / total


def main():
    fails = []
    for ch in CHS:
        d = os.path.join(ROOT, ch)
        if not os.path.isdir(d):
            print('SKIP', ch, '(no dir)')
            continue
        for f in sorted(os.listdir(d)):
            if not f.endswith('.png'):
                continue
            p = os.path.join(d, f)
            r = sat_ratio(p)
            flag = 'PASS' if r < 5.0 else 'FAIL'
            if r >= 5.0:
                fails.append((ch, f, r))
            print('%s %s/%s sat=%.2f%%' % (flag, ch, f, r))
    if fails:
        print('FAIL:', fails)
        sys.exit(1)
    print('VERDICT: ALL PASS (<5%)')


if __name__ == '__main__':
    main()
