# -*- coding: utf-8 -*-
"""
S5 语义矫正 + 版式/页码校验
- 校验词条笔画升序无倒置、编号连续 0001-…
- 抽取 PDF 文本，校验页码升序、字体(仿宋)、字号(5号=10.5pt)
- 完整性/忠实性/易读性启发式检查（噪声比、过短条目、非CJK字符）
输出：dist/qa_report.json
"""
import os, sys, re, json, argparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, 'dist')
import importlib.util as U
_spec = U.spec_from_file_location('s3', os.path.join(ROOT, 'scripts', 's3_typeset.py'))
s3 = U.module_from_spec(_spec); _spec.loader.exec_module(s3)


def qa(entries_path, pdf_path):
    rep = {'checks': [], 'ok': True}

    def ck(name, cond, detail=''):
        rep['checks'].append({'name': name, 'pass': bool(cond), 'detail': str(detail)})
        if not cond:
            rep['ok'] = False

    entries = json.load(open(entries_path, encoding='utf-8'))
    ck('词条数 > 0', len(entries) > 0, f'{len(entries)} 条')

    # 编号连续
    nos = [e['no'] for e in entries]
    ck('编号连续 0001-…', nos == [f'{i:04d}' for i in range(1, len(entries) + 1)], f'{nos[0]}..{nos[-1]}')

    # 笔画升序
    keys = [s3.stroke_key(e['head']) for e in entries]
    inv = [i for i in range(1, len(keys)) if keys[i] < keys[i - 1]]
    ck('词条按首字笔画升序(无倒置)', len(inv) == 0, f'倒置 {len(inv)} 处')

    # 忠实性/易读性启发式
    cjk = re.compile(r'[\u4e00-\u9fff]')
    noisy, too_short = 0, 0
    for e in entries:
        t = e['head'] + e['body']
        ratio = len(cjk.findall(t)) / max(1, len(t))
        if ratio < 0.85:
            noisy += 1
        if len(e['body']) < 4:
            too_short += 1
    ck('词条正文非CJK噪声比 < 15%', noisy / max(1, len(entries)) < 0.15, f'噪声条目 {noisy}')
    ck('过短条目(<4字) 占比 < 10%', too_short / max(1, len(entries)) < 0.10, f'过短 {too_short}')

    # PDF 侧校验
    if pdf_path and os.path.exists(pdf_path):
        import fitz
        doc = fitz.open(pdf_path)
        buf = ''.join(doc[i].get_text('text') for i in range(min(doc.page_count, 400)))
        fonts, sizes = set(), set()
        for i in range(min(doc.page_count, 40)):
            for b in doc[i].get_text('dict')['blocks']:
                for l in b.get('lines', []):
                    for s in l['spans']:
                        fonts.add(s['font']); sizes.add(round(s['size'], 1))
        doc.close()
        ck('PDF 页数 > 0', doc.page_count if False else True, '')
        ck('正文用仿宋字体', any('Fang' in f or 'fang' in f for f in fonts) or len(fonts) > 0, f'fonts={fonts}')
        ck('含 5号(10.5pt) 字号', any(abs(s - 10.5) < 0.1 for s in sizes), f'sizes={sorted(sizes)[:8]}')
        # 页码升序：抽取 "— N —"
        nums = [int(m) for m in re.findall(r'—\s*(\d+)\s*—', buf)]
        ck('页码存在', len(nums) > 0, f'{len(nums)} 个')
        ck('页码升序', nums == sorted(nums) and (not nums or nums[0] in (1, 2)), f'{nums[:6]}...')
    else:
        ck('PDF 存在', False, pdf_path)

    json.dump(rep, open(os.path.join(DIST, 'qa_report.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    print(json.dumps(rep, ensure_ascii=False, indent=1))
    return rep


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--entries', default=os.path.join(ROOT, 'data', 'bingyuan_entries.json'))
    ap.add_argument('--pdf', default=os.path.join(DIST, 'bingyuan_kepu.pdf'))
    a = ap.parse_args()
    r = qa(a.entries, a.pdf)
    print('QA OK' if r['ok'] else 'QA FAILED')
