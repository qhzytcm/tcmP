# -*- coding: utf-8 -*-
"""全书中医药病证术语 × ICD-11 标准对照
1) 从 10 章正文提取病证名出现次数
2) 用 icd11_mms.db 查 ICD-11 标准编码+英文名（search_en / code_lookup）
"""
import re
import sqlite3
import sys
from pathlib import Path

# 测试 sqlite 可用性（Anaconda 可能段错误 -> 需 hermes venv python）
try:
    c = sqlite3.connect(':memory:')
    c.close()
    PY_OK = True
except Exception:
    PY_OK = False
print(f'sqlite OK: {PY_OK} (python={sys.executable})')

DRAFTS = Path(r'C:\Users\DELL\textbook-project\drafts\cmrl')
DB = Path(r'C:\Users\DELL\tcmP\data\icd11_mms.db')

# 中医病证候选清单（含俗名/中医病名）
TERMS = [
    ('不寐', ['不寐', '失眠']),
    ('消渴', ['消渴']),
    ('胸痹', ['胸痹']),
    ('心悸', ['心悸']),
    ('咳嗽', ['咳嗽']),
    ('感冒', ['感冒', '风寒表实', '风热表证']),
    ('头痛', ['头痛']),
    ('眩晕', ['眩晕']),
    ('中风', ['中风']),
    ('痹证', ['痹证', '痹症']),
    ('胃脘痛', ['胃脘痛', '胃痛']),
    ('泄泻', ['泄泻', '腹泻']),
    ('便秘', ['便秘']),
    ('郁证', ['郁证']),
    ('水肿', ['水肿']),
    ('黄疸', ['黄疸']),
    ('血证', ['血证']),
    ('汗证', ['汗证', '自汗', '盗汗']),
    ('虚劳', ['虚劳']),
    ('喘证', ['喘证', '哮喘']),
    ('肺痈', ['肺痈']),
    ('肺痨', ['肺痨']),
    ('心脾两虚', ['心脾两虚']),
    ('肝气郁结', ['肝气郁结']),
    ('痰湿', ['痰湿', '湿痰']),
    ('气虚', ['气虚', '气血不足']),
    ('血虚', ['血虚']),
    ('阴虚', ['阴虚']),
    ('阳虚', ['阳虚']),
    ('瘀血', ['瘀血', '血瘀']),
]

# 1) 正文出现次数
text_all = ''
for ch in range(1, 11):
    for f in (DRAFTS / f'ch{ch:02d}').glob('0*-1.*.md'):
        text_all += f.read_text(encoding='utf-8')

print(f'\n全书正文长度: {len(text_all)} 字符')
print(f'\n{"中医病证":<10}{"出现":<6}{"ICD-11编码":<12}{"ICD-11英文名(截断)"}')
print('-' * 70)

conn = sqlite3.connect(str(DB))
for cn, keys in TERMS:
    cnt = sum(len(re.findall(k, text_all)) for k in keys)
    # ICD-11 查询: 英文名搜索
    en_terms = {
        '失眠': 'insomnia', '消渴': 'diabetes', '胸痹': 'angina', '心悸': 'palpitation',
        '咳嗽': 'cough', '感冒': 'common cold', '头痛': 'headache', '眩晕': 'vertigo',
        '中风': 'stroke', '痹证': 'arthralgia', '胃脘痛': 'epigastric', '泄泻': 'diarrhoea',
        '便秘': 'constipation', '郁证': 'depressive', '水肿': 'oedema', '黄疸': 'jaundice',
        '血证': 'haemorrhage', '汗证': 'sweating', '虚劳': 'fatigue', '喘证': 'asthma',
        '肺痈': 'lung abscess', '肺痨': 'tuberculosis', '心脾两虚': None,
        '肝气郁结': None, '痰湿': None, '气虚': None, '血虚': None,
        '阴虚': None, '阳虚': None, '瘀血': None,
    }
    en = en_terms.get(cn)
    row = None
    if en:
        r = conn.execute(
            "SELECT code, title, fully_specified_name FROM entities "
            "WHERE title LIKE ? OR fully_specified_name LIKE ? OR code=? LIMIT 1",
            (f'%{en}%', f'%{en}%', en.upper())).fetchone()
        if r:
            row = r
    code = row[0] if row else '-'
    en_name = (row[1] if row else '-')[:34] if row else '-'
    print(f'{cn:<10}{cnt:<6}{code:<12}{en_name}')
conn.close()
