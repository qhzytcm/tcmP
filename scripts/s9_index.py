# -*- coding: utf-8 -*-
"""
S9 目录 + 索引 创建与原著索引替代（三段式编译）
前置：目录(1页) → 一、词条索引(笔画序·编号·词目·ICD-11·页码) → 二、主题词索引 → 正文
三段式：①量前置页数 Ip 与节页 ②量正文相对页码 p_rel ③合成(索引页码 = p_rel + Ip；目录回填)
输出：dist/bingyuan_kepu.pdf · dist/entry_page_map.json · dist/toc.json
"""
import os, sys, json, argparse
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, 'dist'); os.makedirs(DIST, exist_ok=True)

import importlib.util as U
_spec = U.spec_from_file_location('s3', os.path.join(ROOT, 'scripts', 's3_typeset.py'))
s3 = U.module_from_spec(_spec); _spec.loader.exec_module(s3)

from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, PageBreak, KeepTogether)


class RecDoc(BaseDocTemplate):
    def __init__(self, *a, **k):
        self.page_map = {}       # 词条号 -> 页码
        self.sections = {}       # 节名 -> 起始页
        super().__init__(*a, **k)

    def afterFlowable(self, f):
        no = getattr(f, '_entry_no', None)
        if no:
            self.page_map.setdefault(no, self.page)
        sec = getattr(f, '_section', None)
        if sec:
            self.sections.setdefault(sec, self.page)


def _doc(out):
    d = RecDoc(out, pagesize=(s3.PAGE_W, s3.PAGE_H),
               leftMargin=s3.MARGIN, rightMargin=s3.MARGIN,
               topMargin=s3.MARGIN * 1.3, bottomMargin=s3.MARGIN * 1.2,
               title='病源辞典（简体科普版）', author='吴克潜 主编 / 简体科普整理')
    fw, fh = s3.COL_W, s3.PAGE_H - s3.MARGIN * 2.5
    fl = Frame(s3.MARGIN, s3.MARGIN * 1.2, fw, fh, id='L', leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    fr = Frame(s3.MARGIN + fw + s3.GUTTER, s3.MARGIN * 1.2, fw, fh, id='R', leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    d.addPageTemplates([PageTemplate(id='two', frames=[fl, fr], onPage=s3.draw_page_number)])
    return d


def _sec(story, styles, key, text):
    p = Paragraph(text, styles['h']); p._section = key
    story.append(p); story.append(Spacer(1, 5))


def _front_story(terms, idx, styles, toc, pmap):
    st = [Paragraph('目　录', styles['title']), Spacer(1, 10),
          Paragraph('本目录与索引替代原著《病名目录》。词条按首字笔画升序编排（原著凡例之序法），编号 0001-…。', styles['idx']),
          Spacer(1, 8)]
    t = toc or {}
    st.append(Paragraph(f'索引说明与编制体例 ………… P{t.get("说明", 1)}', styles['idx']))
    st.append(Paragraph(f'一、词条索引（编号·词目·ICD-11·页码）………… P{t.get("词条索引", "?")}', styles['idx']))
    st.append(Paragraph(f'二、主题词索引（subject-index）………… P{t.get("主题词索引", "?")}', styles['idx']))
    st.append(Paragraph(f'正文（词条 0001-{terms[-1]["no"] if terms else "?"}）………… P{t.get("正文", "?")}', styles['idx']))
    st.append(PageBreak())
    _sec(st, styles, '词条索引', '一、词条索引（按笔画序：编号 · 词目 · ICD-11 · 页码）')
    for e in terms:
        ic = e.get('icd11') or {}
        code = ic.get('code') or ''
        pg = (pmap or {}).get(e['no'], '?')
        tail = f'　{code}' if code else ''
        st.append(Paragraph(f'{e["no"]}　{e["head"]}{tail}　···　P{pg}', styles['idx']))
    st.append(PageBreak())
    _sec(st, styles, '主题词索引', '二、主题词索引（subject-index：主题词 · 编号范围）')
    for kw, nos in idx.items():
        rng = nos[0] + (f'-{nos[-1]}' if len(nos) > 1 else '')
        st.append(Paragraph(f'{kw}　{rng}（{len(nos)}条）', styles['idx']))
    st.append(PageBreak())            # 前置与正文之间强制分页
    return st


def _content_story(terms, styles):
    st = [Paragraph('正文', styles['h']), Spacer(1, 5)]
    for e in terms:
        ic = e.get('icd11') or {}
        tag = f'　［ICD-11 {ic["code"]}］' if ic.get('code') else ''
        p = Paragraph(f'{e["no"]}　{e["head"]}{tag}', styles['h']); p._entry_no = e['no']
        body = e.get('body') or ''.join(e.get('sections', {}).values())
        st.append(KeepTogether([p, Paragraph(body, styles['body'])]))
        st.append(Spacer(1, 5))
    return st


def build_book(terms, out, idx=None):
    """三段式编译：返回 (doc, toc, pmap_abs)"""
    for t in terms:
        t['body'] = t.get('body') or ''.join(t.get('sections', {}).values())
    if idx is None:
        idx = s3.build_subject_index(terms)
    styles = s3.make_styles()
    # ① 量前置
    d0 = _doc(os.path.join(DIST, '_front.pdf'))
    d0.build(_front_story(terms, idx, styles, toc=None, pmap={}))
    Ip = d0.page
    secs = dict(d0.sections)
    # ② 量正文相对页码
    d1 = _doc(os.path.join(DIST, '_content.pdf'))
    d1.build(_content_story(terms, styles) + [PageBreak()])
    pmap_abs = {no: p + Ip for no, p in d1.page_map.items()}
    # ③ 合成
    toc = {'说明': 1, '词条索引': secs.get('词条索引', 2),
           '主题词索引': secs.get('主题词索引'), '正文': Ip + 1}
    d2 = _doc(out)
    d2.build(_front_story(terms, idx, styles, toc=toc, pmap=pmap_abs) + _content_story(terms, styles))
    for f in ('_front.pdf', '_content.pdf'):
        try: os.remove(os.path.join(DIST, f))
        except Exception: pass
    return d2, toc, pmap_abs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--terms', default=os.path.join(ROOT, 'data', 'bingyuan_terms_icd.json'))
    ap.add_argument('--out', default=os.path.join(DIST, 'bingyuan_kepu.pdf'))
    a = ap.parse_args()
    terms = json.load(open(a.terms, encoding='utf-8'))
    print('词条数:', len(terms))
    d2, toc, pmap = build_book(terms, a.out)
    print(f'节页={toc} 词条页码样本={list(pmap.items())[:3]}')
    print(f'PDF: {a.out} ({os.path.getsize(a.out)/1024:.0f} KB), 总页 {d2.page}')
    json.dump(pmap, open(os.path.join(DIST, 'entry_page_map.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    json.dump(toc, open(os.path.join(DIST, 'toc.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)


if __name__ == '__main__':
    main()
