# -*- coding: utf-8 -*-
"""runner: tempfile OS-safe 动态生成 hermes-verify- 脚本 → 运行 → 自动清理（ad-hoc）"""
import os, subprocess, sys, tempfile

BODY = r'''# -*- coding: utf-8 -*-
"""hermes-verify-hjnj-rebuilt.py — qhzy-黄帝内经 重建修复后 1-14章 聚焦验证（ad-hoc）"""
import sys, re, openpyxl

PATH = r'C:\Users\DELL\Desktop\qhzy-黄帝内经(通读注释版).xlsx'
fails, passes = [], []

def check(name, cond, detail=""):
    (passes if cond else fails).append(f"{name}{(' | ' + detail) if detail and not cond else ''}")

wb = openpyxl.load_workbook(PATH, read_only=True)

# 1. 结构
EXPECT_HEAD = ['0改写说明','0分布式体系','平台建设与依赖','平台支撑完整性','0历史',
               '0映射1','0映射2','0映射3','0封面','0目录',
               'ICD11统一命名','病证单元库','多智能体协同','兼容性思维流','可复用Skills']
ch = [s for s in wb.sheetnames if re.match(r'^\d+\.', s)]
check("Sheet数=29", len(wb.sheetnames) == 29, str(len(wb.sheetnames)))
check("0系列+引擎", wb.sheetnames[:15] == EXPECT_HEAD, str(wb.sheetnames[:15]))
check("正文章14", len(ch) == 14, str(ch))

# 2. 无截断
suspects = []
for s in ch:
    ws = wb[s]
    for row in ws.iter_rows(min_row=2, max_col=3):
        v = row[2].value
        if v and isinstance(v, str) and len(v) > 10:
            if not re.search(r'[。；：！？」』）】]$', v) and re.search(r'[以之而于与为者]$', v.strip()):
                suspects.append((s, row[0].row, len(v)))
check("无截断", not suspects, f"{len(suspects)}处")

# 3. 总数
tot = {'原文': 0, '通读': 0, '注释': 0}
pian = 0
for s in ch:
    ws = wb[s]
    for row in ws.iter_rows(min_row=2, max_col=3):
        c = row[0].value
        if c == '篇名': pian += 1
        elif c in tot and row[2].value: tot[c] += 1
check("篇目61", pian == 61, f"实际{pian}")
check("原文434", tot['原文'] == 434, str(tot['原文']))
check("通读61", tot['通读'] == 61, str(tot['通读']))
check("注释71", tot['注释'] == 71, str(tot['注释']))

# 4. 截断修复点
key_fixes = {
    '1.素问·养生总纲': ['因于湿，首如裹', '阴之所生，本在五味', '其应四时，上为岁星'],
    '2.素问·阴阳学说': ['西方生燥，燥生金', '能知七损八益', '二阳之病发心脾'],
    '3.素问·藏象': ['色味当五藏', '凡相五色之奇脉'],
    '4.素问·诊法总论': ['往古人居禽兽之间', '搏脉痹躄'],
    '5.素问·脉学': ['四变之动，脉与之上下', '以春应中规'],
    '7.素问·针刺保命': ['手动若务，针耀而匀', '伏如横弩，起如发机', '天温日明'],
    '9.素问·疟咳论': ['其渴者，热盛也', '不渴者，热未盛也', '肺疟者'],
    '11.素问·风痹痿厥': ['其风气胜者为行痹', '饮食自倍'],
    '13.素问·刺法刺禁': ['刺骨无伤筋者，针至筋而去', '所谓刺皮无伤肉者'],
    '14.素问·经络腧穴': ['气穴三百六十五，以应一岁', '鼠瘘寒热', '岐伯稽首再拜对曰'],
}
for s, kws in key_fixes.items():
    ws = wb[s]
    txt = "\n".join(str(c.value) for row in ws.iter_rows() for c in row if c.value)
    for ks in kws:
        check(f"{s}[{ks[:10]}]", ks in txt)

# 5. 补注篇内
for s, pn_kw in [
    ('2.素问·阴阳学说', '阴阳离合论'), ('3.素问·藏象', '五脏生成'),
    ('3.素问·藏象', '五脏别论'), ('4.素问·诊法总论', '移精变气论'),
    ('4.素问·诊法总论', '玉版论要')]:
    ws = wb[s]
    found, in_pian = False, False
    for row in ws.iter_rows(min_row=2, max_col=3):
        cat = row[0].value
        val = str(row[2].value) if row[2].value else ''
        if cat == '篇名':
            in_pian = pn_kw in val
        elif cat == '注释' and in_pian and '异说并存' in val:
            found = True
    check(f"{pn_kw}补注篇内", found)

wb.close()
print(f"PASS {len(passes)} | FAIL {len(fails)}")
for p in passes:
    print("  ✔", p)
for f in fails:
    print("  ✘", f)
sys.exit(1 if fails else 0)
'''

fd, tmp_path = tempfile.mkstemp(prefix='hermes-verify-hjnj-rebuilt-', suffix='.py', dir=tempfile.gettempdir())
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
