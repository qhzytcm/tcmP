# -*- coding: utf-8 -*-
"""深度自查①: 口语噪音扫描（填充词/口头禅——讲课神韵杀手）"""
import json
import re
from pathlib import Path

D = Path(r'C:\Users\DELL\tcmP\docs\视频')

# 口语填充词（转写特征）
FILLERS = ['嗯', '啊', '那个', '然后', '就是说', '对不对', '对吧', '是不是',
           '这个这个', '就是', '反正', '其实', '基本上', '那那', '对对对',
           '诶', '哦', '哈', '吧', '嘛', '呢', '你看', '我们看', '你看这个']

print('===== 口语噪音扫描（全部 19 篇）=====')
total_fill = 0
for ch in range(1, 20):
    f = D / f'segs_suwen{ch}.json' if ch != 1 else D / 'segs.json'
    if not f.exists():
        continue
    segs = json.loads(f.read_text(encoding='utf-8'))
    ch_fill = 0
    bad_segs = []
    for i, s in enumerate(segs, 1):
        talk = s.get('talk', '')
        n = 0
        for fw in FILLERS:
            n += talk.count(fw)
        if n > 0:
            ch_fill += n
            bad_segs.append((i, n))
    if ch_fill:
        print(f'素问{ch}: 填充词 {ch_fill} 处 {bad_segs[:4]}')
        total_fill += ch_fill
print(f'\n总填充词: {total_fill} 处')
