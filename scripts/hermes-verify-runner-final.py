# -*- coding: utf-8 -*-
"""
hermes-verify-runner-final.py — 用 tempfile 生成 hermes-verify- 前缀脚本并运行（OS-safe, ad-hoc）
验证目标: ① check_zdx_complete.py 修复后 98 项全过 ② qhzy-中医诊断学.xlsx 交付物终检
"""
import os, subprocess, sys, tempfile

VERIFY_BODY = r'''# -*- coding: utf-8 -*-
"""hermes-verify-zdx-final2.py — qhzy-中医诊断学.xlsx 终检 + 检查脚本回归（ad-hoc）"""
import sys, re, openpyxl

PATH = r'C:\Users\DELL\Desktop\qhzy-中医诊断学.xlsx'
fails, passes = [], []

def check(name, cond, detail=""):
    (passes if cond else fails).append(f"{name}{(' | ' + detail) if detail and not cond else ''}")

wb = openpyxl.load_workbook(PATH, read_only=True)

def sheet_text(sname):
    ws = wb[sname]
    return "\n".join(str(c.value) for row in ws.iter_rows() for c in row if c.value)

# ── 1. Sheet 结构（27） ──
EXPECT = ['0改写说明','0分布式体系','平台建设与依赖','0映射1','0映射2','0映射3','0封面','0目录',
          'ICD11统一命名','病证单元库','多智能体协同','兼容性思维流','可复用Skills',
          '1绪论','2望诊','3闻诊','4问诊','5切诊','6八纲辨证','7病性辨证','8脏腑辨证',
          '9经络辨证','10六经辨证','11卫气营血辨证','12三焦辨证','13诊断与病案','14AI平台']
check("Sheet数=27", len(wb.sheetnames) == 27, f"实际{len(wb.sheetnames)}")
check("Sheet顺序", wb.sheetnames == EXPECT)
check("无空Sheet", not [s for s in wb.sheetnames if wb[s].max_row == 0])

# ── 2. 0目录 ↔ 正文一致性（修复后的 (kind,title) 元组比较） ──
ws_toc = wb['0目录']
toc_titles = set()
for row in ws_toc.iter_rows(min_row=2, max_col=5):
    cells = ['' if c.value is None else str(c.value).strip() for c in row]
    a, b, c, d, e = cells
    if not e or a == '章':
        continue
    if re.match(r'^第\d+章', e):
        toc_titles.add(('章', e))
    elif re.match(r'^\d+\.\d+\s', e) and not re.match(r'^\d+\.\d+\.\d+', e):
        toc_titles.add(('节', e.split(' ')[0]))
    elif re.match(r'^\d+\.\d+\.\d+\s', e):
        toc_titles.add(('小节', e.split(' ')[0]))

chapter_sheets = ['1绪论','2望诊','3闻诊','4问诊','5切诊','6八纲辨证','7病性辨证','8脏腑辨证',
                  '9经络辨证','10六经辨证','11卫气营血辨证','12三焦辨证','13诊断与病案','14AI平台']
body_titles = set()
for sname in chapter_sheets:
    ws = wb[sname]
    for row in ws.iter_rows(min_row=2, max_col=5):
        e = row[4].value
        if not e: continue
        e = str(e).strip()
        if re.match(r'^第\d+章', e):
            body_titles.add(('章', e))
        elif re.match(r'^\d+\.\d+\s', e) and not re.match(r'^\d+\.\d+\.\d+', e):
            body_titles.add(('节', e.split(' ')[0]))
        elif re.match(r'^\d+\.\d+\.\d+\s', e):
            body_titles.add(('小节', e.split(' ')[0]))

missing = [f"{k} {t}" for k, t in sorted(toc_titles) if k != '章' and (k, t) not in body_titles]
check("目录节/小节全部有正文(元组比较)", not missing, f"缺失: {missing[:10]}")
toc_ch = {t for k, t in toc_titles if k == '章'}
body_ch = {t for k, t in body_titles if k == '章'}
check("章数=14", len(body_ch) == 14, f"正文章{len(body_ch)}")
check("目录章=正文章", len(toc_ch) == len(body_ch))

# ── 3. 0分布式体系 ──
t = sheet_text('0分布式体系')
for kw in ['华为云服务器','GitHub 仓库','华为硬服务器','浪潮硬服务器','台式机 T1-T4','2云 + 2硬 + 4台式机',
           '114.115.211.254','192.168.1.12','192.168.0.102','四诊客观化','node-coordinator']:
    check(f"0分布式体系含[{kw}]", kw in t)
check("无双址残留", '192.168.1.11' not in t)

# ── 4. ICD11 校准 ──
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

# ── 5. BZU 11 列 ──
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

# ── 6. BZU 病名 ↔ ICD11 表文字 ──
icd_names = set()
for row in wb['ICD11统一命名'].iter_rows(min_row=3, max_col=3):
    b, name = row[0].value, row[1].value
    if b and name and re.match(r'^B\d+$', str(b).strip()):
        icd_names.add(str(name).strip())
bzu_names = set()
for row in wb['病证单元库'].iter_rows(min_row=3, max_col=2):
    code, name = row[0].value, row[1].value
    if code and name and str(code).startswith('BZ-'):
        bzu_names.add(str(name).split(' ')[0].strip())
check("BZU病名⊆ICD11表", bzu_names <= icd_names, f"缺: {bzu_names - icd_names}")

# ── 7. 协同/思维流/Skills ──
check("协同含node-coordinator", 'node-coordinator' in sheet_text('多智能体协同'))
check("思维流含算力调度", '算力调度' in sheet_text('兼容性思维流'))
check("Skills含分布式编排", 'tcm-distributed-node-orchestration' in sheet_text('可复用Skills'))

# ── 8. 版本/封面/目录14.4/14.5/平台依赖 ──
check("版本v2.0-qhzy", 'v2.0-qhzy' in sheet_text('0改写说明'))
check("封面CM-02", 'CM-02' in sheet_text('0封面'))
t = sheet_text('0目录')
check("0目录含14.4", '14.4 岐黄智医分布式教学平台' in t)
check("0目录含14.5", '14.5 四诊客观化数据闭环' in t)
t = sheet_text('平台建设与依赖')
check("平台依赖含E节", 'E. 岐黄智医分布式适配' in t)

# ── 9. 14章正文完整性 ──
for s in chapter_sheets:
    ws = wb[s]
    secs = paras = 0
    for row in ws.iter_rows(min_row=2, max_col=5):
        e = row[4].value
        if not e: continue
        e = str(e).strip()
        if re.match(r'^\d+\.\d+\s', e) and not re.match(r'^\d+\.\d+\.\d+', e): secs += 1
        elif not re.match(r'^第|^\d+\.\d+\.\d+', e): paras += 1
    check(f"{s}有节", secs >= 2, f"节={secs}")
    check(f"{s}有正文", paras >= 3, f"正文段={paras}")

# ── 10. 端到端 build_document ──
sys.path.insert(0, r'C:\Users\DELL\tcmP\scripts')
from tcm_embed import build_document
wb2 = openpyxl.load_workbook(PATH, read_only=True)
ws2 = wb2['病证单元库']
ok = total = 0
for row in ws2.iter_rows(min_row=3, max_col=11):
    cells = ['' if c.value is None else str(c.value).strip() for c in row]
    if not cells[0].startswith('BZ-'):
        continue
    total += 1
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
check("build_document 26/26 兼容", ok == total == 26, f"实际{ok}/{total}")

wb.close()
print(f"PASS {len(passes)} | FAIL {len(fails)}")
for p in passes:
    print("  ✔", p)
for f in fails:
    print("  ✘", f)
sys.exit(1 if fails else 0)
'''

fd, tmp_path = tempfile.mkstemp(prefix='hermes-verify-zdx-final2-', suffix='.py', dir=tempfile.gettempdir())
with os.fdopen(fd, 'w', encoding='utf-8') as f:
    f.write(VERIFY_BODY)
print(f"[hermes-verify] 临时脚本: {tmp_path}")

HERMES_PY = r'C:\Users\DELL\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe'
try:
    r = subprocess.run([HERMES_PY, tmp_path], capture_output=True, text=True, encoding='utf-8', timeout=180)
    print(r.stdout)
    if r.stderr:
        print("STDERR:", r.stderr[-1500:])
    sys.exit(r.returncode)
finally:
    try:
        os.remove(tmp_path)
        print(f"[hermes-verify] 已清理: {tmp_path} 存在={os.path.exists(tmp_path)}")
    except OSError:
        pass
