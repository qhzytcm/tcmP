# -*- coding: utf-8 -*-
"""
S3+S4+S6 病源辭典 科普版 排版引擎
- 提取【词条】→ 按首字笔画升序编号 0001-…
- 16开双栏 从左到右 横排 简体 5号(10.5pt) 仿宋，正文全部内容，页码
- 生成主题词搜索索引 subject-index
输出：dist/bingyuan_kepu.pdf + data/bingyuan_entries.json + dist/subject_index.{json,csv}
"""
import os, sys, re, json, glob, argparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TxtD = os.path.join(ROOT, 'data', 'bingyuan_txt')
DIST = os.path.join(ROOT, 'dist')
os.makedirs(DIST, exist_ok=True)

from reportlab.lib.pagesizes import mm
from reportlab.lib.units import mm as MM
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph,
                                Spacer, NextPageTemplate, PageBreak, KeepTogether)

# 字体：仿宋(正文5号) + 黑体(标题/词条)
pdfmetrics.registerFont(TTFont('FangSong', r'C:\Windows\Fonts\simfang.ttf'))
pdfmetrics.registerFont(TTFont('SimHei', r'C:\Windows\Fonts\simhei.ttf'))
try:
    pdfmetrics.registerFont(TTFont('KaiTi', r'C:\Windows\Fonts\simkai.ttf'))
except Exception:
    pass

# 16开（787×1092mm / 16 = 196.75 × 273 mm）
PAGE_W, PAGE_H = 196.75 * MM, 273 * MM
MARGIN = 18 * MM
GUTTER = 8 * MM
COL_W = (PAGE_W - 2 * MARGIN - GUTTER) / 2
BODY_FS = 10.5            # 5号
LEAD = 15.75              # 1.5 倍行距

STROKES = json.load(open(os.path.join(ROOT, 'data', 'strokes.json'), encoding='utf-8'))


def stroke_key(headword):
    ks = []
    for ch in headword:
        ks.append(STROKES.get(ch, 999))
    return ks + [0] * (8 - len(ks))


def load_pages():
    out = []
    for fp in sorted(glob.glob(os.path.join(TxtD, 'page_*.txt'))):
        n = int(re.search(r'(\d+)', os.path.basename(fp)).group(1))
        out.append((n, open(fp, encoding='utf-8').read()))
    return out


def extract_entries(pages):
    """从含【】的内容页切词条。返回 [{head, body, src_pages}]"""
    entries = []
    buf_head, buf_body, src = None, [], set()
    for pg, txt in pages:
        # 以【…】为界切分
        parts = re.split(r'(【[^】]{1,14}】)', txt)
        for seg in parts:
            m = re.fullmatch(r'【([^】]{1,14})】', seg or '')
            if m:
                if buf_head:
                    entries.append({'head': buf_head, 'body': ''.join(buf_body).strip(), 'src': sorted(src)})
                buf_head, buf_body, src = m.group(1).strip(), [], {pg}
            elif buf_head is not None:
                buf_body.append(seg or '')
                src.add(pg)
        if buf_head is None and txt.strip():
            # 无【】页（序/目录等）跳过
            pass
    if buf_head:
        entries.append({'head': buf_head, 'body': ''.join(buf_body).strip(), 'src': sorted(src)})
    # 清洗：去孤立空白与明显噪声
    for e in entries:
        e['body'] = re.sub(r'[\s]+', '', e['body'])
    return [e for e in entries if e['head'] and len(e['body']) >= 2]


def build_subject_index(entries):
    """主题词索引：主题词 → 出现词条编号。主题词取 五脏/六淫/症状/治法/方剂 等关键词。"""
    import jieba
    SEED = ['风', '寒', '暑', '湿', '燥', '火', '热', '肝', '心', '脾', '肺', '肾',
            '气血', '痰', '瘀', '虚', '实', '泄泻', '咳嗽', '中风', '伤寒', '温病',
            '伤寒论', '金匮', '汤', '散', '丸', '灸', '针', '外治', '忌', '调摄']
    idx = {}
    for e in entries:
        text = e['head'] + e['body']
        toks = set(jieba.cut(text))
        for kw in SEED:
            if kw in text or kw in toks:
                idx.setdefault(kw, []).append(e['no'])
    return {k: v for k, v in sorted(idx.items(), key=lambda kv: stroke_key(kv[0]))}


