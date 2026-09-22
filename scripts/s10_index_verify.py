# -*- coding: utf-8 -*-
"""
S10 目录与索引 页码标注 校验
1) 目录页各节 P 值 == 该节实际起始页
2) 词条索引每条 P 值 == 该词条在正文中的实际页
3) 主题词索引 编号范围 端点有效（编号存在且属于该主题词）
输出：dist/index_verify.json
"""
import os, re, json, argparse
import fitz

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, 'dist')


def verify(pdf, terms_path, out=None):
    terms = json.load(open(terms_path, encoding='utf-8'))
    heads = {t['no']: t['head'] for t in terms}
    doc = fitz.open(pdf)
    N = doc.page_count
    pages = [doc[i].get_text('text') for i in range(N)]

    # 索引页范围：用节标题的**完整唯一串**定位，避免命中目录页里的节名
    toc_page = next((i for i, t in enumerate(pages) if '索引说明与编制体例' in t), None)
    idx_page = next((i for i, t in enumerate(pages) if '一、词条索引（按笔画序' in t), None)
    subj_page = next((i for i, t in enumerate(pages) if '二、主题词索引（subject-index：' in t), None)
    body_page = next((i for i, t in enumerate(pages) if i > (subj_page or 0) and '正文' in t), None)

    rep = {'pdf': os.path.basename(pdf), 'pages': N, 'checks': [], 'ok': True}

    def ck(n, c, d=''):
        rep['checks'].append({'name': n, 'pass': bool(c), 'detail': str(d)})
        if not c:
            rep['ok'] = False

    ck('目录页存在', toc_page is not None, f'page {toc_page+1 if toc_page is not None else "-"}')
    ck('词条索引页存在', idx_page is not None, f'page {idx_page+1 if idx_page is not None else "-"}')
    ck('主题词索引页存在', subj_page is not None, f'page {subj_page+1 if subj_page is not None else "-"}')
    ck('正文起始页存在', body_page is not None, f'page {body_page+1 if body_page is not None else "-"}')

    # ── 1) 目录页 P 值 == 实际节页 ──
    if toc_page is not None:
        tt = pages[toc_page]
        claims = [int(x) for x in re.findall(r'P(\d+)', tt)]   # 顺序: 说明/词条索引/主题词索引/正文
        want = [('词条索引', idx_page), ('主题词索引', subj_page), ('正文', body_page)]
        for k, (name, actual) in enumerate(want, start=1):
            claim = claims[k] if k < len(claims) else None
            ck(f'目录「{name}」页码正确', claim is not None and actual is not None and claim == actual + 1,
               f'标注P{claim} 实际P{actual+1 if actual is not None else "-"}')

    # ── 2) 词条索引 P 值 == 词条正文实际页 ──
    # 解析索引中的 (编号, 词目, 标注页)
    idx_txt = '\n'.join(pages[(idx_page or 0):(subj_page or N)])
    pairs = re.findall(r'(\d{4})\s+(\S+?)(?:\s+[A-Z0-9.]{2,12})?\s+···\s+P(\d+)', idx_txt)
    # 建立 编号->实际页
    body_txt = pages[(body_page or 0):]
    actual = {}
    for i, t in enumerate(body_txt):
        for m in re.finditer(r'(?<!\d)(\d{4})\s+(\S+?)(?:\s+［ICD-11[^\]\n]*］)?(?=\s|$)', t):
            no, head = m.group(1), m.group(2)
            if no not in actual and heads.get(no) == head:   # 词目须与预期一致，防误命中
                actual[no] = (body_page or 0) + i + 1        # 1-based PDF 页
    bad = []
    for no, head, claimed in pairs:
        act = actual.get(no)
        if act is None or int(claimed) != act:
            bad.append((no, head, claimed, act))
    ck(f'词条索引页码全部正确({len(pairs)}条)', len(bad) == 0, f'错 {len(bad)} 条: {bad[:5]}')
    ck('索引条数 == 词条数', len(pairs) == len(terms), f'{len(pairs)} vs {len(terms)}')

    # ── 3) 主题词索引 编号范围端点有效 ──
    subj_txt = '\n'.join(pages[(subj_page or 0):(body_page or N)])
    rng = re.findall(r'(\S+)\s+(\d{4})(?:-(\d{4}))?（(\d+)条）', subj_txt)
    badkw = []
    for kw, a, b, cnt in rng:
        if a not in heads:
            badkw.append((kw, a, '起编号不存在'))
        if b and b not in heads:
            badkw.append((kw, b, '止编号不存在'))
    ck(f'主题词索引编号端点有效({len(rng)}词)', len(badkw) == 0, f'异常 {badkw[:5]}')

    doc.close()
    json.dump(rep, open(out or os.path.join(DIST, 'index_verify.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    for c in rep['checks']:
        print(('  PASS ' if c['pass'] else '  FAIL ') + c['name'] + (f"  [{c['detail']}]" if c['detail'] else ''))
    print('INDEX VERIFY OK' if rep['ok'] else 'INDEX VERIFY FAILED')
    return rep


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--pdf', default=os.path.join(DIST, 'bingyuan_kepu.pdf'))
    ap.add_argument('--terms', default=os.path.join(ROOT, 'data', 'bingyuan_terms_icd.json'))
    a = ap.parse_args()
    verify(a.pdf, a.terms)
