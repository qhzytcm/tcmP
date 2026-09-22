# -*- coding: utf-8 -*-
"""
S47 用户裁定处置 → v19
· 吸咂 → 吸吮        （0010，吸吮义，非呃逆）
· 火咂 → 火呃        （0203）
· 热咂 → 热呃        （2161，与「气咂→气呃」同类）
· 死逆 → 呃逆        （2041/2161，含参见）
· 咂舌瘾：按「肛痔-正确」不改（词目保留）
作用域 head/body/parent/alias
"""
import os, json
from collections import Counter
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, 'dist')
SEQ = [('吸咂', '吸吮'), ('火咂', '火呃'), ('热咂', '热呃'), ('死逆', '呃逆')]


def main():
    d = json.load(open(os.path.join(ROOT, 'data', 'bingyuan_terms_v18.json'), encoding='utf-8'))
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
            if o != s:
                t[f] = o; ch = True
        if t.get('alias'):
            na = [x for x in t['alias']]
            for i, x in enumerate(na):
                for a, b in SEQ:
                    if a in x:
                        log['[alias] %s→%s' % (a, b)] += x.count(a)
                        na[i] = x.replace(a, b)
            if na != t['alias']:
                t['alias'] = na; ch = True
        if ch:
            ents.add(t['no'])
    json.dump(d, open(os.path.join(ROOT, 'data', 'bingyuan_terms_v19.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    # 复检
    rest = Counter(); wha = 0
    for t in d:
        s = ((t.get('head') or '') + (t.get('body') or '') + (t.get('parent') or '') + ''.join(t.get('alias') or []))
        for a, b in SEQ:
            rest[a] += s.count(a)
        wha += s.count('咂')
    json.dump({'changes': dict(log.most_common()), 'entries_changed': len(ents),
               'remaining': dict(rest), 'ya_remaining': wha},
              open(os.path.join(DIST, 'v13_fix_report.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('改动条目:', len(ents), '/', len(d))
    for k, v in log.most_common():
        print(f'  {k}  ×{v}')
    print('复检残留:', dict(rest), '| 「咂」剩余:', wha, '（应为 1＝咂舌瘾词目）')
    for t in d:
        s = (t.get('head') or '') + (t.get('body') or '')
        if '咂' in s:
            i = s.index('咂')
            print(f"  余「咂」: {t['no']} 【{t['head']}】…{s[max(0,i-10):i+10]}…")


if __name__ == '__main__':
    main()
