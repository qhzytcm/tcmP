# -*- coding: utf-8 -*-
"""
S19 合并「上下文重构」产物 → v5（用于 V3 docx）
校验（重构档，比标点档宽松）：去标点后
  ① 长度比 ∈ [0.70, 1.30]
  ② 字多重集重合率 ≥ 0.50（重构会改动较多，但不得变成另写一篇）
  ③ 源含三要素标记时，输出须仍含对应标记（结构保真）
否则回退 v4 原文。
输入 data/bingyuan_terms_v4.json + data/rb_out/*.json → 输出 data/bingyuan_terms_v5.json
"""
import os, re, json, glob
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, 'dist')
RB_OUT = os.path.join(ROOT, 'data', 'rb_out')
PUNCT = '，。；、：？！“”‘’（）《》〈〉·—…,.!?;:()[]"\'　 \n\t'
RX = re.compile('[' + re.escape(PUNCT) + ']')
MARKS = ('病源', '病状', '治法')


def strip_p(s):
    return RX.sub('', s)


def overlap(a, b):
    ca, cb = Counter(a), Counter(b)
    return sum(min(ca[k], cb[k]) for k in ca) / max(1, sum(ca.values()))


def valid(src, out):
    si, so = strip_p(src), strip_p(out)
    if not so:
        return False, 'empty'
    r = len(so) / max(1, len(si))
    if not (0.70 <= r <= 1.30):
        return False, f'len比{r:.2f}'
    ov = overlap(si, so)
    if ov < 0.50:
        return False, f'重合{ov:.2f}'
    for m in MARKS:                      # 结构保真：源有则输出须有
        if m in si and m not in so:
            return False, f'缺标记{m}'
    return True, f'len比{r:.2f} 重合{ov:.2f}'


def main():
    terms = json.load(open(os.path.join(ROOT, 'data', 'bingyuan_terms_v4.json'), encoding='utf-8'))
    rb = {}
    for fp in sorted(glob.glob(os.path.join(RB_OUT, '*.json'))):
        try:
            for e in json.load(open(fp, encoding='utf-8')):
                if e.get('no') and e.get('body'):
                    rb[e['no']] = e['body']
        except Exception as ex:
            print('  跳过坏文件', os.path.basename(fp), type(ex).__name__)
    print(f'词条 {len(terms)} | 重构产物 {len(rb)} 条')

    st = Counter(); rej = []; ovs = []
    for t in terms:
        src = t.get('body') or ''
        if t['no'] in rb:
            ok, why = valid(src, rb[t['no']])
            if ok:
                t['body'] = rb[t['no']]; t['rebuild'] = 'llm'; st['llm'] += 1
                ovs.append(float(why.split('重合')[1]))
            else:
                t['rebuild'] = 'fallback'; st['fallback'] += 1
                rej.append({'no': t['no'], 'why': why, 'in': src[:50], 'out': rb[t['no']][:50]})
        else:
            t['rebuild'] = 'fallback'; st['fallback'] += 1
            rej.append({'no': t['no'], 'why': 'missing', 'in': src[:50], 'out': ''})

    json.dump(terms, open(os.path.join(ROOT, 'data', 'bingyuan_terms_v5.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    rep = {'by_source': dict(st), 'rejected': len(rej), 'rejected_sample': rej[:20],
           'overlap_min': min(ovs) if ovs else None,
           'overlap_avg': round(sum(ovs) / len(ovs), 3) if ovs else None}
    json.dump(rep, open(os.path.join(DIST, 'v5_rebuild_report.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    print('重构来源:', dict(st), '| 被拒/回退:', len(rej),
          '| 字集重合 min/avg:', rep['overlap_min'], rep['overlap_avg'])
    for x in rej[:5]:
        print('  !', x['no'], x['why'])


if __name__ == '__main__':
    main()
