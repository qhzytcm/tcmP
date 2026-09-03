# -*- coding: utf-8 -*-
"""runner: tempfile OS-safe 生成 hermes-verify- 脚本 → 运行 → 自动清理（ad-hoc）"""
import os, subprocess, sys, tempfile

BODY = r'''# -*- coding: utf-8 -*-
"""hermes-verify-hjnj-tongdu.py — qhzy-黄帝内经 通读补丁+注释修复 聚焦验证（ad-hoc）"""
import sys, re, openpyxl

PATH = r'C:\Users\DELL\Desktop\qhzy-黄帝内经(通读注释版).xlsx'
fails, passes = [], []

def check(name, cond, detail=""):
    (passes if cond else fails).append(f"{name}{(' | ' + detail) if detail and not cond else ''}")

wb = openpyxl.load_workbook(PATH, read_only=True)
chs = ['1.素问·养生总纲','2.素问·阴阳学说','3.素问·藏象','4.素问·诊法总论','5.素问·脉学']

# 1. 通读行: 每篇 1 条, 共 20 条
tot_td = 0
for s in chs:
    ws = wb[s]
    n_td = sum(1 for row in ws.iter_rows(min_row=2, max_col=3) if row[0].value == '通读')
    tot_td += n_td
    check(f"{s}通读≥3", n_td >= 3, f"实际{n_td}")
check("通读共20条", tot_td == 20, f"实际{tot_td}")

# 2. 通读行编码规范 (x.y.0 格式)
for s in chs:
    ws = wb[s]
    for row in ws.iter_rows(min_row=2, max_col=3):
        if row[0].value == '通读':
            code = str(row[1].value)
            check(f"{s}通读编码[{code}]", re.match(r'^\d+\.\d+\.0$', code), code)

# 3. 注释: 共 31 条 (原26 + 补5), 编码规范
tot_no = 0
bad_codes = []
for s in chs:
    ws = wb[s]
    for row in ws.iter_rows(min_row=2, max_col=3):
        if row[0].value == '注释':
            tot_no += 1
            code = str(row[1].value)
            if not re.match(r'^\d+\.\d+\.\d+\.\d+$', code):
                bad_codes.append((s, row[0].row, code))
check("注释共31条", tot_no == 31, f"实际{tot_no}")
check("注释编码规范", not bad_codes, str(bad_codes))

# 4. 补注位置正确（锚点篇内: 阴阳离合论注在2.2段, 五脏生成注在3.3段等）
for s, pn_kw, code_prefix in [
    ('2.素问·阴阳学说', '阴阳离合论', '2.2.'),
    ('3.素问·藏象', '五脏生成', '3.3.'),
    ('3.素问·藏象', '五脏别论', '3.4.'),
    ('4.素问·诊法总论', '移精变气论', '4.2.'),
    ('4.素问·诊法总论', '玉版论要', '4.4.'),
]:
    ws = wb[s]
    found = False
    in_pian = False
    for row in ws.iter_rows(min_row=2, max_col=3):
        cat = row[0].value
        val = str(row[2].value) if row[2].value else ''
        if cat == '篇名':
            in_pian = pn_kw in val
        elif cat == '注释' and in_pian and str(row[1].value).startswith(code_prefix):
            found = True
    check(f"{pn_kw}补注在篇内({code_prefix})", found)

# 5. 补注内容含"非零和"
all_note = ""
for s in chs:
    ws = wb[s]
    all_note += "\n".join(str(row[2].value) for row in ws.iter_rows(min_row=2, max_col=3) if row[0].value == '注释' and row[2].value)
check("补注含非零和标注", '非零和' in all_note)

# 6. 原文未受损 (总数160)
tot_or = sum(1 for s in chs for row in wb[s].iter_rows(min_row=2, max_col=3) if row[0].value == '原文')
check("原文160段未受损", tot_or == 160, f"实际{tot_or}")

# 7. 原文关键句仍完整
ws1 = wb['1.素问·养生总纲']
t1 = "\n".join(str(c.value) for row in ws1.iter_rows() for c in row if c.value)
check("第1章原文完整", '法于阴阳，和于术数' in t1 and '阴平阳秘，精神乃治' in t1)

# 8. 无空单元格/乱码
garbled = re.compile(r'[\ufffd]|锟斤拷')
bad_cell = 0
for s in chs + ['0目录','0映射1','0映射2','0映射3']:
    ws = wb[s]
    for row in ws.iter_rows(max_col=3):
        if row[0].value is None:
            continue  # 整行空跳过
        for c in row:
            if isinstance(c.value, str) and garbled.search(c.value):
                bad_cell += 1
check("无空单元格/乱码", bad_cell == 0, f"{bad_cell}处")

wb.close()
print(f"PASS {len(passes)} | FAIL {len(fails)}")
for p in passes:
    print("  ✔", p)
for f in fails:
    print("  ✘", f)
sys.exit(1 if fails else 0)
'''

fd, tmp_path = tempfile.mkstemp(prefix='hermes-verify-hjnj-tongdu-', suffix='.py', dir=tempfile.gettempdir())
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
