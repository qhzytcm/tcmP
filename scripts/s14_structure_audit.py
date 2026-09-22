# -*- coding: utf-8 -*-
"""
S14 「疾病/证候 — 病机 — 治疗汇聚建议」结构一致性审查（v2 安全版）
- 用**标记变体集**定位三要素分节，**只改边界不改写正文**（零内容风险）
- 清洗页眉噪声（病源辞典变体）
- 覆盖率统计 + 异常清单
输出：data/bingyuan_terms_v3.json · dist/structure_audit.json
"""
import os, re, json, argparse
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, 'dist'); os.makedirs(DIST, exist_ok=True)

# 三要素标记的 OCR 变体（频率扫描 + 上下文实证）
SRC_RE = r'[病满润游漏瑞烤浏消荆房痛]源'
ZH_RE = r'病[状默送肤选迭达跋然]'
ZHI_RE = r'[治洛活浩照浴跆沼陪邵路阁]法'
MARK = re.compile(f'({SRC_RE})|({ZH_RE})|({ZHI_RE})')
TYPES = ('病源', '病状', '治法')

HEADER_NOISE = ['病源辞典', '病源静典', '特源牌典', '润源静典', '烤源群典', '病源麟典', '树源静典']
RX_THERAPY = re.compile(r'宜|用|服|方|汤|散|丸|膏|灸|针|外治|敷|洗|涂|参看|参见|忌')


def clean(s):
    for h in HEADER_NOISE:
        s = s.replace(h, '')
    return s


def split3(body):
    """按变体定位分节；正文原样保留（只取其间片段）。"""
    secs = {'病源': '', '病状': '', '治法': ''}
    hits = []
    for m in MARK.finditer(body):
        t = TYPES[0] if m.group(1) else TYPES[1] if m.group(2) else TYPES[2]
        hits.append((t, m.start(), m.end()))
    if not hits:
        secs['病源'] = body
        return secs
    if hits[0][1] > 0:                     # 首个标记前的引导文字归病机
        secs['病源'] = body[:hits[0][1]]
    for idx, (t, s, e) in enumerate(hits):
        nxt = hits[idx + 1][1] if idx + 1 < len(hits) else len(body)
        secs[t] += body[e:nxt]
    return secs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--terms', default=os.path.join(ROOT, 'data', 'bingyuan_terms_v2.json'))
    ap.add_argument('--out', default=os.path.join(ROOT, 'data', 'bingyuan_terms_v3.json'))
    a = ap.parse_args()
    terms = json.load(open(a.terms, encoding='utf-8'))
    n = len(terms)
    print('词条', n)

    stat = Counter(); anomalies = []
    for t in terms:
        body = clean(t.get('body') or '')
        secs = split3(body)
        t['body'] = body
        t['sections'] = secs
        h = {'病机': bool(secs['病源']), '病状': bool(secs['病状']),
             '治疗': bool(secs['治法']), '治疗汇聚建议': bool(RX_THERAPY.search(secs['治法'] or body))}
        t['structure'] = {'疾病证候': t['head'], **h}
        for k, v in h.items():
            if v:
                stat[k] += 1
        if all(h[k] for k in ('病机', '病状', '治疗')):
            stat['三要素齐备'] += 1
        if not h['治疗汇聚建议']:
            anomalies.append({'no': t['no'], 'head': t['head'], 'type': '缺治疗汇聚建议', 'body80': body[:80]})
        elif not h['病机']:
            anomalies.append({'no': t['no'], 'head': t['head'], 'type': '缺病机', 'body80': body[:80]})
        elif not h['病状']:
            anomalies.append({'no': t['no'], 'head': t['head'], 'type': '缺病状', 'body80': body[:80]})

    json.dump(terms, open(a.out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    rep = {'terms': n,
           'coverage': {k: f'{stat[k]} ({100*stat[k]/n:.1f}%)'
                        for k in ('病机', '病状', '治疗', '治疗汇聚建议', '三要素齐备')},
           'anomaly_count': len(anomalies),
           'anomaly_by_type': dict(Counter(x['type'] for x in anomalies)),
           'anomalies_sample': anomalies[:60]}
    json.dump(rep, open(os.path.join(DIST, 'structure_audit.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    print('结构覆盖:', rep['coverage'])
    print('异常:', rep['anomaly_by_type'], '共', len(anomalies))
    for x in anomalies[:5]:
        print('  !', x['no'], x['head'], x['type'], '|', x['body80'][:40])


if __name__ == '__main__':
    main()
