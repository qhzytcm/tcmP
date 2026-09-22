# -*- coding: utf-8 -*-
"""
S11 文本文字排版 → docx（16开双栏 简体 5号仿宋）
- 目录 / 词条索引 / 主题词索引 的页码用 PAGEREF 域（书签），由 Word 更新为**本文档真实页码**
- 页脚 PAGE 域显示页码
输出：C:\\Users\\DELL\\Desktop\\病源辞典_简体科普版_文字排版.docx
"""
import os, sys, json, argparse, time
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from docx import Document
from docx.shared import Pt, Mm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.section import WD_SECTION
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

DESKTOP = r'C:\Users\DELL\Desktop'


# ── 底层 XML 助手 ──────────────────────────────────────────
def _set_font(run, name, size, bold=False, color=None):
    run.font.name = name; run.font.size = Pt(size); run.font.bold = bold
    run._element.rPr.rFonts.set(qn('w:eastAsia'), name)
    if color:
        run.font.color.rgb = RGBColor(*color)


def set_style_font(style, name='仿宋', size=10.5):
    style.font.name = name; style.font.size = Pt(size)
    rpr = style.element.get_or_add_rPr()
    rf = rpr.find(qn('w:rFonts'))
    if rf is None:
        rf = rpr.makeelement(qn('w:rFonts'), {}); rpr.append(rf)
    for a in ('w:eastAsia', 'w:ascii', 'w:hAnsi'):
        rf.set(qn(a), name)


def set_columns(section, num=2, space_twips=454):
    sectPr = section._sectPr
    cols = sectPr.find(qn('w:cols'))
    if cols is None:
        cols = OxmlElement('w:cols'); sectPr.append(cols)
    cols.set(qn('w:num'), str(num)); cols.set(qn('w:space'), str(space_twips))
    cols.set(qn('w:equalWidth'), '1')


def add_bookmark(paragraph, name, bid):
    s = OxmlElement('w:bookmarkStart'); s.set(qn('w:id'), str(bid)); s.set(qn('w:name'), name)
    e = OxmlElement('w:bookmarkEnd'); e.set(qn('w:id'), str(bid))
    paragraph._p.insert(0, s); paragraph._p.append(e)


def add_pageref(paragraph, bookmark, cached='1'):
    fld = OxmlElement('w:fldSimple'); fld.set(qn('w:instr'), f' PAGEREF {bookmark} \\h ')
    r = OxmlElement('w:r'); t = OxmlElement('w:t'); t.text = str(cached)
    r.append(t); fld.append(r); paragraph._p.append(fld)


def add_page_field(paragraph):
    fld = OxmlElement('w:fldSimple'); fld.set(qn('w:instr'), ' PAGE ')
    r = OxmlElement('w:r'); t = OxmlElement('w:t'); t.text = '1'
    r.append(t); fld.append(r); paragraph._p.append(fld)


def body_para(doc, text, size=10.5, name='仿宋', align=None, indent=True):
    p = doc.add_paragraph()
    if align:
        p.alignment = align
    if indent:
        p.paragraph_format.first_line_indent = Pt(size * 2)
    r = p.add_run(text); _set_font(r, name, size)
    return p


