# -*- coding: utf-8 -*-
"""runner: tempfile OS-safe 生成 hermes-verify- 脚本 → 运行 → 自动清理（ad-hoc）"""
import os, subprocess, sys, tempfile

BODY = r'''# -*- coding: utf-8 -*-
"""hermes-verify-hjnj-toc-final.py — qhzy-黄帝内经 0目录 v2（素问81+灵枢81篇序）聚焦验证（ad-hoc）"""
import sys, re, openpyxl

PATH = r'C:\Users\DELL\Desktop\qhzy-黄帝内经(通读注释版).xlsx'
fails, passes = [], []

def check(name, cond, detail=""):
    (passes if cond else fails).append(f"{name}{(' | ' + detail) if detail and not cond else ''}")

wb = openpyxl.load_workbook(PATH, read_only=True)
ws = wb['0目录']
lines = [str(row[0].value).strip() for row in ws.iter_rows() if row[0].value]

# 1. 结构头部
check("标题行", '《黄帝内经（通读注释版）》正文目录' in lines[0])
check("先素问后灵枢说明", '先《素问》81篇' in lines[1] and '后《灵枢》81篇' in lines[1])
check("四级目录标记", '【正文四级目录】' in lines)

# 2. 篇目提取与顺序（节级: "1.1 上古天真论（第1篇）"）
sw, ls = [], []
for ln in lines:
    m = re.match(r'^(\d+)\.(\d+)\s+(.+?)（第(\d+)篇）$', ln)
    if m:
        ch, no, name = int(m.group(1)), int(m.group(4)), m.group(3)
        (sw if ch <= 17 else ls).append((no, name))
check("素问81篇齐全", len(sw) == 81, f"实际{len(sw)}")
check("灵枢81篇齐全", len(ls) == 81, f"实际{len(ls)}")
check("素问1-81顺序", [n for n, _ in sw] == list(range(1, 82)))
check("灵枢1-81顺序", [n for n, _ in ls] == list(range(1, 82)))
check("素问首篇", sw[0][1] == '上古天真论' and sw[0][0] == 1)
check("素问末篇", sw[-1][1] == '解精微论' and sw[-1][0] == 81)
check("灵枢首篇", ls[0][1] == '九针十二原' and ls[0][0] == 1)
check("灵枢末篇", ls[-1][1] == '痈疽' and ls[-1][0] == 81)

# 3. 章节归并（31章, 素问17+灵枢14）
ch_sw = [ln for ln in lines if re.match(r'^\d+\.\s+素问', ln)]
ch_ls = [ln for ln in lines if re.match(r'^\d+\.\s+灵枢', ln)]
check("素问17章", len(ch_sw) == 17, f"实际{len(ch_sw)}")
check("灵枢14章", len(ch_ls) == 14, f"实际{len(ch_ls)}")
check("章号连续1-31", [int(re.match(r'^(\d+)\.', ln).group(1)) for ln in ch_sw + ch_ls] == list(range(1, 32)))

# 4. 四级编码统计
lv = {'章': 0, '节': 0, '小节': 0, '段落': 0}
for ln in lines:
    if re.match(r'^\d+\.\s+素问|^\d+\.\s+灵枢', ln):
        lv['章'] += 1
    elif re.match(r'^\d+\.\d+\.\d+\.\d+\s', ln):
        lv['段落'] += 1
    elif re.match(r'^\d+\.\d+\.\d+\s', ln):
        lv['小节'] += 1
    elif re.match(r'^\d+\.\d+\s', ln):
        lv['节'] += 1
check("章=31", lv['章'] == 31, str(lv))
check("节=162(81×2)", lv['节'] == 162, str(lv))
check("小节=324", lv['小节'] == 324, str(lv))
check("段落=648", lv['段落'] == 648, str(lv))

# 5. 小节2标题闭合检查
sub2 = [ln for ln in lines if re.match(r'^\d+\.\d+\.2\s', ln)]
bad_sub = [ln for ln in sub2 if not ln.endswith('）')]
check("小节2标题162条全闭合", len(sub2) == 162 and not bad_sub, f"未闭合{len(bad_sub)}")
check("素问应用标签", '应用（养生康复）' in sub2[0])
ls_idx = next(i for i, ln in enumerate(sub2) if '经络针灸' in ln)
check("灵枢应用标签", '应用（经络针灸）' in sub2[ls_idx])

# 6. 每篇4段落完整（每篇: 小节1×2段 + 小节2×2段）
paras = [ln for ln in lines if re.match(r'^\d+\.\d+\.\d+\.\d+\s', ln)]
check("段落数=162×4", len(paras) == 648, f"实际{len(paras)}")

# 7. 附录
app = [ln for ln in lines if ln.startswith('A.') or ln.startswith('B.') or ln.startswith('C.') or ln.startswith('D.') or ln.startswith('E.')]
check("附录A-E", len(app) == 5, str(app))

# 8. 0映射1/0映射3 未被破坏
ws1 = wb['0映射1']
t1 = "\n".join(str(c.value) for row in ws1.iter_rows() for c in row if c.value)
ws3 = wb['0映射3']
t3 = "\n".join(str(c.value) for row in ws3.iter_rows() for c in row if c.value)
check("0映射1完整", '邹纯朴' in t1 and '契合点' in t1)
check("0映射3完整", '李梢' in t3 and '网络靶标' in t3)

wb.close()
print(f"PASS {len(passes)} | FAIL {len(fails)}")
for p in passes:
    print("  ✔", p)
for f in fails:
    print("  ✘", f)
sys.exit(1 if fails else 0)
'''

fd, tmp_path = tempfile.mkstemp(prefix='hermes-verify-hjnj-toc-final-', suffix='.py', dir=tempfile.gettempdir())
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
