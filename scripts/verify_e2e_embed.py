# -*- coding: utf-8 -*-
"""端到端验证: 教材 BZU(11列) → 平台 tcm_embed.build_document 兼容性"""
import sys, openpyxl, json
sys.path.insert(0, r'C:\Users\DELL\tcmP\scripts')
from tcm_embed import build_document

# 从教材 BZU 构造 DSU dict
wb = openpyxl.load_workbook(r'C:\Users\DELL\Desktop\qhzy-中医基础理论.xlsx', read_only=True)
ws = wb['病证单元库']
ok = 0
fail = []
for row in ws.iter_rows(min_row=4, max_col=11):
    cells = ['' if c.value is None else str(c.value).strip() for c in row]
    if not cells[0].startswith('BZ-'):
        continue
    code, disease, syndrome, jibing, symptoms, treat, formula, meds, zf, six, tp = cells[:11]
    # 病名/ICD码拆分
    m = disease.split(' ')
    dname, icd = m[0], (m[1] if len(m) > 1 else '')
    dsu = {
        'id': code.replace('BZ-', 'DSU-').replace('-', '-'),
        'disease_side': {
            'disease_name': dname,
            'icd_code': icd,
            'category': '',
            'molecular_targets': [],
        },
        'syndrome_side': {
            'syndrome_name': syndrome.split(' ')[0],
            'pattern_type': syndrome.split(' ')[0],
            'zangfu': zf,
            'six_channels': six,
            'key_symptoms': [s for s in symptoms.replace('、', ',').split(',') if s],
        },
        'clinical': {
            'recommended_formula': formula,
        },
    }
    try:
        doc = build_document(dsu)
        if doc['text'] and doc['dsu_id']:
            ok += 1
        else:
            fail.append(code)
    except Exception as e:
        fail.append(f"{code}: {e}")
wb.close()
print(f"build_document 兼容: {ok}/32 成功")
if fail:
    print("失败:", fail[:5])
else:
    print("✅ 全部 BZU 可被平台 Embedding 引擎消费")

# 展示一条完整 Document 样例
wb2 = openpyxl.load_workbook(r'C:\Users\DELL\Desktop\qhzy-中医基础理论.xlsx', read_only=True)
ws2 = wb2['病证单元库']
for row in ws2.iter_rows(min_row=4, max_col=11):
    cells = ['' if c.value is None else str(c.value).strip() for c in row]
    if cells[0] == 'BZ-B21-Z04':
        m = cells[1].split(' ')
        dsu = {
            'id': 'DSU-90001',
            'disease_side': {'disease_name': m[0], 'icd_code': m[1], 'category': '循环系统疾病', 'molecular_targets': []},
            'syndrome_side': {'syndrome_name': cells[2].split(' ')[0], 'pattern_type': cells[2].split(' ')[0],
                              'zangfu': cells[8], 'six_channels': cells[9],
                              'key_symptoms': [s for s in cells[4].replace('、', ',').split(',') if s]},
            'clinical': {'recommended_formula': cells[6]},
        }
        doc = build_document(dsu)
        print("\n样例 BZ-B21-Z04 → Document:\n", doc['text'])
        break
wb2.close()
