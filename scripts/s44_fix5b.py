# -*- coding: utf-8 -*-
"""
S44 用户第二批校字 → v17
① 水疗/牙疗/气疗… → 疔（正则 `(?<![治医疗])疗(?!法|效|程)`；保护 治疗/医疗/疗法）
② 五更欢 → 五更咳（**全书统一用「咳」329 处、欬 0 处 → 取「咳」求体例一致**）
③ 太阳嘛病 → 太阳经病
④ 牛身不途/牛身不肌 → 半身不遂；牛身 → 半身
⑤ 气咂 → 气呃；咂逆 → 呃逆
作用域：head / body / parent
输出 data/bingyuan_terms_v17.json + dist/v12_fix_report.json
"""
import os, json, re
from collections import Counter
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, 'dist'); os.makedirs(DIST, exist_ok=True)

# 先具体后泛化
SEQ = [
    ('太阳嘛病', '太阳经病'),
    ('牛身不途', '半身不遂'), ('半身不途', '半身不遂'),
    ('牛身不肌', '半身不遂'), ('半身不肌', '半身不遂'),
    ('牛身', '半身'),
    ('不途', '不遂'),
    ('气咂', '气呃'), ('咂逆', '呃逆'),
    ('欢', '咳'),
]
RX_LIAO = re.compile(r'(?<![治医疗])疗(?!法|效|程)')   # 疗→疔，保护治疗/医疗/疗法


def main():
    d = json.load(open(os.path.join(ROOT, 'data', 'bingyuan_terms_v16.json'), encoding='utf-8'))
    log = Counter(); ents = set()
    for t in d:
        ch = False
        for f in ('head', 'body', 'parent'):
            s = t.get(f)
            if not s:
                continue
            o = s
            for a, b in SEQ:
                if a in o:
                    log[f'[{f}] {a}→{b}'] += o.count(a)
                    o = o.replace(a, b)
            n = len(RX_LIAO.findall(o))
            if n:
                log[f'[{f}] 疗→疔'] += n
                o = RX_LIAO.sub('疔', o)
            if o != s:
                t[f] = o; ch = True
        if ch:
            ents.add(t['no'])
    json.dump(d, open(os.path.join(ROOT, 'data', 'bingyuan_terms_v17.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    # 复检
    rest = Counter()
    for t in d:
        s = ((t.get('head') or '') + (t.get('body') or '') + (t.get('parent') or ''))
        for a, b in SEQ:
            rest[a] += s.count(a)
        rest['疗(非治疗类)'] += len(RX_LIAO.findall(s))
    json.dump({'changes': dict(log.most_common()), 'entries_changed': len(ents), 'remaining': dict(rest)},
              open(os.path.join(DIST, 'v12_fix_report.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('改动条目:', len(ents), '/', len(d))
    for k, v in log.most_common():
        print(f'  {k}  ×{v}')
    print('\n复检残留:', dict(rest))


if __name__ == '__main__':
    main()
