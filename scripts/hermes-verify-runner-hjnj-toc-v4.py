# -*- coding: utf-8 -*-
"""
runner: tempfile.mkstemp 动态生成 hermes-verify- 前缀脚本 → 运行 → 自动清理（OS-safe, ad-hoc）
验证目标: qhzy-黄帝内经 0目录（素问81+灵枢81篇序, gen_hjnj_toc2.py 修复后）
"""
import os, subprocess, sys, tempfile

BODY = r'''# -*- coding: utf-8 -*-
"""hermes-verify-hjnj-toc-v4.py — 0目录 素问81+灵枢81篇序 聚焦验证（ad-hoc）"""
import sys, re, openpyxl

PATH = r'C:\Users\DELL\Desktop\qhzy-黄帝内经(通读注释版).xlsx'
fails, passes = [], []

def check(name, cond, detail=""):
    (passes if cond else fails).append(f"{name}{(' | ' + detail) if detail and not cond else ''}")

wb = openpyxl.load_workbook(PATH, read_only=True)
ws = wb['0目录']
lines = [str(row[0].value).strip() for row in ws.iter_rows() if row[0].value]

# 1. 头部结构
check("标题行", '《黄帝内经（通读注释版）》正文目录' in lines[0])
check("先素问后灵枢", '先《素问》81篇' in lines[1] and '后《灵枢》81篇' in lines[1])
check("四级目录标记", '【正文四级目录】' in lines)

# 2. 篇目 81×2 与顺序
sw, ls = [], []
for ln in lines:
    m = re.match(r'^(\d+)\.(\d+)\s+(.+?)（第(\d+)篇）$', ln)
    if m:
        ch, no, name = int(m.group(1)), int(m.group(4)), m.group(3)
        (sw if ch <= 17 else ls).append((no, name))
check("素问81篇", len(sw) == 81, f"实际{len(sw)}")
check("灵枢81篇", len(ls) == 81, f"实际{len(ls)}")
check("素问1-81序", [n for n, _ in sw] == list(range(1, 82)))
check("灵枢1-81序", [n for n, _ in ls] == list(range(1, 82)))
check("素问首末", sw[0][1] == '上古天真论' and sw[-1][1] == '解精微论')
check("灵枢首末", ls[0][1] == '九针十二原' and ls[-1][1] == '痈疽')

# 3. 31 章
ch_sw = [ln for ln in lines if re.match(r'^\d+\.\s+素问', ln)]
ch_ls = [ln for ln in lines if re.match(r'^\d+\.\s+灵枢', ln)]
check("素问17章", len(ch_sw) == 17, f"实际{len(ch_sw)}")
check("灵枢14章", len(ch_ls) == 14, f"实际{len(ch_ls)}")
nums = [int(re.match(r'^(\d+)\.', ln).group(1)) for ln in ch_sw + ch_ls]
check("章号1-31连续", nums == list(range(1, 32)), str(nums))

# 4. 四级统计
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
check("四级31/162/324/648", lv == {'章': 31, '节': 162, '小节': 324, '段落': 648}, str(lv))

# 5. 小节2 闭合（修复点）
sub2 = [ln for ln in lines if re.match(r'^\d+\.\d+\.2\s', ln)]
bad = [ln for ln in sub2 if not ln.endswith('）')]
check("小节2 162条全闭合", len(sub2) == 162 and not bad, f"未闭合{len(bad)}")
ls_i = next(i for i, ln in enumerate(sub2) if '经络针灸' in ln)
check("应用标签", '应用（养生康复）' in sub2[0] and '应用（经络针灸）' in sub2[ls_i])

# 6. 每篇4段落 + 附录
paras = [ln for ln in lines if re.match(r'^\d+\.\d+\.\d+\.\d+\s', ln)]
check("段落=648", len(paras) == 648, f"实际{len(paras)}")
apps = [ln for ln in lines if re.match(r'^[A-E]\.', ln)]
check("附录A-E", len(apps) == 5, str(apps))

# 7. 未破坏
t1 = "\n".join(str(c.value) for row in wb['0映射1'].iter_rows() for c in row if c.value)
t3 = "\n".join(str(c.value) for row in wb['0映射3'].iter_rows() for c in row if c.value)
check("0映射1", '邹纯朴' in t1 and '契合点' in t1)
check("0映射3", '李梢' in t3 and '网络靶标' in t3)
check("Sheet数=4", wb.sheetnames == ['0封面', '0映射1', '0映射3', '0目录'], str(wb.sheetnames))

wb.close()
print(f"\nPASS {len(passes)} | FAIL {len(fails)}")
for p in passes:
    print("  ✔", p)
for f in fails:
    print("  ✘", f)
sys.exit(1 if fails else 0)
'''

fd, tmp_path = tempfile.mkstemp(prefix='hermes-verify-hjnj-toc-v4-', suffix='.py', dir=tempfile.gettempdir())
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
