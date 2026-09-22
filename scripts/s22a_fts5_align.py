# -*- coding: utf-8 -*-
"""
S22a 通过 FTS5 校正完善正文（V5）
权威源：① 本地 ICD-11 MMS 31,838 条中文标题（data/icd11_mms.db）
        ② tcmP 平台病证单元 KB（kg/samples，103 DSU：疾病/证候/方剂）
方法：CJK **二元组**入 FTS5 索引（unicode61 默认分词对中文整串成单 token，故拆二元组），
     词目查询 → BM25 排序 → 字面复核 → **校正**(单字差归一) + **完善**(标注 ICD-11 编码/标准名)
输入 data/bingyuan_terms_v6.json → 输出 data/bingyuan_terms_v7.json + dist/fts5_align_report.json
"""
import os, re, json, sqlite3
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, 'dist'); os.makedirs(DIST, exist_ok=True)
DB = os.path.join(ROOT, 'data', 'icd11_mms.db')


def bgs(s):
    s = re.sub(r'[\s（）()、，。；：·\-—/]', '', s or '')
    if len(s) < 2:
        return [s] if s else []
    return [s[i:i + 2] for i in range(len(s) - 1)]


def overlap(a, b):
    ba, bb = Counter(bgs(a)), Counter(bgs(b))
    return sum(min(ba[k], bb[k]) for k in ba) / max(1, sum(ba.values()))


def build_index():
    con = sqlite3.connect(':memory:')
    con.execute("CREATE VIRTUAL TABLE t USING fts5(bg, code, title)")
    rows = []
    c = sqlite3.connect(DB)
    for code, title in c.execute("SELECT code, title FROM entities WHERE title IS NOT NULL AND title<>''"):
        rows.append((' '.join(bgs(title)), code, title))
    c.close()
    # 平台 KB 术语（疾病/证候/方剂）也入库
    kb = []
    try:
        for f in sorted(os.listdir(os.path.join(ROOT, 'kg', 'samples'))):
            for d in json.load(open(os.path.join(ROOT, 'kg', 'samples', f), encoding='utf-8')):
                ds, ss = d.get('disease_side', {}), d.get('syndrome_side', {})
                for nm, code in [(ds.get('disease_name', ''), ds.get('icd11_code') or ds.get('icd_code') or ''),
                                 (ss.get('syndrome_name', ''), ''), (d.get('clinical', {}).get('recommended_formula', ''), '')]:
                    if nm:
                        kb.append((' '.join(bgs(nm)), code, nm))
    except Exception as e:
        print('  KB 载入跳过:', type(e).__name__)
    for r in rows + kb:
        con.execute("INSERT INTO t VALUES (?,?,?)", r)
    con.commit()
    return con, len(rows), len(kb)


def main():
    con, n_icd, n_kb = build_index()
    print(f'FTS5 索引: ICD-11 {n_icd} 条 + KB {n_kb} 条')
    terms = json.load(open(os.path.join(ROOT, 'data', 'bingyuan_terms_v6.json'), encoding='utf-8'))

    st = Counter(); samples = []
    for t in terms:
        head = t['head']
        q = ' OR '.join(f'"{g}"' for g in list(dict.fromkeys(bgs(head)))[:12]) or f'"{head}"'
        try:
            rows = con.execute("SELECT code, title FROM t WHERE t MATCH ? ORDER BY rank LIMIT 5", (q,)).fetchall()
        except sqlite3.OperationalError:
            rows = []
        best = None
        for code, title in rows:
            ov = overlap(head, title)
            if best is None or ov > best[0]:
                best = (ov, code, title)
        t['fts5'] = None
        if best and best[0] >= 0.6 and len(head) >= 2:
            ov, code, title = best
            t['fts5'] = {'code': code, 'title': title, 'overlap': round(ov, 3)}
            st['对齐'] += 1
            # 校正：词目与标准名单字差 → 归一
            if len(head) == len(title) and sum(1 for x, y in zip(head, title) if x != y) == 1:
                t['head'] = title; st['词目归一'] += 1
            if len(samples) < 8:
                samples.append((t['no'], head, title, code, round(ov, 3)))
        else:
            st['未对齐'] += 1

    json.dump(terms, open(os.path.join(ROOT, 'data', 'bingyuan_terms_v7.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    rep = {'index': {'icd11': n_icd, 'kb': n_kb}, 'aligned': st['对齐'], 'headword_norm': st['词目归一'],
           'unaligned': st['未对齐'], 'samples': samples}
    json.dump(rep, open(os.path.join(DIST, 'fts5_align_report.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('对齐:', st['对齐'], '| 词目归一:', st['词目归一'], '| 未对齐:', st['未对齐'])
    for s in samples:
        print('  ', s)


if __name__ == '__main__':
    main()
