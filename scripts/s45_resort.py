# -*- coding: utf-8 -*-
"""
S45 校字后重排 + 重编号 → v18
词目笔画变化（欢6→咳9、嘛14→经8、牛4→半5…）会破坏多级笔画序，故整体重排。
病名待定条目继承父词目的笔画键，紧随父条目。
"""
import os, json
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = json.load(open(os.path.join(ROOT, 'data', 'strokes.json'), encoding='utf-8'))


def st(c):
    v = S.get(c)
    return v if isinstance(v, int) else (v[0] if isinstance(v, list) and v else 999)


def skey(h):
    return [st(c) for c in h] or [999]


def main():
    d = json.load(open(os.path.join(ROOT, 'data', 'bingyuan_terms_v17.json'), encoding='utf-8'))
    key_of = {t['head']: skey(t['head']) for t in d}

    def sortkey(e):
        if e['head'] == '病名待定':
            return (key_of.get(e.get('parent') or '', [999]), 1, e.get('seq') or 0)
        return (skey(e['head']), 0, 0)

    d.sort(key=sortkey)
    for i, e in enumerate(d, 1):
        e['no'] = f'{i:04d}'
    json.dump(d, open(os.path.join(ROOT, 'data', 'bingyuan_terms_v18.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    # 复检
    bad = 0; prev = None
    for t in d:
        if t['head'] == '病名待定':
            continue
        k = skey(t['head'])
        if prev is not None and k < prev:
            bad += 1
        prev = k
    print('条目:', len(d), '| 重编号 0001-%04d' % len(d))
    print('重排后多级笔画序违规:', bad)
    ns = [int(t['no']) for t in d]
    print('编号连续:', ns == list(range(1, len(d) + 1)))
    print('前 8 条:', [(t['no'], t['head']) for t in d[:8]])


if __name__ == '__main__':
    main()
