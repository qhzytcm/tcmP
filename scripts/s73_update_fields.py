# -*- coding: utf-8 -*-
"""
S73 用 Word COM 更新域（PAGEREF → 本文档真实页码）+ 导出 PDF + 报页数
用法：python scripts/s73_update_fields.py [docx路径]
"""
import os, sys, time
import win32com.client as win32

path = sys.argv[1] if len(sys.argv) > 1 else r'C:\Users\DELL\Desktop\病源辞典_简体横排版.docx'
path = os.path.abspath(path)
print('目标:', path, os.path.getsize(path), 'bytes', flush=True)

app = win32.gencache.EnsureDispatch('Word.Application')
app.Visible = False
app.DisplayAlerts = 0
doc = None
try:
    doc = app.Documents.Open(path, ReadOnly=False)
    n_pages = doc.ComputeStatistics(2)          # wdStatisticPages
    n_fields = doc.Fields.Count
    print(f'打开：{n_pages} 页 | 域 {n_fields}', flush=True)
    t0 = time.time()
    doc.Fields.Update()
    for s in doc.Sections:
        s.Footers(1).Range.Fields.Update()
    print(f'域已更新（{time.time()-t0:.0f}s）', flush=True)
    doc.Repaginate()
    n2 = doc.ComputeStatistics(2)
    print(f'更新后：{n2} 页', flush=True)
    doc.Save()
    pdf = os.path.splitext(path)[0] + '.pdf'
    doc.ExportAsFixedFormat(pdf, 17)            # wdExportFormatPDF
    print(f'PDF: {pdf} {os.path.getsize(pdf)} bytes | {n2} 页', flush=True)
finally:
    if doc is not None:
        doc.Close(True)
    app.Quit()
print('DONE')
