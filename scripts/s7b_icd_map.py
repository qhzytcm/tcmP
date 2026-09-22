# -*- coding: utf-8 -*-
"""
S7b ICD-11 术语映射：病源辞典词目 → ICD-11 标准编码
用 hermes venv python（sqlite3 在 Anaconda 段错误）。内网 API 中文搜索 + 本地 db 编码桥接。
输出：data/bingyuan_terms_icd.json
"""
import os, sys, json, time, argparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
from icd11_client import ICD11Client


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--terms', default=os.path.join(ROOT, 'data', 'bingyuan_terms.json'))
    ap.add_argument('--out', default=os.path.join(ROOT, 'data', 'bingyuan_terms_icd.json'))
    ap.add_argument('--limit', type=int, default=None)
    a = ap.parse_args()

    terms = json.load(open(a.terms, encoding='utf-8'))
    cache = {}
    if os.path.exists(a.out):
        cache = {t['no']: t.get('icd11') for t in json.load(open(a.out, encoding='utf-8'))}
    cl = ICD11Client()

    mapped = 0
    t0 = time.time()
    for i, t in enumerate(terms):
        if a.limit and i >= a.limit:
            break
        if cache.get(t['no']):
            t['icd11'] = cache[t['no']]; mapped += 1; continue
        try:
            res = cl.lookup(t['head'], limit=3)
            best = None
            for r in res:
                if 'error' in r:
                    continue
                best = {'code': r.get('code'), 'foundation_id': r.get('foundation_id'),
                        'title_cn': r.get('title_cn'), 'title_en': r.get('title_en'),
                        'chapter': r.get('chapter')}
                break
            t['icd11'] = best
            if best:
                mapped += 1
        except Exception as e:
            t['icd11'] = {'error': str(e)}
        if (i + 1) % 20 == 0:
            print(f'  ..{i+1}/{len(terms)} mapped={mapped} 用时{time.time()-t0:.0f}s', flush=True)

    json.dump(terms, open(a.out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f'完成: {len(terms)} 词条, 映射成功 {mapped} → {a.out}  用时{time.time()-t0:.0f}s')
    for t in terms[:6]:
        ic = t.get('icd11') or {}
        print(f"  {t['no']} {t['head']:10s} → {ic.get('code') or '--':8s} {(ic.get('title_cn') or '')[:24]}")


if __name__ == '__main__':
    main()
