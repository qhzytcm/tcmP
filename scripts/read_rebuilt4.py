# -*- coding: utf-8 -*-
"""读取 rebuilt4 中 6.2.1.7 实际内容"""
import openpyxl

PATH = r'C:\Users\DELL\Desktop\qhzy-黄帝内经(通读注释版)_rebuilt4.xlsx'
try:
    wb = openpyxl.load_workbook(PATH, read_only=True)
    ws = wb['6.素问·经脉血气']
    for row in ws.iter_rows(min_row=2, max_col=3):
        if row[1].value == '6.2.1.7':
            v = str(row[2].value)
            print(f"len={len(v)}")
            print(f"repr: {repr(v)}")
            break
    wb.close()
except Exception as e:
    print(f"读取失败: {e}")
