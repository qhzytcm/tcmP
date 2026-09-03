# -*- coding: utf-8 -*-
"""全书病证术语 × ICD-11 精确对照（优先 title 精确匹配, 标注 TM1 传统医学章节）
用 hermes venv python 运行: venv\Scripts\python.exe cmrl_icd11_terms2.py
"""
import re
import sqlite3
from pathlib import Path

DRAFTS = Path(r'C:\Users\DELL\textbook-project\drafts\cmrl')
DB = Path(r'C:\Users\DELL\tcmP\data\icd11_mms.db')

# 病证 -> 候选 ICD-11 英文（精确 title 优先）
TERMS = [
    ('不寐', 42, ['Insomnia', 'insomnia']),
    ('心悸', 9, ['Palpitations', 'palpitation']),
    ('咳嗽', 6, ['Cough']),
    ('感冒', 15, ['Common cold disorder']),
    ('心脾两虚', 10, []),          # 证候名, ICD-11 无直接编码, 记辨证参考
    ('阴虚', 4, []), ('阳虚', 5, []), ('气虚', 1, []), ('血虚', 1, []),
    ('痰湿', 1, []), ('瘀血', 1, []),
    # 以下为书中示例/习题涉及（目录级）
    ('消渴', 0, ['Diabetes mellitus']),
    ('胸痹', 0, ['Angina pectoris']),
    ('头痛', 0, ['Headache']),
    ('眩晕', 0, ['Vertigo']),
    ('中风', 0, ['Stroke']),
    ('痹证', 0, ['Arthralgia']),
    ('胃脘痛', 0, ['Epigastric pain']),
    ('泄泻', 0, ['Diarrhoea']),
    ('便秘', 0, ['Constipation']),
    ('郁证', 0, ['Depressive disorders']),
    ('水肿', 0, ['Oedema']),
    ('黄疸', 0, ['Jaundice']),
    ('汗证', 0, ['Sweating']),
    ('虚劳', 0, ['Fatigue']),
    ('喘证', 0, ['Asthma']),
    ('肺痈', 0, ['Lung abscess']),
    ('肺痨', 0, ['Tuberculosis']),
]

conn = sqlite3.connect(str(DB))
print(f'{"中医病证":<10}{"现":<4}{"ICD-11编码":<14}{"章节":<6}{"ICD-11 英文名/说明"}')
print('-' * 78)
for cn, cnt, cands in TERMS:
    best = None
    for en in cands:
        # 1) 精确 title
        r = conn.execute(
            "SELECT code, title, fully_specified_name, class_kind FROM entities "
            "WHERE title=? LIMIT 1", (en,)).fetchone()
        if r:
            best = r
            break
        # 2) 前缀
        r = conn.execute(
            "SELECT code, title, fully_specified_name, class_kind FROM entities "
            "WHERE title LIKE ? LIMIT 1", (en + '%',)).fetchone()
        if r:
            best = r
            break
    if best:
        code, title, fsn, kind = best
        ch = 'TM1' if code and 'SA00' <= code <= 'SF57' else (code[:1] if code else '-')
        name = title or (fsn or '')[:40]
        print(f'{cn:<10}{cnt:<4}{code:<14}{ch:<6}{name[:44]}')
    else:
        note = '证候名（八纲/脏腑辨证）— ICD-11 无单病编码, 按辨证参考' if not cands else '-'
        print(f'{cn:<10}{cnt:<4}{"-":<14}{"-":<6}{note}')
conn.close()
