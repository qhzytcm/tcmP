# -*- coding: utf-8 -*-
"""runner-fresh: tempfile 动态生成 hermes-verify- 脚本 → 运行 → 自动清理（ad-hoc, OS-safe）"""
import os, subprocess, sys, tempfile

BODY = r'''# -*- coding: utf-8 -*-
"""hermes-verify-hjnj-map2-v2.py — qhzy-黄帝内经 0映射2（翟双庆, 重排后）ad-hoc 聚焦验证"""
import sys, re, openpyxl

PATH = r'C:\Users\DELL\Desktop\qhzy-黄帝内经(通读注释版).xlsx'
fails, passes = [], []

def check(name, cond, detail=""):
    (passes if cond else fails).append(f"{name}{(' | ' + detail) if detail and not cond else ''}")

wb = openpyxl.load_workbook(PATH, read_only=True)

# 1. Sheet 顺序（重排后规范序列）
EXPECT = ['0封面', '0映射1', '0映射2', '0映射3', '0目录']
check("Sheet顺序规范", wb.sheetnames == EXPECT, str(wb.sheetnames))

# 2. 0映射2 内容
ws = wb['0映射2']
txt = "\n".join(str(c.value) for row in ws.iter_rows() for c in row if c.value)
for kw in ['1. 身份速读卡', '2. 学术背景时间线', '3. 专业成果', '5. 审稿人角色定义',
           '6. 与 TCM-Agents 教材的契合点', '7. 待核实清单', '附录 A. 数据源指纹', '【qhzy 工作流增强']:
    check(f"0映射2含[{kw}]", kw in txt)
for kw in ['翟双庆', '北京中医药大学', '博士生导师', '副校长', '百家讲坛', '内经学', '教改实验班',
           '王冰本', '太素', 'review_criteria', 'refusal_rules', '李梢', '[待核实]', '法律与伦理声明']:
    check(f"0映射2含[{kw}]", kw in txt)

# 3. 其他 Sheet 未破坏
t1 = "\n".join(str(c.value) for row in wb['0映射1'].iter_rows() for c in row if c.value)
t3 = "\n".join(str(c.value) for row in wb['0映射3'].iter_rows() for c in row if c.value)
tt = "\n".join(str(c.value) for row in wb['0目录'].iter_rows() for c in row if c.value)
check("0映射1完整", '邹纯朴' in t1 and '契合点' in t1)
check("0映射3完整", '李梢' in t3 and '网络靶标' in t3)
check("0目录完整", '素问81篇' in tt and '灵枢81篇' in tt and '解精微论' in tt)

# 4. 0目录 素问/灵枢 81 篇仍完整
sw, ls = [], []
for ln in [str(row[0].value).strip() for row in wb['0目录'].iter_rows() if row[0].value]:
    m = re.match(r'^(\d+)\.(\d+)\s+(.+?)（第(\d+)篇）$', ln)
    if m:
        ch, no = int(m.group(1)), int(m.group(4))
        (sw if ch <= 17 else ls).append(no)
check("0目录素问81篇", len(sw) == 81 and sw == list(range(1, 82)))
check("0目录灵枢81篇", len(ls) == 81 and ls == list(range(1, 82)))

wb.close()
print(f"PASS {len(passes)} | FAIL {len(fails)}")
for p in passes:
    print("  ✔", p)
for f in fails:
    print("  ✘", f)
sys.exit(1 if fails else 0)
'''

fd, tmp_path = tempfile.mkstemp(prefix='hermes-verify-hjnj-map2-v2-', suffix='.py', dir=tempfile.gettempdir())
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
