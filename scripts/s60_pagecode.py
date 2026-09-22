# -*- coding: utf-8 -*-
"""S60 生成「1182 页 → 原书页码编码」映射表 dist/pdf3_pagecode.json"""
import json, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, 'dist')
TOTAL = 1182
SEG = [('前置', 0, 11, None),
       ('目录', 12, 58, 47),
       ('正文', 59, 1176, 1118),
       ('增补', 1177, 1179, 3),
       ('尾页', 1180, 1181, None)]
# 1) 结构闭合校验
n = sum(b - a + 1 for _, a, b, _ in SEG)
seg_ok = all((cnt is None or (b - a + 1) == cnt) for _, a, b, cnt in SEG)
assert n == TOTAL and seg_ok, (n, seg_ok)

# 2) 逐页编码
pages = {}
for name, a, b, cnt in SEG:
    for i, pg in enumerate(range(a, b + 1)):
        if name == '目录':
            pages[pg] = {'seg': '目录', 'code': f'病源辞典 目录 {i+1:02d}'}
        elif name == '正文':
            pages[pg] = {'seg': '正文', 'code': f'病源辞典 <笔画> <首字> {i+1:04d}', 'n': i + 1}
        elif name == '增补':
            pages[pg] = {'seg': '增补', 'code': f'病源辞典 <笔画> <首字> {1119+i:04d}', 'n': 1119 + i}
        else:
            pages[pg] = {'seg': name, 'code': name}
out = {'total': TOTAL, 'segments': [{'seg': s, 'scan': [a, b], 'pages': (b - a + 1), 'count': c}
                                    for s, a, b, c in SEG],
       'pages': {str(k): v for k, v in sorted(pages.items())}}
json.dump(out, open(os.path.join(DIST, 'pdf3_pagecode.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print('段闭合:', n, '==', TOTAL, '✓ | 各段页数匹配:', seg_ok, '✓')
for s, a, b, c in SEG:
    print(f'  {s}: 扫描 {a}-{b} = {b-a+1} 页' + (f'（原书编码数 {c}）' if c else ''))
print('首末样本:', pages[12]['code'], '|', pages[58]['code'], '|', pages[59]['code'], '|', pages[1179]['code'])
print('→', os.path.join(DIST, 'pdf3_pagecode.json'), os.path.getsize(os.path.join(DIST, 'pdf3_pagecode.json')), 'bytes')
