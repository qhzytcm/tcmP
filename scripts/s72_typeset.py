# -*- coding: utf-8 -*-
"""
S72 横行排版定稿（16开 · 双栏 · 简体 · 5号仿宋 · 页码升序 · 笔画索引）
输入：data/pdf3_units_v2.json（3899 单元）+ data/pdf3_llm_out.jsonl（LLM 校本）+ data/strokes.json
输出：C:\\Users\\DELL\\Desktop\\病源辞典_简体横排版.docx
要点：
  · 词条按**首字笔画 → 次字 → 三字…**多级升序编号 0001..N（依《凡例》）
  · 目录 / 笔画索引 的页码用 **PAGEREF 域（书签）**，由 Word 更新为**本文档真实页码**
  · 页脚 PAGE 域显示页码（升序）
"""
import os, sys, json, argparse, re
from collections import Counter, OrderedDict
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
from docx import Document
from docx.shared import Pt, Mm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.section import WD_SECTION
from s11_docx import (_set_font, set_style_font, set_columns,
                      add_bookmark, add_pageref, add_page_field, body_para)

DESKTOP = r'C:\Users\DELL\Desktop'
DATA = os.path.join(ROOT, 'data')
DIST = os.path.join(ROOT, 'dist')
MISS = 200            # 未收字的笔画兜底


def load_units():
    U = json.load(open(os.path.join(DATA, 'pdf3_units_v2.json'), encoding='utf-8'))
    outs = {}
    fp = os.path.join(DATA, 'pdf3_llm_out.jsonl')
    if os.path.exists(fp):
        for line in open(fp, encoding='utf-8', errors='replace'):
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except Exception:
                continue
            if r['i'] not in outs or (r.get('ok') and not outs[r['i']].get('ok')):
                outs[r['i']] = r
    out = []
    for i, u in enumerate(U):
        r = outs.get(i)
        txt = (r['out'] if (r and r.get('ok')) else u['body']) if r else u['body']
        flag = 'LLM校' if (r and r.get('ok')) else '原'
        out.append({'name': u['name'], 'body': txt, 'flag': flag, 'src': u['body']})
    return out


