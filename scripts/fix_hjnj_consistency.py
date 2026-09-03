# -*- coding: utf-8 -*-
"""
全书一致性修复: 早期章节（1-15, 17章）注释统一补「悬疑/非零和」标注
（16, 18-31 章已达标, 跳过）
"""
import re, openpyxl

PATH = r'C:\Users\DELL\Desktop\qhzy-黄帝内经(通读注释版).xlsx'
wb = openpyxl.load_workbook(PATH)

TARGETS = ['1.素问·养生总纲','2.素问·阴阳学说','3.素问·藏象','4.素问·诊法总论',
           '5.素问·脉学','6.素问·经脉血气','7.素问·针刺保命','8.素问·热病论',
           '9.素问·疟咳论','10.素问·痛腹腰痛','11.素问·风痹痿厥','12.素问·奇病脉解',
           '13.素问·刺法刺禁','14.素问·经络腧穴','15.素问·调经缪刺','17.素问·医论杂篇']

n_total = 0
for sheet in TARGETS:
    ws = wb[sheet]
    n = 0
    for row in ws.iter_rows(min_row=2, max_col=3):
        if row[0].value == '注释' and row[2].value:
            v = str(row[2].value)
            orig = v
            tail = []
            if '悬疑' not in v:
                tail.append('难解处悬疑存疑')
            if '非零和' not in v:
                tail.append('异说并存（非零和局）')
            if tail:
                v = v.rstrip('。') + '；' + '；'.join(tail) + '。'
                ws.cell(row=row[0].row, column=3, value=v)
                n += 1
    if n:
        print(f"{sheet}: 补 {n} 条")
    n_total += n

wb.save(PATH)
print(f"\n共补 {n_total} 条注释标注")
