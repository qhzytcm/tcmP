# -*- coding: utf-8 -*-
"""查素问 11-13 篇 sheet 名"""
import pandas as pd

xl = pd.ExcelFile(r'C:\Users\DELL\Desktop\HDNJ音频理解(2).xls')
for s in xl.sheet_names:
    if s[0].isdigit() or s.startswith('SW'):
        print(s)
