# -*- coding: utf-8 -*-
"""长句语义群切分: 对无标点长 talk 按语义断点插入逗号（tcm-lecture-spirit 规范）"""
import json
import re
from pathlib import Path

D = Path(r'C:\Users\DELL\tcmP\docs\视频')

# 需切分的 (篇, 段号)
TARGETS = [(1, 3), (4, 6), (4, 7), (4, 9), (6, 4)]

# 语义断点词（其后可断句）
BREAKS = ('的', '了', '是', '在', '于', '与', '和', '而', '则', '者', '也',
          '之', '其', '以', '为', '如', '若', '故', '乃', '所', '因')


def split_long(talk):
    """将无标点长段按语义断点切分为语义群（逗号分隔, 每群 15-40 字）"""
    if '，' in talk[:200] or '。' in talk[:200]:
        return talk  # 已有标点
    out = []
    buf = ''
    for ch in talk:
        buf += ch
        if len(buf) >= 18 and buf[-1] in BREAKS:
            out.append(buf)
            buf = ''
    if buf:
        out.append(buf)
    return '，'.join(out)


for ch, seg_i in TARGETS:
    f = D / f'segs_suwen{ch}.json' if ch != 1 else D / 'segs.json'
    segs = json.loads(f.read_text(encoding='utf-8'))
    s = segs[seg_i - 1]
    old = s['talk']
    if '。' not in old[:80] and len(old) > 150:
        new = split_long(old)
        s['talk'] = new
        f.write_text(json.dumps(segs, ensure_ascii=False, indent=1), encoding='utf-8')
        print(f'素问{ch} 段{seg_i}: {len(old)}字 → 已切分({len(new)}字)')
        print(f'  前 90: {new[:90]}')
    else:
        print(f'素问{ch} 段{seg_i}: 已有标点或不长, 跳过')
