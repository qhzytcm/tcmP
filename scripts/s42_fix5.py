# -*- coding: utf-8 -*-
"""
S42 用户点名的 5 处定向校正 → v16
1) 四物散之粪 → 四物散之类
2) 牌 → 脾（**词目**；正文已于 S32 修正）
3) 伏熟 → 伏热（核查：已为 0，保留规则以防再生）
4) 初越 → 初起
5) 任派 → 任脉（并依上下文证据扩展为 派 → 脉，含词目）
输出 data/bingyuan_terms_v16.json + dist/v11_fix_report.json
"""
import os, json
from collections import Counter
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, 'dist'); os.makedirs(DIST, exist_ok=True)

# (原, 新, 作用域)  作用域: 'head' / 'body' / 'both'
RULES = [
    ('四物散之粪', '四物散之类', 'body'),   # 1
    ('牌', '脾', 'head'),                   # 2（正文已修）
    ('伏熟', '伏热', 'both'),               # 3
    ('初越', '初起', 'both'),               # 4
    ('派', '脉', 'both'),                   # 5（任派→任脉；依上下文证据整体校正）
]


def main():
    d = json.load(open(os.path.join(ROOT, 'data', 'bingyuan_terms_v15.json'), encoding='utf-8'))
    log = Counter(); ents = set()
    for t in d:
        ch = False
        for old, new, scope in RULES:
            if scope in ('head', 'both') and old in (t.get('head') or ''):
                n = t['head'].count(old)
                t['head'] = t['head'].replace(old, new)
                log[f'[词目] {old}→{new}'] += n; ch = True
            if scope in ('body', 'both') and old in (t.get('body') or ''):
                n = t['body'].count(old)
                t['body'] = t['body'].replace(old, new)
                log[f'[正文] {old}→{new}'] += n; ch = True
        if ch:
            ents.add(t['no'])
    json.dump(d, open(os.path.join(ROOT, 'data', 'bingyuan_terms_v16.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    # 复检
    rest = {}
    for old, new, scope in RULES:
        cnt = 0
        for t in d:
            if scope in ('head', 'both'):
                cnt += (t.get('head') or '').count(old)
            if scope in ('body', 'both'):
                cnt += (t.get('body') or '').count(old)
        rest[old] = cnt
    rep = {'changes': dict(log.most_common()), 'entries_changed': len(ents), 'remaining': rest}
    json.dump(rep, open(os.path.join(DIST, 'v11_fix_report.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    print('改动条目:', len(ents), '/', len(d))
    for k, v in log.most_common():
        print(f'  {k}  ×{v}')
    print('复检残留:', rest)


if __name__ == '__main__':
    main()
