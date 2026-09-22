# -*- coding: utf-8 -*-
"""
S64 校勘底本生成：按「页 → 栏 → 列」重建 OCR 文字对应，保留原印刷版式
输出：
  dist/pdf3_layout.json          结构：page → bands → columns（含书眉/页脚侧位）
  C:\\Users\\DELL\\Desktop\\03-bycd-校勘底本.docx   人可读，逐页逐栏逐列
要点：**用原始 OCR 文字（不转简、不校字）**，与扫描件逐字对应，便于人工校对。
"""
import os, re, json, argparse, sys
import pymupdf
from docx import Document
from docx.shared import Pt, Mm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, 'data', 'bingyuan3_ocr')
DIST = os.path.join(ROOT, 'dist'); os.makedirs(DIST, exist_ok=True)
DESKTOP = r'C:\Users\DELL\Desktop'
TOTAL = 1182


def seg_of(pg):
    """返回 (区段名, 原书编码, 栏数)"""
    if pg <= 11:
        return '前置', f'前置{pg+1:02d}', 3
    if 12 <= pg <= 58:
        return '目录', f'目录{pg-11:02d}', 4
    if 59 <= pg <= 1176:
        return '正文', f'正文{pg-58:04d}', 3
    if 1177 <= pg <= 1179:
        return '增补', f'增补{pg-1176+1118:04d}', 3
    return '尾页', f'尾页{pg-1179:02d}', 3