def stroke_keys(name, st):
    """多级笔画序：逐字 (笔画, 码位)；未收字笔画兜底 MISS"""
    out = []
    for ch in re.sub(r'[^\u4e00-\u9fff]', '', name)[:6]:
        out.append((st.get(ch, MISS), ord(ch)))
    return out or [(MISS, 0xFFFF)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default=os.path.join(DESKTOP, '病源辞典_简体横排版.docx'))
    a = ap.parse_args()
    units = load_units()
    ST = json.load(open(os.path.join(DATA, 'strokes.json'), encoding='utf-8'))
    print(f'单元 {len(units)} | 笔画表 {len(ST)}')

    # ── 排序：有名条目按多级笔画升序；**病名待定单独成组**（不污染笔画段）──
    named = [u for u in units if u['name'] != '病名待定']
    pending = [u for u in units if u['name'] == '病名待定']
    for u in named:
        u['key'] = stroke_keys(u['name'], ST)
    named.sort(key=lambda u: (u['key'], u['name']))
    for u in pending:
        u['key'] = [(MISS, 0xFFFF)]
    units = named + pending
    for i, u in enumerate(units, 1):
        u['no'] = f'{i:04d}'
    print(f'有名 {len(named)} | 待定 {len(pending)}（置于末尾）')

    doc = Document()
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Mm(196.75), Mm(273)      # 16 开
    sec.left_margin = sec.right_margin = Mm(18)
    sec.top_margin = sec.bottom_margin = Mm(18)
    set_style_font(doc.styles['Normal'], '仿宋', 10.5)          # 5 号仿宋
    for nm, sz, fn in [('Title', 20, '黑体'), ('Heading 1', 14, '黑体'), ('Heading 2', 12, '黑体')]:
        try:
            set_style_font(doc.styles[nm], fn, sz)
        except Exception:
            pass
    fp = sec.footer.paragraphs[0]; fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = fp.add_run('— '); _set_font(r, '仿宋', 9)
    add_page_field(fp)
    r2 = fp.add_run(' —'); _set_font(r2, '仿宋', 9)

    # ── 封面 ──
    for _ in range(4):
        doc.add_paragraph()
    t = doc.add_paragraph(); t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = t.add_run('病　源　辞　典'); _set_font(r, '黑体', 30, bold=True)
    st = doc.add_paragraph(); st.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = st.add_run('（简体横排版）'); _set_font(r, '黑体', 16)
    doc.add_paragraph()
    for line in ['吴克潜　主编', '', '底本：一九三五年铅印本（bycd/03-病源辞典.pdf，1182 页）',
                 '整理：逐栏阅读重建 · 繁转简 · 文本校勘 · 按首字笔画多级升序',
                 f'词条　{len(units)}　条']:
        pp = doc.add_paragraph(); pp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = pp.add_run(line); _set_font(r, '仿宋', 12)
    doc.add_page_break()

    # ── 自序 / 凡例 ──
    try:
        fm = json.load(open(os.path.join(DATA, 'front_matter.json'), encoding='utf-8'))
    except Exception:
        fm = {'preface_title': '自　序', 'preface': [], 'notes_title': '凡　例', 'notes': []}
    h = doc.add_paragraph(); h.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = h.add_run(fm['preface_title']); _set_font(r, '黑体', 16, bold=True)
    add_bookmark(h, 'sec_preface', 900003)
    for para in fm.get('preface', []):
        body_para(doc, para, 10.5)
    doc.add_page_break()
    h = doc.add_paragraph(); h.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = h.add_run(fm['notes_title']); _set_font(r, '黑体', 16, bold=True)
    add_bookmark(h, 'sec_notes', 900004)
    for kv in fm.get('notes', []):
        k, v = (kv if isinstance(kv, (list, tuple)) else (kv, ''))
        body_para(doc, f'{k}　{v}', 10.5)
    doc.add_page_break()

    # ── 目录 ──
    h = doc.add_paragraph(); h.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = h.add_run('目　录'); _set_font(r, '黑体', 16, bold=True)
    doc.add_paragraph()
    for key, cn in [('sec_preface', '自序'), ('sec_notes', '凡例'),
                    ('sec_toc', '病名目录（原书 目录01–47）'),
                    ('sec_index', '笔画索引（编号 · 词目 · 页码）'),
                    ('sec_body', '正文（词条 0001–%s）' % (units[-1]['no'] if units else '?'))]:
        p = doc.add_paragraph()
        r = p.add_run(cn + '　…………　P'); _set_font(r, '仿宋', 10.5)
        add_pageref(p, key, cached='1')
    doc.add_page_break()

    # ── 病名目录（原书目录流）──
    h = doc.add_paragraph(); r = h.add_run('病名目录（据原书 病名目录 01–47 页）')
    _set_font(r, '黑体', 14, bold=True); add_bookmark(h, 'sec_toc', 900005)
    try:
        toc = json.load(open(os.path.join(DIST, 'pdf3_toc_stream.json'), encoding='utf-8'))['pages']
        for it in toc:
            body_para(doc, it['text'], 10.5, indent=False)
    except Exception as e:
        body_para(doc, f'（目录数据缺失：{e}）', 10.5, indent=False)
    doc.add_page_break()

    # ── 笔画索引（PAGEREF 页码）──
    h = doc.add_paragraph()
    r = h.add_run('笔画索引（按首字笔画 → 次字 → 三字 多级升序）')
    _set_font(r, '黑体', 14, bold=True); add_bookmark(h, 'sec_index', 900000)
    cur = None
    for u in units:
        s = u['key'][0][0]
        if s != cur:
            cur = s
            sp = doc.add_paragraph()
            label = '〔病名待定〕（三段论拆分产生的待命名条目）' if s >= MISS else f'{s} 画'
            rr = sp.add_run(f'—— {label} ——')
            _set_font(rr, '黑体', 11, bold=True)
        p = doc.add_paragraph()
        r = p.add_run(f'{u["no"]}　{u["name"]}　···　P'); _set_font(r, '仿宋', 10.5)
        add_pageref(p, f'e{u["no"]}', cached='1')
    doc.add_page_break()

    # ── 正文（双栏 · 横行）──
    new_sec = doc.add_section(WD_SECTION.CONTINUOUS)
    set_columns(new_sec, 2)
    h = doc.add_paragraph(); r = h.add_run('正　文')
    _set_font(r, '黑体', 14, bold=True); add_bookmark(h, 'sec_body', 900002)
    for u in units:
        hp = doc.add_paragraph()
        rr = hp.add_run(f'{u["no"]}　{u["name"]}')
        _set_font(rr, '黑体', 10.5, bold=True, color=(0x7B, 0x1E, 0x1E))
        add_bookmark(hp, f'e{u["no"]}', 100000 + int(u['no']))
        b = u['body']
        b = (b.replace('病源', '[病源]', 1) if '病源' in b else b)
        b = (b.replace('病状', '　[病状]', 1) if '病状' in b else b)
        b = (b.replace('治法', '　[治法]', 1) if '治法' in b else b)
        body_para(doc, b, 10.5, indent=True)

    _tmp = a.out + '.tmp'
    try:
        doc.save(_tmp); os.replace(_tmp, a.out)
    except PermissionError:
        a.out = a.out.replace('.docx', '_新.docx')
        doc.save(a.out)
        print('  [!] 目标被占用，改存:', a.out)
    print(f'→ {a.out}  {os.path.getsize(a.out)} bytes | 词条 {len(units)}')
    print('  首 8:', [f'{u["no"]} {u["name"]}' for u in units[:8]])
    print('  末 4:', [f'{u["no"]} {u["name"]}' for u in units[-4:]])


if __name__ == '__main__':
    main()
