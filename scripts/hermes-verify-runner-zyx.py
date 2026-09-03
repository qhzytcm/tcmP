# -*- coding: utf-8 -*-
"""runner: tempfile 生成 hermes-verify- 前缀验证脚本（OS-safe, ad-hoc）→ 运行 → 清理"""
import os, subprocess, sys, tempfile

BODY = r'''# -*- coding: utf-8 -*-
"""hermes-verify-zyx-final.py — qhzy-中药学.xlsx 完善后聚焦验证（ad-hoc）"""
import sys, re, openpyxl

PATH = r'C:\Users\DELL\Desktop\qhzy-中药学.xlsx'
fails, passes = [], []

def check(name, cond, detail=""):
    (passes if cond else fails).append(f"{name}{(' | ' + detail) if detail and not cond else ''}")

wb = openpyxl.load_workbook(PATH, read_only=True)

def sheet_text(sname):
    ws = wb[sname]
    return "\n".join(str(c.value) for row in ws.iter_rows() for c in row if c.value)

# 1. 43 Sheet
EXPECT = ['0改写说明','0分布式体系','平台建设与依赖','0映射1','0映射2','0映射3','0封面','0目录',
          'ICD11统一命名','病证单元库','多智能体协同','兼容性思维流','可复用Skills',
          '1绪论','2简史','3产地采集','4炮制','5性能','6配伍','7禁忌','8剂量用法',
          '9解表药','10清热药','11泻下药','12祛风湿药','13化湿药','14利水渗湿药','15温里药',
          '16理气药','17消食药','18驱虫药','19止血药','20活血化瘀药','21化痰止咳','22安神药',
          '23平肝息风','24开窍药','25补虚药','26收涩药','27涌吐药','28攻毒杀虫','29拔毒化腐','30临床中药应用']
check("Sheet数=43", len(wb.sheetnames) == 43, f"实际{len(wb.sheetnames)}")
check("Sheet顺序", wb.sheetnames == EXPECT)
check("无空Sheet", not [s for s in wb.sheetnames if wb[s].max_row == 0])

# 2. 0分布式体系（A800）
t = sheet_text('0分布式体系')
for kw in ['华为云服务器','GitHub 仓库服务器','华为硬服务器','浪潮硬服务器(含A800)','台式机 T1-T4',
           'A800','192.168.0.102','智能鉴别','药性预测','node-coordinator']:
    check(f"0分布式体系含[{kw}]", kw in t)

# 3. 30.4 章节 + 学时归属
t = sheet_text('30临床中药应用')
check("30章含30.4", '30.4 岐黄智医分布式教学平台' in t)
check("30章含药者", '药者(核心对接角色)' in t)
t = sheet_text('0目录')
check("0目录含30.4学时归属", '30.4 岐黄智医分布式教学平台（学时含于' in t)

# 4. ICD11 校准
ws = wb['ICD11统一命名']
calib = {}
for row in ws.iter_rows(min_row=3, max_col=6):
    b = row[0].value
    if b and str(b).strip() in ('B8','B9','B10','B12','B19'):
        calib[str(b).strip()] = str(row[5].value) if row[5].value else ''
check("B8→MB48.0", 'MB48.0' in calib.get('B8',''))
check("B9→8B11", '8B11' in calib.get('B9',''))
check("B10→MD81", 'MD81' in calib.get('B10',''))
check("B12→DD91.2", 'DD91.2' in calib.get('B12',''))
check("B19→ME84.2", 'ME84.2' in calib.get('B19',''))

# 5. BZU 11 列 + 溯源说明
ws = wb['病证单元库']
bzu_n = c9 = c10 = c11 = 0
for row in ws.iter_rows(min_row=3, max_col=11):
    if row[0].value and str(row[0].value).startswith('BZ-'):
        bzu_n += 1
        if row[8].value: c9 += 1
        if row[9].value: c10 += 1
        if row[10].value: c11 += 1
check("BZU=26", bzu_n == 26, f"实际{bzu_n}")
check("脏腑/六经/舌脉全填", c9 == c10 == c11 == 26, f"{c9}/{c10}/{c11}")
check("BZU含药名变体说明", '生地' in sheet_text('病证单元库') and '丹皮' in sheet_text('病证单元库'))

# 6. 287 味药精确覆盖
names = {9:'解表药',10:'清热药',11:'泻下药',12:'祛风湿药',13:'化湿药',14:'利水渗湿药',15:'温里药',
         16:'理气药',17:'消食药',18:'驱虫药',19:'止血药',20:'活血化瘀药',21:'化痰止咳',22:'安神药',
         23:'平肝息风',24:'开窍药',25:'补虚药',26:'收涩药',27:'涌吐药',28:'攻毒杀虫',29:'拔毒化腐'}
total = 0
for n in range(9, 30):
    ws2 = wb[f'{n}{names[n]}']
    for row in ws2.iter_rows(min_row=1, max_col=5):
        e = row[4].value
        if e and isinstance(e, str):
            m = re.match(r'^(.+?)·来源与性味归经$', e.strip())
            if m:
                total += 1
check("287味药覆盖", total == 287, f"实际{total}")

# 7. 学时汇总 160
t = sheet_text('0目录')
check("学时合计160", '160' in t and '160学时' in t)

# 8. 引擎增补
check("协同含node-coordinator", 'node-coordinator' in sheet_text('多智能体协同'))
check("思维流含算力调度", '算力调度' in sheet_text('兼容性思维流'))
check("Skills含分布式编排", 'tcm-distributed-node-orchestration' in sheet_text('可复用Skills'))
check("平台依赖含E节", 'E. 岐黄智医分布式适配' in sheet_text('平台建设与依赖'))

# 9. 版本/封面
check("版本v2.0-qhzy", 'v2.0-qhzy' in sheet_text('0改写说明'))
check("封面MM-01", 'MM-01' in sheet_text('0封面'))

# 10. 端到端 build_document
sys.path.insert(0, r'C:\Users\DELL\tcmP\scripts')
from tcm_embed import build_document
wb2 = openpyxl.load_workbook(PATH, read_only=True)
ws2 = wb2['病证单元库']
ok = total_b = 0
for row in ws2.iter_rows(min_row=3, max_col=11):
    cells = ['' if c.value is None else str(c.value).strip() for c in row]
    if not cells[0].startswith('BZ-'):
        continue
    total_b += 1
    m = cells[1].split(' ')
    dsu = {
        'id': cells[0],
        'disease_side': {'disease_name': m[0], 'icd_code': m[1] if len(m) > 1 else '', 'category': '', 'molecular_targets': []},
        'syndrome_side': {'syndrome_name': cells[2], 'pattern_type': cells[2],
                          'zangfu': cells[8], 'six_channels': cells[9],
                          'key_symptoms': [s for s in cells[4].replace('、', '/').replace(',', '/').split('/') if s]},
        'clinical': {'recommended_formula': cells[6]},
    }
    doc = build_document(dsu)
    if doc['text'] and doc['dsu_id']:
        ok += 1
wb2.close()
check("build_document 26/26 兼容", ok == total_b == 26, f"实际{ok}/{total_b}")

wb.close()
print(f"PASS {len(passes)} | FAIL {len(fails)}")
for p in passes:
    print("  ✔", p)
for f in fails:
    print("  ✘", f)
sys.exit(1 if fails else 0)
'''

fd, tmp_path = tempfile.mkstemp(prefix='hermes-verify-zyx-final-', suffix='.py', dir=tempfile.gettempdir())
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
