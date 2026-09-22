# -*- coding: utf-8 -*-
"""
S32 确定性高置信术语校正 → v12
判据：目标词在语料中的频次 ≥ 变体频次 × 5（方向性证据强），且变体非合法中医用字
输出 data/bingyuan_terms_v12.json + dist/v7_termfix_report.json
"""
import os, json
from collections import Counter
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, 'dist'); os.makedirs(DIST, exist_ok=True)

# 高置信 OCR 变体 → 规范形（药名/方名/病名/书名）
PAIRS = [
    ('黄茶', '黄芩'), ('白龙', '白术'), ('世草', '甘草'), ('廿草', '甘草'), ('茯茶', '茯苓'),
    ('屎角', '犀角'), ('葛蒲', '菖蒲'), ('遗志', '远志'), ('遵翘', '连翘'), ('牛夏', '半夏'),
    ('之殿', '之属'), ('之厨', '之属'), ('之阁', '之属'), ('之开', '之属'), ('牌', '脾'),
    ('源醉典', '源辞典'), ('源爵典', '源辞典'), ('源路典', '源辞典'), ('源鲜典', '源辞典'),
    ('源酵典', '源辞典'), ('源壁典', '源辞典'), ('源游典', '源辞典'), ('源舒典', '源辞典'),
    ('源群典', '源辞典'), ('源解典', '源辞典'), ('源医典', '源辞典'), ('源科典', '源辞典'),
    ('手少除', '手少阴'), ('手太除', '手太阴'), ('足少除', '足少阴'), ('足太除', '足太阴'),
]
RATIO = 5.0


def main():
    terms = json.load(open(os.path.join(ROOT, 'data', 'bingyuan_terms_v11.json'), encoding='utf-8'))
    body_all = ''.join((t.get('body') or '') for t in terms)
    applied, skipped = [], []
    for old, new in PAIRS:
        f_old = body_all.count(old)
        f_new = body_all.count(new)
        if f_old == 0:
            continue
        if f_new >= f_old * RATIO:
            applied.append({'old': old, 'new': new, 'f_old': f_old, 'f_new': f_new})
        else:
            skipped.append({'old': old, 'new': new, 'f_old': f_old, 'f_new': f_new})
    print('通过判据(目标≥变体×5):', len(applied), '| 未通过:', len(skipped))
    for s in skipped:
        print('  跳过', s)

    n = 0; log = Counter(); hn = 0
    HEAD_PAIRS = [{'old': o, 'new': n} for o, n in PAIRS if o.startswith(('手少', '手太', '足少', '足太'))]
    for t in terms:
        h = t.get('head') or ''
        nh = h
        for a in HEAD_PAIRS:
            if a['old'] in nh:
                nh = nh.replace(a['old'], a['new'])
        if nh != h:
            t['head'] = nh; hn += 1
            log['【词目】' + h + '→' + nh] += 1
        b = t.get('body') or ''
        nb = b
        for a in applied:
            if a['old'] in nb:
                log[a['old'] + '→' + a['new']] += nb.count(a['old'])
                nb = nb.replace(a['old'], a['new'])
        if nb != b:
            t['body'] = nb; t['ver'] = 'v7fix'; n += 1
    json.dump(terms, open(os.path.join(ROOT, 'data', 'bingyuan_terms_v12.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    rep = {'applied': applied, 'skipped': skipped, 'entries_changed': n, 'counts': dict(log)}
    json.dump(rep, open(os.path.join(DIST, 'v7_termfix_report.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    print('改动条目:', n, '/', len(terms))
    for k, v in log.most_common():
        print(f'   {k}  x{v}')


if __name__ == '__main__':
    main()
