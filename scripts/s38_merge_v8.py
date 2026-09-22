# -*- coding: utf-8 -*-
"""
S38 合并「第二份扫描件定向提取」→ v13
判据：新正文 ≥20 字，且未引入源文与旧正文都没有的药名（防编造）
输出 data/bingyuan_terms_v13.json + dist/v8_pdf2_report.json
"""
import os, re, json
from collections import Counter
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, 'dist'); os.makedirs(DIST, exist_ok=True)
DOSE = '一两三四五六七八九十钱分斤勺厘'
RXH = re.compile(r'([\u4e00-\u9fff]{2,3})各?(?=[' + DOSE + r'])')
BLACK = {'每服', '各等', '参见', '者宜', '草各', '病源', '病状', '治法', '宜用', '或用', '各二', '一两'}


def herbs(s):
    return {m.group(1) for m in RXH.finditer(s or '') if m.group(1) not in BLACK}


def main():
    base = json.load(open(os.path.join(ROOT, 'data', 'bingyuan_terms_v12.json'), encoding='utf-8'))
    outs = json.load(open(os.path.join(ROOT, 'data', 'pdf2_out.json'), encoding='utf-8'))
    srcmap = {p['no']: p['source'] for p in json.load(open(os.path.join(ROOT, 'data', 'pdf2_repair.json'), encoding='utf-8'))}
    st = Counter(); rec = []
    for t in base:
        o = outs.get(t['no'])
        if not o:
            continue
        new = (o.get('body') or '').strip()
        old = t.get('body') or ''
        if len(new) < 20:
            st['太短未采用'] += 1
            rec.append({'no': t['no'], 'head': t['head'], 'from': len(old), 'to': len(new), 'act': 'skip-short'})
            continue
        if new == old:
            st['无变化'] += 1
            continue
        fab = herbs(new) - herbs(old) - herbs(srcmap.get(t['no'], ''))
        if fab:
            st['药名越界未采用'] += 1
            rec.append({'no': t['no'], 'head': t['head'], 'from': len(old), 'to': len(new),
                        'act': 'skip-fab', 'fab': sorted(fab)[:4]})
            continue
        t['body'] = new; t['ver'] = 'v8pdf2'; st['已采用'] += 1
        rec.append({'no': t['no'], 'head': t['head'], 'from': len(old), 'to': len(new), 'act': 'ok'})
    json.dump(base, open(os.path.join(ROOT, 'data', 'bingyuan_terms_v13.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    json.dump({'stats': dict(st), 'details': rec}, open(os.path.join(DIST, 'v8_pdf2_report.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    print('统计:', dict(st))
    for r in rec:
        if r['act'] == 'ok':
            print(f"  ✓ {r['no']} {r['head'][:14]} {r['from']}→{r['to']}")
    for r in rec:
        if r['act'].startswith('skip'):
            print(f"  - {r['no']} {r['head'][:14]} {r['from']}→{r['to']} ({r['act']}{r.get('fab','')})")
    n = sum(1 for t in base if len(t.get('body') or '') < 20)
    print('合并后仍 <20 字:', n)


if __name__ == '__main__':
    main()
