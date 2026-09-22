# -*- coding: utf-8 -*-
"""S23a 用 Word COM 导出 docx→PDF（须 Anaconda python：有 win32com；不含 sqlite 故不段错误）"""
import os, sys, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from s12_docx_verify import export_pdf

ap = argparse.ArgumentParser()
ap.add_argument('--docx', required=True)
ap.add_argument('--pdf', required=True)
a = ap.parse_args()
pages = export_pdf(a.docx, a.pdf)
print('WORD_PAGES', pages, '| pdf:', a.pdf, os.path.getsize(a.pdf))