def build_docx(terms, out, subject_index, toc_pages=None):
    _tmp = out + '.tmp'
    doc = Document()
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Mm(196.75), Mm(273)
    sec.left_margin = sec.right_margin = Mm(18)
    sec.top_margin = sec.bottom_margin = Mm(18)
    set_style_font(doc.styles['Normal'], '仿宋', 10.5)
    for nm, sz, fn in [('Title', 20, '黑体'), ('Heading 1', 14, '黑体'), ('Heading 2', 12, '黑体')]:
        if nm in [s.name for s in doc.styles]:
            set_style_font(doc.styles[nm], fn, sz)

    # 页脚页码（PAGE 域）
    footer = sec.footer
    fp = footer.paragraphs[0]; fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = fp.add_run('— '); _set_font(r, '仿宋', 9)
    add_page_field(fp)
    r2 = fp.add_run(' —'); _set_font(r2, '仿宋', 9)

    # ── 封面 / 目录 ──
    t = doc.add_paragraph(); t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = t.add_run('病源辞典（简体科普版·文字排版）'); _set_font(r, '黑体', 22, bold=True)
    st = doc.add_paragraph(); st.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = st.add_run('吴克潜 主编　简体科普整理　16开双栏 5号仿宋　按病名首字笔画（次字、三字递推）升序　'
                   '编号 0001-…　含自序·凡例·别名条目')
    _set_font(r, '仿宋', 10.5, color=(0x66, 0x66, 0x66))
    doc.add_page_break()
    # ── 自序 ──
    try:
        _fm = json.load(open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                          'data', 'front_matter.json'), encoding='utf-8'))
    except Exception:
        _fm = {'preface_title': '自　序', 'preface': [], 'notes_title': '凡　例', 'notes': []}
    hp = doc.add_paragraph(); hp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = hp.add_run(_fm['preface_title']); _set_font(r, '黑体', 16, bold=True)
    add_bookmark(hp, 'sec_preface', 900003)
    for para in _fm['preface']:
        body_para(doc, para, 10.5)
    doc.add_page_break()
    # ── 凡例 ──
    hp = doc.add_paragraph(); hp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = hp.add_run(_fm['notes_title']); _set_font(r, '黑体', 16, bold=True)
    add_bookmark(hp, 'sec_notes', 900004)
    for k, v in _fm['notes']:
        body_para(doc, f'{k}　{v}', 10.5)
    doc.add_page_break()
    # ── 目录 ──
    h = doc.add_paragraph(); h.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = h.add_run('目　录'); _set_font(r, '黑体', 16, bold=True)
    doc.add_paragraph()

    for key, cn in [('sec_preface', '自序'), ('sec_notes', '凡例'),
                    ('sec_index', '一、词条索引（编号·词目·ICD-11·页码）'),
                    ('sec_subject', '二、主题词索引（subject-index）'),
                    ('sec_body', '正文（词条 %s-%s）' % (terms[0]['no'] if terms else '?',
                                                      terms[-1]['no'] if terms else '?'))]:
        p = doc.add_paragraph()
        r = p.add_run(cn + '　…………　P'); _set_font(r, '仿宋', 10.5)
        add_pageref(p, key, cached=(toc_pages or {}).get(key, '1'))

    doc.add_page_break()
    # ── 一、词条索引 ──
    hp = doc.add_paragraph(); r = hp.add_run('一、词条索引（按笔画序：编号 · 词目 · ICD-11 · 页码）')
    _set_font(r, '黑体', 12, bold=True); add_bookmark(hp, 'sec_index', 900000)
    for e in terms:
        ic = e.get('icd11') or {}
        code = ('　' + ic['code']) if ic.get('code') else ''
        al = ('　〔别名：' + '、'.join(e['alias']) + '〕') if e.get('alias') else ''
        pd = ('　〔病名待定·原属' + (e.get('parent') or '') + '〕') if e['head'] == '病名待定' else ''
        p = doc.add_paragraph()
        r = p.add_run(f'{e["no"]}　{e["head"]}{al}{pd}{code}　···　P'); _set_font(r, '仿宋', 10.5)
        add_pageref(p, f'e{e["no"]}', cached='1')
    doc.add_page_break()
    # ── 二、主题词索引 ──
    hp = doc.add_paragraph(); r = hp.add_run('二、主题词索引（subject-index：主题词 · 编号范围）')
    _set_font(r, '黑体', 12, bold=True); add_bookmark(hp, 'sec_subject', 900001)
    for kw, nos in subject_index.items():
        rng = nos[0] + (f'-{nos[-1]}' if len(nos) > 1 else '')
        body_para(doc, f'{kw}　{rng}（{len(nos)}条）', 10.5, indent=False)
    doc.add_page_break()
    # ── 正文（双栏） ──
    new_sec = doc.add_section(WD_SECTION.CONTINUOUS)
    set_columns(new_sec, 2)
    hp = doc.add_paragraph(); r = hp.add_run('正文')
    _set_font(r, '黑体', 14, bold=True); add_bookmark(hp, 'sec_body', 900002)
    for e in terms:
        ic = e.get('icd11') or {}
        tag = f'　［ICD-11 {ic["code"]}］' if ic.get('code') else ''
        al = ('　〔别名：' + '、'.join(e['alias']) + '〕') if e.get('alias') else ''
        pd = ('　〔病名待定·原属' + (e.get('parent') or '') + '〕') if e['head'] == '病名待定' else ''
        hp = doc.add_paragraph()
        r = hp.add_run(f'{e["no"]}　{e["head"]}{al}{pd}{tag}'); _set_font(r, '黑体', 10.5, bold=True, color=(0x7B, 0x1E, 0x1E))
        add_bookmark(hp, f'e{e["no"]}', 100000 + int(e['no']))
        body = e.get('body') or ''.join(e.get('sections', {}).values())
        body_para(doc, body, 10.5)
        f5 = e.get('fts5') or e.get('ref')
        if f5:
            nm = f5.get('title') or f5.get('disease') or ''
            code = f5.get('code') or f5.get('icd11') or ''
            extra = f'　〔{f5.get("syndrome","")}〕' if f5.get('syndrome') else ''
            ap_ = doc.add_paragraph()
            r = ap_.add_run(f'　　〖FTS5 检索·权威对照：{nm}{extra}'
                            + (f'　ICD-11 {code}' if code else '')
                            + f'（重合 {f5.get("overlap")}）〗')
            _set_font(r, '仿宋', 9, color=(0x55, 0x55, 0x88))
    doc.save(_tmp)
    for _ in range(12):
        try:
            os.replace(_tmp, out)
            return out
        except PermissionError:
            time.sleep(1.5)
    os.replace(_tmp, out)
    return out


