# -*- coding: utf-8 -*-
"""
S23b 通过 FTS5 核验/校正「目录页码标注」与「索引页码标注」
① Word 导出 PDF 的逐页文本 → 仅取**正文页**建 SQLite FTS5（CJK 二元组）
   （不把前置「词条索引」页入索引：其含全部四位编号，会污染 BM25 排序）
② 目录三节 + 1831 词条：FTS5 检索定位实际页 → 与 docx PAGEREF 标注比对
③ 输出 dist/fts5_page_audit.json（须 .venv-api python：sqlite3+FTS5+pymupdf）
"""
import os, sys, re, json, sqlite3, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, 'dist')
flat = lambda s: re.sub(r'[\s\u3000]', '', s or '')


def bgs(s):
    s = flat(s)
    return [s[i:i + 2] for i in range(len(s) - 1)] if len(s) > 1 else ([s] if s else [])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--pdf', required=True)
    ap.add_argument('--docx', required=True)
    ap.add_argument('--terms', default=os.path.join(ROOT, 'data', 'bingyuan_terms_v7.json'))
    a = ap.parse_args()

    import pymupdf
    from s12_docx_verify import read_pagerefs

    claims = read_pagerefs(a.docx)
    doc = pymupdf.open(a.pdf)
    texts = [(doc[i].get_text() or '') for i in range(doc.page_count)]
    doc.close()

    heads = {}
    if os.path.exists(a.terms):
        for t in json.load(open(a.terms, encoding='utf-8')):
            heads[t['no']] = t.get('head', '')

    # ── 节定位（纯文本，唯一串）──
    def first_page(pat, start=1):
        for i in range(start, len(texts)):
            if flat(pat) in flat(texts[i]):
                return i + 1
        return None
    sec_index = first_page('一、词条索引（按笔画序', 1)
    sec_subject = first_page('二、主题词索引（subject-index：', (sec_index or 1) + 1)
    h1 = heads.get('0001', '')
    body_start = None
    for i in range((sec_subject or 1), len(texts)):
        if ('0001' + h1) in flat(texts[i]):
            body_start = i + 1; break

    # ── FTS5 仅索引正文页 ──
    con = sqlite3.connect(':memory:')
    con.execute("CREATE VIRTUAL TABLE pages USING fts5(bg, page UNINDEXED)")
    for i in range((body_start or 1) - 1, len(texts)):
        con.execute("INSERT INTO pages VALUES (?,?)", (' '.join(bgs(texts[i])), i + 1))
    con.commit()
    n_body = con.execute("SELECT count(*) FROM pages").fetchone()[0]

    def fts_top(query, k=5):
        q = ' OR '.join(f'"{g}"' for g in list(dict.fromkeys(bgs(query)))[:16])
        if not q:
            return []
        try:
            return [int(r[0]) for r in con.execute(
                "SELECT page FROM pages WHERE pages MATCH ? ORDER BY rank LIMIT ?", (q, k)).fetchall()]
        except sqlite3.OperationalError:
            return []

    toc = {'sec_index': {'claim': claims.get('sec_index'), 'actual': sec_index, 'fts5': fts_top('一、词条索引（按笔画序')},
           'sec_subject': {'claim': claims.get('sec_subject'), 'actual': sec_subject, 'fts5': fts_top('二、主题词索引（subject-index：')},
           'sec_body': {'claim': claims.get('sec_body'), 'actual': body_start, 'fts5': []}}
    for v in toc.values():
        v['pass'] = (v['actual'] is not None and v['claim'] == v['actual'])

    bad = []; ok = 0; unsat = 0
    for no, head in heads.items():
        claim = claims.get('e' + no)
        if claim is None:
            unsat += 1; continue
        pat = no + head
        cands = fts_top(f'{no} {head}')
        real = next((p for p in cands if pat in flat(texts[p - 1])), None)
        # 兜底①：直接核对「声称页」（编号+词目 唯一）
        if real is None and claim and 1 <= claim <= len(texts) and pat in flat(texts[claim - 1]):
            real = claim
        # 兜底②：全量扫描（同名条目多时 FTS5 候选会落空）
        if real is None:
            real = next((i + 1 for i, t in enumerate(texts) if pat in flat(t)), None)
        if real is None:
            bad.append({'no': no, 'head': head, 'claim': claim, 'fts5': cands, 'why': '未定位'})
        elif real != claim:
            bad.append({'no': no, 'head': head, 'claim': claim, 'fts5': cands, 'actual': real, 'why': '页码不符'})
        else:
            ok += 1

    rep = {'pdf_pages': len(texts), 'body_start': body_start, 'body_pages_indexed': n_body,
           'fields': len(claims), 'index_ok': ok, 'index_bad': len(bad), 'index_unmatched': unsat,
           'toc': toc, 'bad_sample': bad[:10], 'pass': all(v['pass'] for v in toc.values()) and not bad}
    json.dump(rep, open(os.path.join(DIST, 'fts5_page_audit.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    print(f"正文起点 P{body_start} | 入索引正文页 {n_body} | PDF {len(texts)} 页")
    print('目录: ' + ' | '.join(f"{k} 标注{v['claim']} 实际{v['actual']} {'PASS' if v['pass'] else 'FAIL'}" for k, v in toc.items()))
    print(f"索引词条: 一致 {ok} | 不符 {len(bad)} | 无域 {unsat}")
    for b in bad[:6]:
        print('  !', b)
    print('FTS5 PAGE AUDIT', 'OK' if rep['pass'] else 'FAIL')


if __name__ == '__main__':
    main()
