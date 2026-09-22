# -*- coding: utf-8 -*-
"""
S43 补修：同步更新拆分条目的 `parent` 字段 → v16（覆盖）
原因：S42 修了词目，但 956 条「病名待定」的 parent（原属×××）仍持旧字形。
做法：对 v15 重新施加 S42 全部规则，**作用域含 parent 字段**。
"""
import os, json
from collections import Counter
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, 'dist')
RULES = [
    ('四物散之粪', '四物散之类', 'body'),
    ('牌', '脾', 'head'),
    ('伏熟', '伏热', 'both'),
    ('初越', '初起', 'both'),
    ('派', '脉', 'both'),
]


def main():
    d = json.load(open(os.path.join(ROOT, 'data', 'bingyuan_terms_v15.json'), encoding='utf-8'))
    log = Counter(); ents = set()
    for t in d:
        ch = False
        for old, new, scope in RULES:
            if scope in ('head', 'both') and old in (t.get('head') or ''):
                n = t['head'].count(old); t['head'] = t['head'].replace(old, new)
                log[f'[词目] {old}→{new}'] += n; ch = True
            if scope in ('body', 'both') and old in (t.get('body') or ''):
                n = t['body'].count(old); t['body'] = t['body'].replace(old, new)
                log[f'[正文] {old}→{new}'] += n; ch = True
        # ★ 关键：parent 字段同步（所有规则都作用于它）
        for old, new, _ in RULES:
            if old in (t.get('parent') or ''):
                n = t['parent'].count(old); t['parent'] = t['parent'].replace(old, new)
                log[f'[原属] {old}→{new}'] += n; ch = True
        if ch:
            ents.add(t['no'])
    json.dump(d, open(os.path.join(ROOT, 'data', 'bingyuan_terms_v16.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    # 复检：head/body/parent 三处
    rest = {}
    for old, new, scope in RULES:
        cnt = 0
        for t in d:
            if scope in ('head', 'both'):
                cnt += (t.get('head') or '').count(old)
            if scope in ('body', 'both'):
                cnt += (t.get('body') or '').count(old)
            cnt += (t.get('parent') or '').count(old)
        rest[old] = cnt
    json.dump({'changes': dict(log.most_common()), 'entries_changed': len(ents), 'remaining': rest},
              open(os.path.join(DIST, 'v11_fix_report.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('改动条目:', len(ents), '/', len(d))
    for k, v in log.most_common():
        print(f'  {k}  ×{v}')
    print('复检残留(head/body/parent):', rest)


if __name__ == '__main__':
    main()
