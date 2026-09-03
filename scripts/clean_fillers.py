# -*- coding: utf-8 -*-
"""口语噪音清洗: 全部篇 talk 去填充词（保留语义词/语气词尾）"""
import json
import re
from pathlib import Path

D = Path(r'C:\Users\DELL\tcmP\docs\视频')

# 填充词（整词删除; 按出现位置处理）
FILLER_WORDS = ['嗯', '啊', '诶', '哦哈', '那个', '然后', '就是说', '对不对',
                '对吧', '是不是', '这个这个', '对对对', '那那', '你看',
                '我们看', '你看这个', '反正', '基本上', '其实呢', '就是说呢']
# 谨慎处理: 独立"就是/其实"（仅删句首/逗号后）
PREFIX_FILLERS = ['就是', '其实', '反正']


def clean(talk):
    t = talk
    for fw in FILLER_WORDS:
        t = t.replace(fw, '')
    # 句首/逗号后填充词
    for fw in PREFIX_FILLERS:
        t = re.sub(rf'(^|[，。；])\s*{fw}', r'\1', t)
    # 清理产生的重复标点/空格
    t = re.sub(r'[，。；]{2,}', lambda m: m.group(0)[0], t)
    t = re.sub(r'\s+', '', t)
    t = t.strip('，。')
    return t


total = 0
for ch in range(1, 20):
    f = D / f'segs_suwen{ch}.json' if ch != 1 else D / 'segs.json'
    if not f.exists():
        continue
    segs = json.loads(f.read_text(encoding='utf-8'))
    ch_del = 0
    for s in segs:
        old = s.get('talk', '')
        new = clean(old)
        # 统计删除量（填充词计数）
        n = sum(old.count(fw) for fw in FILLER_WORDS)
        n += sum(len(re.findall(rf'(^|[，。；])\s*{fw}', old)) for fw in PREFIX_FILLERS)
        if new != old:
            s['talk'] = new if len(new) > 15 else old  # 防过度清洗
            ch_del += n
    if ch_del:
        f.write_text(json.dumps(segs, ensure_ascii=False, indent=1), encoding='utf-8')
        print(f'素问{ch}: 清洗填充词 {ch_del} 处')
        total += ch_del
print(f'总清洗: {total} 处')
