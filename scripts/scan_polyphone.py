# -*- coding: utf-8 -*-
"""扫描 81 篇 segs 医学多音字分布（脏/藏象/恶寒/相傅 等）"""
import json
import re
from pathlib import Path

D = Path(r'C:\Users\DELL\tcmP\docs\视频')

# 关注词（含读音歧义）
WORDS = ['脏腑', '五脏', '心脏', '脏象', '藏象', '恶寒', '恶风', '相傅',
         '藏精', '藏于', '肾藏', '肝藏', '脾藏', '藏神', '中病', '脏']
hits = {}
examples = {}
for ch in range(1, 82):
    f = D / f'segs_suwen{ch}.json' if ch != 1 else D / 'segs.json'
    if not f.exists():
        continue
    segs = json.loads(f.read_text(encoding='utf-8'))
    for i, s in enumerate(segs, 1):
        text = s.get('orig', '') + '。' + s.get('talk', '')
        for w in WORDS:
            n = text.count(w)
            if n:
                hits.setdefault(w, []).append((ch, i, n))
                if w not in examples:
                    m = re.search(re.escape(w), text)
                    examples[w] = text[max(0, m.start()-15):m.end()+15]

print('===== 医学多音字命中统计 =====')
for w, lst in sorted(hits.items(), key=lambda x: -len(x[1])):
    chs = sorted(set(c for c, _, _ in lst))
    total = sum(n for _, _, n in lst)
    print(f'{w}: {total} 处 / {len(chs)} 篇 {chs[:12]}{"…" if len(chs)>12 else ""}')
    if w in examples:
        print(f'   例: …{examples[w]}…')
