# -*- coding: utf-8 -*-
"""runner: tempfile OS-safe 生成 hermes-verify- 脚本 → 运行 → 自动清理（ad-hoc）"""
import os, subprocess, sys, tempfile

BODY = r'''# -*- coding: utf-8 -*-
"""hermes-verify-hjnj-engines-v2.py — qhzy-黄帝内经 引擎补齐+重排 聚焦验证（ad-hoc）"""
import sys, re, openpyxl

PATH = r'C:\Users\DELL\Desktop\qhzy-黄帝内经(通读注释版).xlsx'
fails, passes = [], []

def check(name, cond, detail=""):
    (passes if cond else fails).append(f"{name}{(' | ' + detail) if detail and not cond else ''}")

wb = openpyxl.load_workbook(PATH, read_only=True)

# 1. 20 Sheet 顺序（对齐前5本模式）
EXPECT = ['0改写说明','0分布式体系','平台建设与依赖','平台支撑完整性','0历史',
          '0映射1','0映射2','0映射3','0封面','0目录',
          'ICD11统一命名','病证单元库','多智能体协同','兼容性思维流','可复用Skills',
          '1.素问·养生总纲','2.素问·阴阳学说','3.素问·藏象','4.素问·诊法总论','5.素问·脉学']
check("Sheet数=20", len(wb.sheetnames) == 20, str(len(wb.sheetnames)))
check("Sheet顺序规范", wb.sheetnames == EXPECT, str(wb.sheetnames))

# 2. 10 个引擎 Sheet 内容关键词
engines = {
    '0改写说明': ['v0.1-qhzy', '照抄原文', '非零和局', '邹纯朴', '翟双庆', '李梢', '31 章', 'tcmP'],
    '0分布式体系': ['华为云 114.115.211.254', 'GitHub', '192.168.1.12', '192.168.0.102', 'A800', 'T1-T4', 'node-coordinator'],
    '平台建设与依赖': ['概念向量表', 'icd11_mms.db', 'A800', '部署验证', '章节-平台映射', '依赖清单'],
    '平台支撑完整性': ['MB48.0', '8B11', 'MD81', 'DD91.2', 'ME84.2', '17 内经病证单元', 'molecular_targets'],
    '0历史': ['成书', '王冰', '太素', '史崧', '马莳', '张介宾', '人民卫生出版社'],
    'ICD11统一命名': ['BZ-HJ-01', 'MB48.0', '8B11', 'MD81', 'DD91.2', 'ME84.2', 'pending_who_api'],
    '病证单元库': ['BZ-HJ-01', '风证', '痹证', '痿证', '厥证', '咳', '疟', '消渴', '痈疽', '癫狂', '梦', '虚'],
    '多智能体协同': ['tcm-chief-editor', 'tcm-author', 'tcmreviewer', 'aireviewer', 'node-coordinator'],
    '兼容性思维流': ['第1局', '第7局', '非零和', '原文忠实', '王冰本', 'AI辅助'],
    '可复用Skills': ['tcm-huangdi-neijing-seed', 'tcm-classic-collation', 'tcm-concept-vector-rag',
                     'tcm-disease-unit-dsu', 'tcm-sage-decision-dataset', 'tcm-distributed-node-orchestration'],
}
for s, kws in engines.items():
    ws = wb[s]
    txt = "\n".join(str(c.value) for row in ws.iter_rows() for c in row if c.value)
    for k in kws:
        check(f"{s}含[{k}]", k in txt)

# 3. 正文 1-5 章未破坏
tot = {'原文': 0, '通读': 0, '注释': 0}
for s in ['1.素问·养生总纲','2.素问·阴阳学说','3.素问·藏象','4.素问·诊法总论','5.素问·脉学']:
    ws = wb[s]
    for row in ws.iter_rows(min_row=2, max_col=3):
        if row[0].value in tot:
            tot[row[0].value] += 1
check("正文原文160", tot['原文'] == 160, str(tot['原文']))
check("正文通读20", tot['通读'] == 20, str(tot['通读']))
check("正文注释31", tot['注释'] == 31, str(tot['注释']))

# 4. 0映射/0目录 未破坏
t1m = "\n".join(str(c.value) for row in wb['0映射1'].iter_rows() for c in row if c.value)
t2m = "\n".join(str(c.value) for row in wb['0映射2'].iter_rows() for c in row if c.value)
t3m = "\n".join(str(c.value) for row in wb['0映射3'].iter_rows() for c in row if c.value)
tt = "\n".join(str(c.value) for row in wb['0目录'].iter_rows() for c in row if c.value)
check("0映射1邹纯朴", '邹纯朴' in t1m)
check("0映射2翟双庆", '翟双庆' in t2m)
check("0映射3李梢", '李梢' in t3m)
check("0目录素问灵枢81篇", '素问81篇' in tt and '灵枢81篇' in tt and '痈疽' in tt)

wb.close()
print(f"PASS {len(passes)} | FAIL {len(fails)}")
for p in passes:
    print("  ✔", p)
for f in fails:
    print("  ✘", f)
sys.exit(1 if fails else 0)
'''

fd, tmp_path = tempfile.mkstemp(prefix='hermes-verify-hjnj-engines-v2-', suffix='.py', dir=tempfile.gettempdir())
with os.fdopen(fd, 'w', encoding='utf-8') as f:
    f.write(BODY)
print(f"[hermes-verify] 临时脚本: {tmp_path}")

PY = r'C:\Users\DELL\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe'
try:
    r = subprocess.run([PY, tmp_path], capture_output=True, text=True, encoding='utf-8', timeout=180)
    print(r.stdout)
    if r.stderr:
        print("STDERR:", r.stderr[-1200:])
    sys.exit(r.returncode)
finally:
    try:
        os.remove(tmp_path)
        print(f"[hermes-verify] 已清理: {tmp_path} 存在={os.path.exists(tmp_path)}")
    except OSError:
        pass