def update_fields_and_save(path, visible=False):
    """用 Word COM 更新域（PAGEREF/PAGE）→ 页码变为本文档真实页码。
    PAGEREF 依赖分页，须先 Repaginate，再逐域 Update，最后再 Repaginate。
    注意：Word 残态会抛 RPC_E_CALL_REJECTED（-2147418111）→ 用 DispatchEx 独立实例 + 重试。"""
    import win32com.client as w32
    import pythoncom
    last = None
    for attempt in range(4):
        word = None
        try:
            pythoncom.CoInitialize()
            word = w32.DispatchEx('Word.Application')      # 独立实例，避开残态
            word.Visible = visible
            word.DisplayAlerts = 0
            d = word.Documents.Open(path, ReadOnly=False)
            for _ in range(3):
                try:
                    d.Repaginate(); break
                except Exception:
                    time.sleep(2)
            # 整体更新域（逐域 Update 在 2800+ 域时极慢 → 只在整体更新后补一次）
            for _ in range(3):
                try:
                    d.Fields.Update(); break
                except Exception:
                    time.sleep(3)
            for _ in range(3):
                try:
                    d.Repaginate(); break
                except Exception:
                    time.sleep(2)
            d.Save(); d.Close(False)
            return
        except Exception as e:
            last = e
            time.sleep(3)
        finally:
            try:
                if word is not None:
                    word.Quit()
            except Exception:
                pass
    raise last


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--terms', default=os.path.join(ROOT, 'data', 'bingyuan_terms_icd.json'))
    ap.add_argument('--out', default=os.path.join(DESKTOP, '病源辞典_简体科普版_文字排版.docx'))
    a = ap.parse_args()
    terms = json.load(open(a.terms, encoding='utf-8'))
    for t in terms:
        t['body'] = t.get('body') or ''.join(t.get('sections', {}).values())
    import importlib.util as U
    spec = U.spec_from_file_location('s3', os.path.join(ROOT, 'scripts', 's3_typeset.py'))
    s3 = U.module_from_spec(spec); spec.loader.exec_module(s3)
    idx = s3.build_subject_index(terms)
    print('词条数:', len(terms))
    build_docx(terms, a.out, idx)
    print('docx(初稿):', a.out, os.path.getsize(a.out))
    print('更新域…')
    update_fields_and_save(a.out)
    print('docx(域已更新):', a.out, os.path.getsize(a.out))


if __name__ == '__main__':
    main()
