# -*- coding: utf-8 -*-
"""
S53 把已确立的校字规则应用到 03 清晰底本
① 校正全书阅读序文本流 → dist/pdf3_stream_fixed.json
② 重新切分病名单元 → data/pdf3_units_fixed.json
③ 重出两份 docx：03-bycd.docx / 03-bycd-三段结构.docx（加「已校」标记）
"""
import os, re, json
from collections import Counter
from docx import Document
from docx.shared import Pt, Mm
from docx.enum.text import WD_ALIGN_PARAGRAPH
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ocr_fix_rules import fix, SEQ

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, 'dist')
DESKTOP = r'C:\Users\DELL\Desktop'
RX_S, RX_Z, RX_F = re.compile(r'病源'), re.compile(r'病状'), re.compile(r'治法')
ORD = ('病源', '病状', '治法')


def parse_name(seg):
    j = seg.find('】')
    if 0 <= j <= 10:
        return seg[:j], seg[j + 1:]
    m = re.match(r'([\u4e00-\u9fff]{1,8}?)(?=[，,。；;：:（(0-9０-９]|病源|病状|治法)', seg)
    if m:
        return m.group(1), seg[m.end():]
    return seg[:5], seg[5:]


def split_sections(body):
    pos = {}
    for k, rx in (('病源', RX_S), ('病状', RX_Z), ('治法', RX_F)):
        m = rx.search(body)
        if m:
            pos[k] = m.start()
    if not pos:
        return {'全': body}
    order = sorted(pos.items(), key=lambda kv: kv[1])
    out = {}
    for i, (k, p) in enumerate(order):
        e = order[i + 1][1] if i + 1 < len(order) else len(body)
        seg = body[p:e]
        if seg.startswith(k):
            seg = seg[len(k):]
        out[k] = seg
    if order[0][1] > 0:
        out[order[0][0]] = body[:order[0][1]] + out[order[0][0]]
    return out


def main():
    raw = json.load(open(os.path.join(DIST, 'pdf3_stream.json'), encoding='utf-8'))['full']
    print('原流字数:', len(raw))
    fixed = fix(raw)
    # 统计规则命中
    hit = Counter()
    for a, b in SEQ:
        n = raw.count(a)
        if n:
            hit[f'{a}→{b}'] += n
    json.dump({'full': fixed, 'rules_hit': dict(hit.most_common())},
              open(os.path.join(DIST, 'pdf3_stream_fixed.json'), 'w', encoding='utf-8'), ensure_ascii=False)
    print('校正后字数:', len(fixed))
    print('规则命中:', dict(hit.most_common(14)))

    # ② 重新切分
    idx = [m.start() for m in re.finditer('【', fixed)]
    units = []
    for i, p in enumerate(idx):
        end = idx[i + 1] if i + 1 < len(idx) else len(fixed)
        seg = fixed[p + 1:end]
        name, body = parse_name(seg)
        name = name.strip()
        if not name or len(name) > 12:
            continue
        sec = split_sections(body)
        units.append({'name': name, 'body': body, 'sections': sec,
                      'has': {k: (k in sec) for k in ORD}})
    json.dump(units, open(os.path.join(ROOT, 'data', 'pdf3_units_fixed.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=0)
    st = Counter()
    for u in units:
        for k in ORD:
            if u['has'][k]:
                st[k] += 1
        st['三段齐备'] += all(u['has'].values())
    print('病名单元:', len(units), '| 分段:', dict(st))

    # ③ 结构 docx
    doc = Document()
    s = doc.sections[0]; s.page_width, s.page_height = Mm(210), Mm(297)
    stl = doc.styles['Normal']; stl.font.name = '仿宋'; stl.font.size = Pt(10.5)
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run('《病源辞典》病名单元·三段结构（bycd/03 清晰本 OCR·已校字）')
    r.bold = True; r.font.size = Pt(16)
    q = doc.add_paragraph(); q.alignment = WD_ALIGN_PARAGRAPH.CENTER
    q.add_run(f'共 {len(units)} 个病名单元　三段齐备 {st["三段齐备"]}　已应用校字规则').font.size = Pt(10)
    for i, u in enumerate(units, 1):
        h = doc.add_paragraph(); rr = h.add_run(f'{i:04d}　{u["name"]}')
        rr.bold = True; rr.font.size = Pt(12)
        sec = u.get('sections') or {}
        if not sec:
            doc.add_paragraph('（无正文内容）'); continue
        for k in ORD:
            if k in sec:
                doc.add_paragraph(f'{k}：{sec[k]}')
        for k, v in sec.items():
            if k not in ORD:
                doc.add_paragraph(v)
    out2 = os.path.join(DESKTOP, '03-bycd-三段结构.docx')
    doc.save(out2)
    print('→', out2, os.path.getsize(out2), 'bytes')


if __name__ == '__main__':
    main()
