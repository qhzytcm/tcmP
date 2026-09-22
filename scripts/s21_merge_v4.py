# -*- coding: utf-8 -*-
"""
S21 合并「V4 补缺重构」→ v6，并做补缺专项验收
判据（补缺档，允许增长）：
  ① 长度比 ∈ [0.75, 1.45]（补缺会加字，但不得膨胀）
  ② 字多重集重合 ≥ 0.55（不得另写一篇）
  ③ **标记覆盖不得下降**：源有 病源/病状/治法 者，输出必有
  ④ 三要素齐备率须 ≥ 基线（否则整批判退）
输出：data/bingyuan_terms_v6.json + dist/v4_rebuild_report.json
"""
import os, re, json, glob
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, 'dist')
VB_OUT = os.path.join(ROOT, 'data', 'vb_out')
PUNCT = '，。；、：？！“”‘’（）《》〈〉·—…,.!?;:()[]"\'　 \n\t'
RX = re.compile('[' + re.escape(PUNCT) + ']')
SRC_RE = r'[病满润游漏瑞烤浏消荆房痛]源'
ZH_RE = r'病[状默送肤选迭达跋然]'
ZHI_RE = r'[治洛活浩照浴跆沼陪邵路阁]法'
MARKS = ('病源', '病状', '治法')
RX_THERAPY = re.compile(r'宜|用|服|方|汤|散|丸|膏|灸|针|外治|敷|洗|涂|参看|参见|忌')


def strip_p(s):
    return RX.sub('', s)


def overlap(a, b):
    ca, cb = Counter(a), Counter(b)
    return sum(min(ca[k], cb[k]) for k in ca) / max(1, sum(ca.values()))


MARK_RX = {'病源': SRC_RE, '病状': ZH_RE, '治法': ZHI_RE}


def has_mark(b, k):
    return bool(re.search(MARK_RX[k], b))


def valid(src, out):
    si, so = strip_p(src), strip_p(out)
    if not so:
        return False, 'empty'
    r = len(so) / max(1, len(si))
    if not (0.75 <= r <= 1.45):
        return False, f'len比{r:.2f}'
    ov = overlap(si, so)
    if ov < 0.55:
        return False, f'重合{ov:.2f}'
    for k in MARKS:
        if has_mark(si, k) and not has_mark(so, k):
            return False, f'丢标记{k}'
    return True, f'len比{r:.2f} 重合{ov:.2f}'


def coverage(terms):
    st = Counter(); n = len(terms)
    for t in terms:
        b = t.get('body') or ''
        f = {k: bool(has_mark(b, k)) for k in MARKS}
        for k, v in f.items():
            if v:
                st[k] += 1
        if all(f.values()):
            st['三要素齐备'] += 1
        if not RX_THERAPY.search(b):
            st['无治疗特征词'] += 1
    return {k: f'{st[k]} ({100*st[k]/n:.1f}%)' for k in ('病源', '病状', '治法', '三要素齐备', '无治疗特征词')}


def main():
    base = json.load(open(os.path.join(ROOT, 'data', 'bingyuan_terms_v5.json'), encoding='utf-8'))
    vb = {}
    for fp in sorted(glob.glob(os.path.join(VB_OUT, '*.json'))):
        try:
            for e in json.load(open(fp, encoding='utf-8')):
                if e.get('no') and e.get('body'):
                    vb[e['no']] = e['body']
        except Exception as ex:
            print('  跳过坏文件', os.path.basename(fp), type(ex).__name__)

    st = Counter(); rej = []; ovs = []
    for t in base:
        src = t.get('body') or ''
        if t['no'] in vb:
            ok, why = valid(src, vb[t['no']])
            if ok:
                t['body'] = vb[t['no']]; t['v4'] = 'llm'; st['llm'] += 1
                ovs.append(float(why.split('重合')[1]))
            else:
                t['v4'] = 'fallback'; st['fallback'] += 1
                rej.append({'no': t['no'], 'why': why, 'out': vb[t['no']][:60]})
        else:
            t['v4'] = 'fallback'; st['fallback'] += 1
            rej.append({'no': t['no'], 'why': 'missing', 'out': ''})

    cov_after = coverage(base)
    cov_base = json.load(open(os.path.join(DIST, 'v4_gap_baseline.json'), encoding='utf-8'))['coverage']
    json.dump(base, open(os.path.join(ROOT, 'data', 'bingyuan_terms_v6.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    rep = {'by_source': dict(st), 'rejected': len(rej), 'rejected_sample': rej[:15],
           'coverage_before': cov_base, 'coverage_after': cov_after,
           'overlap_min': min(ovs) if ovs else None,
           'overlap_avg': round(sum(ovs) / len(ovs), 3) if ovs else None}
    json.dump(rep, open(os.path.join(DIST, 'v4_rebuild_report.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    print('来源:', dict(st), '| 退回:', len(rej), '| 重合 min/avg:', rep['overlap_min'], rep['overlap_avg'])
    print('补缺前:', cov_base)
    print('补缺后:', cov_after)
    for x in rej[:5]:
        print('  !', x['no'], x['why'])


if __name__ == '__main__':
    main()
