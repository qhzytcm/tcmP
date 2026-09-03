# -*- coding: utf-8 -*-
"""runner: tempfile OS-safe 动态生成 hermes-verify- 脚本 → 运行 → 自动清理（ad-hoc）"""
import os, subprocess, sys, tempfile

BODY = r'''# -*- coding: utf-8 -*-
"""hermes-verify-hjnj-ch1-5-v2.py — qhzy-黄帝内经 1-5章正文（原文+注释）ad-hoc 聚焦验证"""
import sys, re, openpyxl

PATH = r'C:\Users\DELL\Desktop\qhzy-黄帝内经(通读注释版).xlsx'
fails, passes = [], []

def check(name, cond, detail=""):
    (passes if cond else fails).append(f"{name}{(' | ' + detail) if detail and not cond else ''}")

wb = openpyxl.load_workbook(PATH, read_only=True)

# 1. 5 个正文章 Sheet 连续
ch = [s for s in wb.sheetnames if re.match(r'^\d+\.', s)]
check("正文章=5", len(ch) == 5, str(ch))
check("章1-5连续", ch == ['1.素问·养生总纲','2.素问·阴阳学说','3.素问·藏象','4.素问·诊法总论','5.素问·脉学'], str(ch))

# 2. 各章篇名/原文/注释结构
expected = {
    '1.素问·养生总纲': (4, ['上古天真论','四气调神大论','生气通天论','金匮真言论']),
    '2.素问·阴阳学说': (3, ['阴阳应象大论','阴阳离合论','阴阳别论']),
    '3.素问·藏象': (4, ['灵兰秘典论','六节藏象论','五脏生成','五脏别论']),
    '4.素问·诊法总论': (5, ['异法方宜论','移精变气论','汤液醪醴论','玉版论要','诊要经终论']),
    '5.素问·脉学': (4, ['脉要精微论','平人气象论','玉机真脏论','三部九候论']),
}
for s, (n_pian, pnames) in expected.items():
    ws = wb[s]
    cats = {'篇名': 0, '原文': 0, '注释': 0}
    got = []
    for row in ws.iter_rows(min_row=2, max_col=3):
        c = row[0].value
        if c in cats:
            cats[c] += 1
        if c == '篇名' and row[2].value:
            got.append(str(row[2].value))
    check(f"{s}篇名={n_pian}", cats['篇名'] == n_pian, f"实际{cats['篇名']}")
    check(f"{s}原文≥15", cats['原文'] >= 15, f"实际{cats['原文']}")
    check(f"{s}注释≥4", cats['注释'] >= 4, f"实际{cats['注释']}")
    for pn in pnames:
        check(f"{s}篇[{pn}]", any(pn in g for g in got))

# 3. 原文非创作抽查（通行本原句）
key = {
    '1.素问·养生总纲': ['法于阴阳，和于术数', '恬惔虚无，真气从之', '春夏养阳，秋冬养阴', '阴平阳秘，精神乃治'],
    '2.素问·阴阳学说': ['治病必求于本', '壮火之气衰，少火之气壮', '太阳为开，阳明为阖', '阴搏阳别，谓之有子'],
    '3.素问·藏象': ['心者，君主之官也', '凡十一藏，取决于胆也', '人卧血归于肝', '藏精气而不写也'],
    '4.素问·诊法总论': ['地势使然也', '得神者昌，失神者亡', '病为本，工为标', '开鬼门，洁净府', '神转不回', '十二经脉之终'],
    '5.素问·脉学': ['诊法常以平旦', '夫脉者，血之府也', '胃者，平人之常气也', '人以水谷为本', '三部九候', '真藏脉见者死'],
}
for s, kws in key.items():
    ws = wb[s]
    txt = "\n".join(str(c.value) for row in ws.iter_rows() for c in row if c.value)
    for ks in kws:
        check(f"{s}原文[{ks[:10]}]", ks in txt)

# 4. 注释非零和局
for s in ch:
    ws = wb[s]
    zt = "\n".join(str(row[2].value) for row in ws.iter_rows(min_row=2, max_col=3) if row[0].value == '注释' and row[2].value)
    check(f"{s}注释非零和", '非零和' in zt or ('并存' in zt and '注' in zt))

# 5. 0目录 未破坏
tt = "\n".join(str(c.value) for row in wb['0目录'].iter_rows() for c in row if c.value)
check("0目录素问灵枢完整", '上古天真论' in tt and '三部九候论' in tt and '痈疽' in tt and '解精微论' in tt)

wb.close()
print(f"PASS {len(passes)} | FAIL {len(fails)}")
for p in passes:
    print("  ✔", p)
for f in fails:
    print("  ✘", f)
sys.exit(1 if fails else 0)
'''

fd, tmp_path = tempfile.mkstemp(prefix='hermes-verify-hjnj-ch1-5-v2-', suffix='.py', dir=tempfile.gettempdir())
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
