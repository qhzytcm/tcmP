# -*- coding: utf-8 -*-
"""runner: tempfile OS-safe 动态生成 hermes-verify- 脚本 → 运行 → 自动清理（ad-hoc）"""
import os, subprocess, sys, tempfile

BODY = r'''# -*- coding: utf-8 -*-
"""hermes-verify-hjnj-ch6-11.py — qhzy-黄帝内经 6-11章（素问21-45篇）聚焦验证（ad-hoc）"""
import sys, re, json, openpyxl

PATH = r'C:\Users\DELL\Desktop\qhzy-黄帝内经(通读注释版).xlsx'
fails, passes = [], []

def check(name, cond, detail=""):
    (passes if cond else fails).append(f"{name}{(' | ' + detail) if detail and not cond else ''}")

wb = openpyxl.load_workbook(PATH, read_only=True)

# 1. 正文章 11 个 + 顺序
ch = [s for s in wb.sheetnames if re.match(r'^\d+\.', s)]
check("正文章=11", len(ch) == 11, str(ch))
check("章1-11连续", ch == [f'{i}.素问·{t}' for i, t in [
    (1,'养生总纲'),(2,'阴阳学说'),(3,'藏象'),(4,'诊法总论'),(5,'脉学'),(6,'经脉血气'),
    (7,'针刺保命'),(8,'热病论'),(9,'疟咳论'),(10,'痛腹腰痛'),(11,'风痹痿厥')]], str(ch))

# 2. 新增 6-11 章: 篇名/原文/通读/注释
expected = {
    '6.素问·经脉血气': (4, ['经脉别论','脏气法时论','宣明五气','血气形志']),
    '7.素问·针刺保命': (6, ['宝命全形论','八正神明论','离合真邪论','通评虚实论','太阴阳明论','阳明脉解']),
    '8.素问·热病论': (4, ['热论','刺热','评热病论','逆调论']),
    '9.素问·疟咳论': (4, ['疟论','刺疟','气厥论','咳论']),
    '10.素问·痛腹腰痛': (3, ['举痛论','腹中论','刺腰痛']),
    '11.素问·风痹痿厥': (4, ['风论','痹论','痿论','厥论']),
}
for s, (n_pian, pnames) in expected.items():
    ws = wb[s]
    cats = {'篇名': 0, '原文': 0, '通读': 0, '注释': 0}
    got = []
    for row in ws.iter_rows(min_row=2, max_col=3):
        c = row[0].value
        if c in cats:
            cats[c] += 1
        if c == '篇名' and row[2].value:
            got.append(str(row[2].value))
    check(f"{s}篇名={n_pian}", cats['篇名'] == n_pian, f"实际{cats['篇名']}")
    check(f"{s}原文≥15", cats['原文'] >= 15, f"实际{cats['原文']}")
    check(f"{s}通读={n_pian}", cats['通读'] == n_pian, f"实际{cats['通读']}")
    check(f"{s}注释≥3", cats['注释'] >= 3, f"实际{cats['注释']}")
    for pn in pnames:
        check(f"{s}篇[{pn}]", any(pn in g for g in got))

# 3. 原文非创作抽查（6-11章关键原句）
key = {
    '6.素问·经脉血气': ['饮入于胃，游溢精气', '肺朝百脉', '肝苦急，急食甘以缓之', '五谷为养，五果为助',
                         '酸入肝，辛入肺', '心藏神，肺藏魄', '久视伤血', '太阳常多血少气', '形乐志苦'],
    '7.素问·针刺保命': ['天覆地载，万物悉备，莫贵于人', '凡刺之真，必先治神', '法天则地，合以天光',
                         '邪气盛则实，精气夺则虚', '为胃行其津液', '四支皆禀气于胃', '阳盛则四支实',
                         '写必用方', '补必用员'],
    '8.素问·热病论': ['今夫热病者，皆伤寒之类也', '伤寒一日，巨阳受之', '其未满三日者，可汗而已',
                       '病热少愈，食肉则复', '肝热病者，小便先黄', '邪之所凑，其气必虚',
                       '胃不和则卧不安'],
    '9.素问·疟咳论': ['夫痎疟皆生于风', '阴阳上下交争', '夏伤于暑，秋必病疟', '方其盛时，必毁',
                       '足太阳之疟', '五藏六府皆令人咳，非独肺也', '聚于胃，关于肺'],
    '10.素问·痛腹腰痛': ['经脉流行不止，环周不休', '寒气入经而稽迟', '百病生于气也', '怒则气上，喜则气缓',
                          '名为鼓胀', '病名血枯', '四乌鲗骨一藘茹', '左取右，右取左'],
    '11.素问·风痹痿厥': ['风者，百病之长也', '风寒湿三气杂至，合而为痹也', '其风气胜者为行痹',
                          '肺热叶焦', '治痿者独取阳明', '阳气衰于下，则为寒厥', '阴气衰于下，则为热厥',
                          '暴不知人'],
}
for s, kws in key.items():
    ws = wb[s]
    txt = "\n".join(str(c.value) for row in ws.iter_rows() for c in row if c.value)
    for ks in kws:
        check(f"{s}原文[{ks[:10]}]", ks in txt)

# 4. 注释非零和（6-11章）
for s in ['6.素问·经脉血气','7.素问·针刺保命','8.素问·热病论','9.素问·疟咳论','10.素问·痛腹腰痛','11.素问·风痹痿厥']:
    ws = wb[s]
    zt = "\n".join(str(row[2].value) for row in ws.iter_rows(min_row=2, max_col=3) if row[0].value == '注释' and row[2].value)
    check(f"{s}注释非零和", '非零和' in zt and '并存' in zt)

# 5. 总统计（修正阈值: 原文340段/通读45/注释56）
tot = {'原文': 0, '通读': 0, '注释': 0}
pian = 0
for s in ch:
    ws = wb[s]
    for row in ws.iter_rows(min_row=2, max_col=3):
        c = row[0].value
        if c == '篇名': pian += 1
        elif c in tot and row[2].value: tot[c] += 1
check("篇目45(素问1-45)", pian == 45, f"实际{pian}")
check("原文340", tot['原文'] == 340, str(tot['原文']))
check("通读45", tot['通读'] == 45, str(tot['通读']))
check("注释56", tot['注释'] == 56, str(tot['注释']))

# 6. 引擎/0系列未破坏
EXPECT_HEAD = ['0改写说明','0分布式体系','平台建设与依赖','平台支撑完整性','0历史',
               '0映射1','0映射2','0映射3','0封面','0目录',
               'ICD11统一命名','病证单元库','多智能体协同','兼容性思维流','可复用Skills']
check("0系列+引擎顺序", wb.sheetnames[:15] == EXPECT_HEAD, str(wb.sheetnames[:15]))
tt = "\n".join(str(c.value) for row in wb['0目录'].iter_rows() for c in row if c.value)
check("0目录完整", '素问81篇' in tt and '灵枢81篇' in tt and '痈疽' in tt)

wb.close()
print(f"PASS {len(passes)} | FAIL {len(fails)}")
for p in passes:
    print("  ✔", p)
for f in fails:
    print("  ✘", f)
sys.exit(1 if fails else 0)
'''

fd, tmp_path = tempfile.mkstemp(prefix='hermes-verify-hjnj-ch6-11-', suffix='.py', dir=tempfile.gettempdir())
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
