# -*- coding: utf-8 -*-
"""
S17 合并 LLM 矫正结果 → V4
来源优先级：llm_out/批次文件 > ollama 缓存 > 语义群规则引擎
校验（防跑偏）：去标点后 ① 长度比∈[0.85,1.15] ② 字多重集重合率≥0.85，否则回退规则标点
输入 data/bingyuan_terms_v3.json → 输出 data/bingyuan_terms_v4.json
"""
import os, re, json, glob
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, 'dist')
LLM_OUT = os.path.join(ROOT, 'data', 'llm_out')
CACHE = os.path.join(ROOT, 'data', 'llm_punct_cache.json')
PUNCT = '，。；、：？！“”‘’（）《》〈〉·—…,.!?;:()[]"\'　 \n\t'
RX = re.compile('[' + re.escape(PUNCT) + ']')

import importlib.util as U
spec = U.spec_from_file_location('s15', os.path.join(ROOT, 'scripts', 's15_llm_punct.py'))
s15 = U.module_from_spec(spec); spec.loader.exec_module(s15)


def strip_p(s):
    return RX.sub('', s)


def overlap(a, b):
    ca, cb = Counter(a), Counter(b)
    if not ca:
        return 0.0
    return sum(min(ca[k], cb[k]) for k in ca) / sum(ca.values())


def valid(inp, out, loose=True):
    si, so = strip_p(inp), strip_p(out)
    if not so:
        return False
    if not loose:
        return si == so
    r = len(so) / max(1, len(si))
    return 0.85 <= r <= 1.15 and overlap(si, so) >= 0.85


def main():
    terms = json.load(open(os.path.join(ROOT, 'data', 'bingyuan_terms_v3.json'), encoding='utf-8'))
    cache = json.load(open(CACHE, encoding='utf-8')) if os.path.exists(CACHE) else {}
    llm = {}
    for d in (LLM_OUT, os.path.join(ROOT, 'data', 'llm_out2')):
        for fp in sorted(glob.glob(os.path.join(d, '*.json'))):
            try:
                for e in json.load(open(fp, encoding='utf-8')):
                    if e.get('no') and e.get('body'):
                        llm[e['no']] = e['body']
            except Exception as ex:
                print('  跳过坏文件', os.path.basename(fp), type(ex).__name__)
    print(f'词条 {len(terms)} | llm_out {len(llm)} 条 | ollama缓存 {len(cache)} 条')

    st = Counter(); rej = []
    for t in terms:
        body = t.get('body') or ''
        src, out = 'rule', s15.rule_punct(body)
        if t['no'] in cache and valid(body, cache[t['no']], loose=False):
            src, out = 'ollama', cache[t['no']]
        if t['no'] in llm:
            cand = llm[t['no']]
            if valid(body, cand, loose=True):
                src, out = 'llm', cand
            else:
                rej.append({'no': t['no'], 'why': f'len比{len(strip_p(cand))/max(1,len(strip_p(body))):.2f} 重合{overlap(strip_p(body),strip_p(cand)):.2f}',
                            'in': body[:60], 'out': cand[:60]})
        t['body'] = out; t['punct_src'] = src
        st[src] += 1

    json.dump(terms, open(os.path.join(ROOT, 'data', 'bingyuan_terms_v4.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    rep = {'by_source': dict(st), 'rejected': len(rej), 'rejected_sample': rej[:20]}
    json.dump(rep, open(os.path.join(DIST, 'v4_merge_report.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    print('来源分布:', dict(st), '| 因跑偏被拒:', len(rej))
    for x in terms[:2]:
        print(f"  {x['no']}[{x['punct_src']}]: {x['body'][:100]}")


if __name__ == '__main__':
    main()