def bands_of(pg):
    """按 y 切横栏，返回 [[列文本,...], ...]（列序右→左，列内字上→下）+ 书眉侧位"""
    fp = os.path.join(RES, f'page_{pg:04d}.json')
    if not os.path.exists(fp):
        return None
    d = json.load(open(fp, encoding='utf-8'))
    L = []
    for x in d['lines']:
        xs = [p[0] for p in x['box']]; ys = [p[1] for p in x['box']]
        if x['text'].strip():
            L.append((sum(xs) / 4, sum(ys) / 4, x['text'].strip()))
    if not L:
        return {'bands': [], 'head': '', 'side': ''}
    nb = seg_of(pg)[2]
    ymin = min(i[1] for i in L); ymax = max(i[1] for i in L)
    span = max(1.0, ymax - ymin)
    xmin = min(i[0] for i in L); xmax = max(i[0] for i in L)
    bands = []
    for b in range(nb):
        lo = ymin + span * b / nb
        seg = ([i for i in L if lo <= i[1] < ymin + span * (b + 1) / nb]
               if b < nb - 1 else [i for i in L if i[1] >= lo])
        if not seg:
            bands.append([]); continue
        cols = []
        for cx, cy, t in sorted(seg, key=lambda z: -z[0]):
            for c in cols:
                if abs(c['cx'] - cx) < 45:
                    c['segs'].append((cy, t)); break
            else:
                cols.append({'cx': cx, 'segs': [(cy, t)]})
        cols.sort(key=lambda c: -c['cx'])
        bands.append([''.join(t for _, t in sorted(c['segs'])) for c in cols])
    # 书眉/中缝判定（**以中缝为基准**，不用奇偶规律）：
    #   书眉在右 ⟹ 中缝在左 ⟹ 本页=前页(中缝右侧页)，带页眉
    #   书眉在左 ⟹ 中缝在右 ⟹ 本页=后页(中缝左侧页)，带页尾
    #   两端皆有  ⟹ 中缝居中 ⟹ 该扫描页含「对开双页」
    # 书眉识别用**精确白名单**（勿用单字松匹配，否则正文「病源群見…」会误判）
    try:
        from ocr_fix_rules import BOOKNAME_V
        _KEYS = tuple(v for v in BOOKNAME_V) + ('病源辞典',)
    except Exception:
        _KEYS = ('病源典', '病源静典', '病源醉典', '病源爵典', '病源辞典')
    hs = [(cx, t) for cx, cy, t in L if len(t) <= 14 and any(k in t for k in _KEYS)]
    head, side, page_kind, zf = '', '', '', ''
    if hs:
        band = (xmax - xmin) * 0.12
        lefts = [t for cx, t in hs if cx <= xmin + band]
        rights = [t for cx, t in hs if cx >= xmax - band]
        if lefts and rights:
            side = '左右'; zf = '居中(对开双页)'
            page_kind = '双页'
            head = f'左:{lefts[0]}｜右:{rights[-1]}'
        elif rights:
            side = '右'; zf = '左'; page_kind = '前页'
            head = rights[-1]
        elif lefts:
            side = '左'; zf = '右'; page_kind = '后页'
            head = lefts[0]
    return {'bands': bands, 'head': head, 'side': side, 'zhongfeng': zf, 'kind': page_kind}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--lo', type=int, default=12)
    ap.add_argument('--hi', type=int, default=1179)
    ap.add_argument('--form', choices=['raw', 'simp', 'both'], default='both',
                    help='raw=繁体原文（对照扫描件）；simp=繁转简（保留原排版）；both=两份都出')
    a = ap.parse_args()
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from ocr_fix_rules import safe_t2s as to_simp     # 仅繁→简（不做校字，保持"识别原貌"）

    pages = {}
    for pg in range(a.lo, a.hi + 1):
        r = bands_of(pg)
        if r is None:
            continue
        seg, code, nb = seg_of(pg)
        r.update({'seg': seg, 'code': code, 'bands_n': nb, 'scan': pg})
        pages[pg] = r
    json.dump({'total': TOTAL, 'pages': {str(k): v for k, v in pages.items()}},
              open(os.path.join(DIST, 'pdf3_layout.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    print('结构已写 dist/pdf3_layout.json | 页数:', len(pages))

    BANDNAME = {3: ['上栏', '中栏', '下栏'], 4: ['上栏', '中上栏', '中下栏', '下栏']}

    def build(tf, tag, note):
        doc = Document()
        s = doc.sections[0]; s.page_width, s.page_height = Mm(210), Mm(297)
        st = doc.styles['Normal']; st.font.name = '仿宋'; st.font.size = Pt(10.5)
        p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(f'《病源辞典》OCR 校勘底本·{tag}（按原书印刷版式：页→栏→列）')
        r.bold = True; r.font.size = Pt(16)
        q = doc.add_paragraph(); q.alignment = WD_ALIGN_PARAGRAPH.CENTER
        q.add_run('底本：bycd/03-病源辞典.pdf（1182 页）　阅读序：栏自上而下 → 栏内列右→左 → 列内字上→下　'
                  + note).font.size = Pt(9)
        q2 = doc.add_paragraph(); q2.alignment = WD_ALIGN_PARAGRAPH.CENTER
        q2.add_run('中缝基准：书眉在右⟹中缝在左⟹前页(带页眉)｜书眉在左⟹中缝在右⟹后页(带页尾)｜两端皆有⟹对开双页').font.size = Pt(9)
        for pg, rr0 in pages.items():
            h = doc.add_paragraph()
            rr = h.add_run(f'【{rr0["code"]}】扫描 p{pg}　'
                           f'〔{rr0.get("kind") or "—"}〕书眉在{rr0["side"] or "?"}·中缝在{rr0.get("zhongfeng") or "?"}：'
                           f'{tf(rr0["head"]) or "—"}　（{rr0["bands_n"]} 栏）')
            rr.bold = True; rr.font.size = Pt(12)
            rr.font.color.rgb = RGBColor(0x1F, 0x4E, 0x79)
            for bi, cols in enumerate(rr0['bands']):
                nm = BANDNAME[rr0['bands_n']][bi] if bi < len(BANDNAME[rr0['bands_n']]) else f'栏{bi+1}'
                bh = doc.add_paragraph(); br = bh.add_run(f'　── {nm}（{len(cols)} 列）──')
                br.bold = True; br.font.size = Pt(10.5)
                if not cols:
                    doc.add_paragraph('　　（本栏无识别文本）'); continue
                for ci, txt in enumerate(cols, 1):
                    ttag = '最右' if ci == 1 else ('最左' if ci == len(cols) else '')
                    pp = doc.add_paragraph()
                    pp.add_run(f'　　[列{ci}{ttag}] ').bold = True
                    pp.add_run(tf(txt))
        out = os.path.join(DESKTOP, f'03-bycd-校勘底本{"" if tag.startswith("繁体") else "（简体）"}.docx')
        try:
            doc.save(out)
        except PermissionError:
            out = out.replace('.docx', '_新.docx')
            doc.save(out)
            print('  [!] 目标被 Word 占用，改存:', out)
        print('→', out, os.path.getsize(out), 'bytes')

    ident = lambda s: s
    if a.form in ('raw', 'both'):
        build(ident, '繁体原文', '文字为原始 OCR（繁体、未校字），与扫描件逐字对应')
    if a.form in ('simp', 'both'):
        build(lambda s: to_simp(s or ''), '繁转简', '繁体已转简体（**仍保持原印刷栏列排版**；未做内容校字）')


if __name__ == '__main__':
    main()
