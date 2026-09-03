# -*- coding: utf-8 -*-
"""补查 ICD-11 编码: 不寐/消渴/头痛/郁证/肺痨（code_lookup + 更精确 title）"""
import sqlite3
from pathlib import Path

DB = Path(r'C:\Users\DELL\tcmP\data\icd11_mms.db')
conn = sqlite3.connect(str(DB))

QUERIES = [
    ('不寐', ['7A00', 'Insomnia']),
    ('消渴', ['5A10', 'Diabetes mellitus']),
    ('头痛', ['8A80', 'Headache']),
    ('郁证', ['6A70', 'Depressive']),
    ('肺痨', ['1B10', 'Tuberculosis']),
    ('胃脘痛', ['DA90', 'Epigastric pain']),
    ('汗证', ['MG46', 'Hyperhidrosis']),
    ('痹证', ['FA25', 'Arthritis']),
]
for cn, (code, title) in QUERIES:
    # 先精确编码
    r = conn.execute("SELECT code, title FROM entities WHERE code=?", (code,)).fetchone()
    if r:
        print(f'{cn}: {r[0]} {r[1][:44]}')
        continue
    # title 精确
    r = conn.execute("SELECT code, title FROM entities WHERE title=?", (title,)).fetchone()
    if r:
        print(f'{cn}: {r[0]} {r[1][:44]}')
        continue
    # 前缀
    r = conn.execute("SELECT code, title FROM entities WHERE title LIKE ? LIMIT 1",
                     (title + '%',)).fetchone()
    if r:
        print(f'{cn}: {r[0]} {r[1][:44]}')
    else:
        print(f'{cn}: 未找到（{title}）')
conn.close()