def make_styles():
    return {
        'title': ParagraphStyle('t', fontName='SimHei', fontSize=20, leading=26, alignment=1),
        'h': ParagraphStyle('h', fontName='SimHei', fontSize=12, leading=18, textColor=colors.HexColor('#7B1E1E')),
        'body': ParagraphStyle('b', fontName='FangSong', fontSize=BODY_FS, leading=LEAD, firstLineIndent=BODY_FS * 2),
        'idx': ParagraphStyle('i', fontName='FangSong', fontSize=BODY_FS, leading=LEAD),
    }


def draw_page_number(canv, doc):
    canv.saveState()
    canv.setFont('FangSong', 9)          # 页码：小五号(9pt) 仿宋
    canv.setFillColor(colors.HexColor('#333333'))
    canv.drawCentredString(PAGE_W / 2, MARGIN * 0.55, f'— {doc.page} —')
    canv.setFont('FangSong', 8)
    canv.setFillColor(colors.HexColor('#888888'))
    canv.drawString(MARGIN, PAGE_H - MARGIN * 0.8, '病源辞典（简体科普版·16开双栏）')
    canv.drawRightString(PAGE_W - MARGIN, PAGE_H - MARGIN * 0.8, '按词首笔画升序 第0001-…条')
    canv.restoreState()


def build_pdf(entries, styles, out, with_index=True, idx=None):
    doc = BaseDocTemplate(out, pagesize=(PAGE_W, PAGE_H),
                          leftMargin=MARGIN, rightMargin=MARGIN,
                          topMargin=MARGIN * 1.3, bottomMargin=MARGIN * 1.2,
                          title='病源辞典（简体科普版）', author='吴克潜 主编 / 简体科普整理')
    fw = COL_W
    fh = PAGE_H - MARGIN * 2.5
    frame_l = Frame(MARGIN, MARGIN * 1.2, fw, fh, id='L',
                    leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    frame_r = Frame(MARGIN + fw + GUTTER, MARGIN * 1.2, fw, fh, id='R',
                    leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    doc.addPageTemplates([PageTemplate(id='two', frames=[frame_l, frame_r], onPage=draw_page_number)])

    story = [Paragraph('病源辞典 · 简体科普版', styles['title']), Spacer(1, 6),
             Paragraph('（吴克潜 主编　按词条首字笔画升序编排　16开双栏横排）', styles['idx']),
             Spacer(1, 10)]
    for e in entries:
        block = [Paragraph(f'{e["no"]}　{e["head"]}', styles['h']),
                 Paragraph(e['body'], styles['body'])]
        story.append(KeepTogether(block))
        story.append(Spacer(1, 5))
    if with_index and idx:
        story.append(PageBreak())
        story.append(Paragraph('主题词搜索索引（subject-index）', styles['title']))
        story.append(Spacer(1, 8))
        for kw, nos in idx.items():
            rng = f'{nos[0]}' + (f'-{nos[-1]}' if len(nos) > 1 else '')
            story.append(Paragraph(f'<b>{kw}</b>　{rng}（{len(nos)}条）', styles['idx']))
    doc.build(story)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default=os.path.join(DIST, 'bingyuan_kepu.pdf'))
    ap.add_argument('--content-from', type=int, default=None, help='正文起始PDF页(0基)')
    ap.add_argument('--max-entries', type=int, default=None)
    a = ap.parse_args()

    pages = load_pages()
    print(f'简化页数：{len(pages)}')
    if a.content_from is not None:
        pages = [(n, t) for n, t in pages if n >= a.content_from]
        print(f'正文范围：{len(pages)} 页')

    entries = extract_entries(pages)
    print(f'提取词条：{len(entries)}')
    entries.sort(key=lambda e: (stroke_key(e['head']), e['head']))
    for i, e in enumerate(entries, 1):
        e['no'] = f'{i:04d}'
    if a.max_entries:
        entries = entries[:a.max_entries]

    if not entries:
        print('⚠ 尚无【词条】可提取（正文页可能未OCR到）。跳过PDF。')
        return

    json.dump(entries, open(os.path.join(ROOT, 'data', 'bingyuan_entries.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    idx = build_subject_index(entries)
    json.dump(idx, open(os.path.join(DIST, 'subject_index.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    with open(os.path.join(DIST, 'subject_index.csv'), 'w', encoding='utf-8-sig') as f:
        f.write('主题词,条数,编号范围\n')
        for kw, nos in idx.items():
            f.write(f'{kw},{len(nos)},{nos[0]}-{nos[-1]}\n')

    st = make_styles()
    out = build_pdf(entries, st, a.out, idx=idx)
    print(f'PDF: {out} ({os.path.getsize(out)/1024:.0f} KB) | 词条 {len(entries)} | 主题词 {len(idx)}')


if __name__ == '__main__':
    main()
