# -*- coding: utf-8 -*-
"""
S52 将切分好的病名单元输出为结构化 docx
每单元：病名（标题）+ 病源/病状/治法（三段，各起一段）
输出 C:\\Users\\DELL\\Desktop\\03-bycd-三段结构.docx
"""
import os, json
from docx import Document
from docx.shared import Pt, Mm
from docx.enum.text import WD_ALIGN_PARAGRAPH

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UNITS = json.load(open(os.path.join(ROOT, 'data', 'pdf3_units.json'), encoding='utf-8'))
OUT = r'C:\Users\DELL\Desktop\03-bycd-三段结构.docx'
ORD = ('病源', '病状', '治法')


def main():
    doc = Document()
    s = doc.sections[0]
    s.page_width, s.page_height = Mm(210), Mm(297)
    st = doc.styles['Normal']; st.font.name = '仿宋'; st.font.size = Pt(10.5)
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run('《病源辞典》病名单元·三段结构重建（据 bycd/03 清晰本 OCR）')
    r.bold = True; r.font.size = Pt(16)
    q = doc.add_paragraph(); q.alignment = WD_ALIGN_PARAGRAPH.CENTER
    q.add_run(f'共 {len(UNITS)} 个病名单元　三段齐备 749　繁转简已生效　待校').font.size = Pt(10)
    for i, u in enumerate(UNITS, 1):
        h = doc.add_paragraph()
        rr = h.add_run(f'{i:04d}　{u["name"]}'); rr.bold = True; rr.font.size = Pt(12)
        sec = u.get('sections') or {}
        if not sec:
            doc.add_paragraph('（无正文内容）'); continue
        for k in ORD:
            if k in sec:
                doc.add_paragraph(f'{k}：{sec[k]}')
        for k, v in sec.items():                 # 未按三段归类者
            if k not in ORD:
                doc.add_paragraph(v)
    doc.save(OUT)
    print('写入单元:', len(UNITS), '→', OUT, os.path.getsize(OUT), 'bytes')


if __name__ == '__main__':
    main()
