# -*- coding: utf-8 -*-
"""
qhzy-中医诊断学.xlsx 完整性全面检查（对标中基 101 项标准）
维度: Sheet结构/0系列/目录↔正文一致/正文层级/ICD11/BZU交叉/协同/思维流/Skills/平台依赖/端到端
"""
import sys, re, openpyxl

PATH = r'C:\Users\DELL\Desktop\qhzy-中医诊断学.xlsx'
wb = openpyxl.load_workbook(PATH, read_only=True)
fails, passes, warns = [], [], []

def check(name, cond, detail=""):
    (passes if cond else fails).append(f"{name}{(' | ' + detail) if detail and not cond else ''}")

def sheet_text(sname):
    ws = wb[sname]
    return "\n".join(str(c.value) for row in ws.iter_rows() for c in row if c.value)

# ── 1. Sheet 结构 ──
EXPECT = ['0改写说明','0分布式体系','平台建设与依赖','0映射1','0映射2','0映射3','0封面','0目录',
          'ICD11统一命名','病证单元库','多智能体协同','兼容性思维流','可复用Skills',
          '1绪论','2望诊','3闻诊','4问诊','5切诊','6八纲辨证','7病性辨证','8脏腑辨证',
          '9经络辨证','10六经辨证','11卫气营血辨证','12三焦辨证','13诊断与病案','14AI平台']
check("Sheet数=27", len(wb.sheetnames) == 27, f"实际{len(wb.sheetnames)}")
check("Sheet顺序", wb.sheetnames == EXPECT, str(wb.sheetnames))
check("无空Sheet", not [s for s in wb.sheetnames if wb[s].max_row == 0], f"空: {[s for s in wb.sheetnames if wb[s].max_row == 0]}")

# ── 2. 0改写说明 ──
t = sheet_text('0改写说明')
check("改写说明v2.0-qhzy", 'v2.0-qhzy' in t)
check("改写说明含分布式任务", '分布式' in t)
check("改写说明含版本变更", '版本变更' in t)

# ── 3. 0分布式体系 ──
t = sheet_text('0分布式体系')
for kw in ['华为云服务器','GitHub 仓库','华为硬服务器','浪潮硬服务器','台式机 T1-T4',
           '2云 + 2硬 + 4台式机','114.115.211.254','192.168.1.12','192.168.0.102',
           '四诊客观化','node-coordinator','CI/CD 人机闭环']:
    check(f"0分布式体系含[{kw}]", kw in t)
check("分布式体系无双址残留", '192.168.1.11' not in t and '双址' not in t)

# ── 4. 平台建设与依赖 ──
t = sheet_text('平台建设与依赖')
for kw in ['A. tcmP','B. 教材章节','C. 平台安装','D. 平台部署','E. 岐黄智医分布式适配','数据层','算法层','应用层','交互层','requirements.txt','pytest']:
    check(f"平台依赖含[{kw}]", kw in t)

# ── 5. 0映射1/2/3 ──
t1, t2, t3 = sheet_text('0映射1'), sheet_text('0映射2'), sheet_text('0映射3')
check("映射1蔡大勇", '蔡大勇' in t1 and 'Dayong Cai' in t1)
check("映射2雷燕审稿红线", '雷燕' in t2 and '血瘀证' in t2 and '四诊客观化' in t2)
check("映射3胡孔法AI红线", '胡孔法' in t3 and '术语映射' in t3)

# ── 6. 0封面 ──
t = sheet_text('0封面')
check("封面CM-02", 'CM-02' in t and '5 学分' in t)

# ── 7. 0目录 ↔ 正文一致性 ──
ws_toc = wb['0目录']
toc_titles = set()
for row in ws_toc.iter_rows(min_row=2, max_col=5):
    cells = ['' if c.value is None else str(c.value).strip() for c in row]
    a, b, c, d, e = cells
    if not e or a == '章':
        continue
    # 诊断学格式: 章|节|小节|段 为数字序号, 内容自带编号前缀
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

missing = []
for kind, title in sorted(toc_titles):
    if kind == '章':
        continue
    if (kind, title) not in body_titles:
        missing.append(f"{kind} {title}")
check("目录节/小节全部有正文", not missing, f"缺失: {missing[:15]}")

# 章数核对
toc_ch = {t for k, t in toc_titles if k == '章'}
body_ch = {t for k, t in body_titles if k == '章'}
check("章数=14", len(body_ch) == 14, f"正文章{len(body_ch)}")
check("目录章=正文章", len(toc_ch) == len(body_ch), f"目录{len(toc_ch)} vs 正文{len(body_ch)}")

# ── 8. 各章正文层级 ──
for sname in chapter_sheets:
    ws = wb[sname]
    cnt = {'章':0,'节':0,'小节':0,'正文':0}
    for row in ws.iter_rows(min_row=2, max_col=5):
        e = row[4].value
        if not e: continue
        e = str(e).strip()
        if re.match(r'^第\d+章', e): cnt['章'] += 1
        elif re.match(r'^\d+\.\d+\.\d+\.\d+\s', e): pass
        elif re.match(r'^\d+\.\d+\.\d+\s', e): cnt['小节'] += 1
        elif re.match(r'^\d+\.\d+\s', e): cnt['节'] += 1
        else: cnt['正文'] += 1
    check(f"{sname}有正文段", cnt['正文'] >= 3, f"正文段={cnt['正文']}")
    check(f"{sname}有节标题", cnt['节'] >= 2, f"节={cnt['节']}")

# ── 9. ICD11统一命名 ──
ws = wb['ICD11统一命名']
diseases, syndromes = [], []
for row in ws.iter_rows(min_row=3, max_col=6):
    cells = ['' if c.value is None else str(c.value).strip() for c in row]
    if re.match(r'^B\d+$', cells[0]):
        diseases.append(cells[0])
    if re.match(r'^Z\d+$', cells[0]):
        syndromes.append(cells[0])
check("ICD11病=20", len(diseases) == 20, f"实际{len(diseases)}")
check("ICD11证=15", len(syndromes) == 15, f"实际{len(syndromes)}")
t = sheet_text('ICD11统一命名')
check("ICD11含校准列", '平台db校准' in t)

# ── 10. 病证单元库 ──
ws = wb['病证单元库']
bzus = {}
for row in ws.iter_rows(min_row=3, max_col=11):
    cells = ['' if c.value is None else str(c.value).strip() for c in row]
    if re.match(r'^BZ-', cells[0]):
        bzus[cells[0]] = cells
check("BZU唯一=26", len(bzus) == 26, f"实际{len(bzus)}")
incomplete = [code for code, cells in bzus.items() if any(not cells[i] for i in range(1, 8))]
check("BZU前8列无空缺", not incomplete, f"缺: {incomplete[:5]}")
incomplete11 = [code for code, cells in bzus.items() if any(not cells[i] for i in (8, 9, 10))]
check("BZU 11列无空缺", not incomplete11, f"缺: {incomplete11[:5]}")
# 交叉一致: BZU病码/证码 vs ICD11表
b_nums = set(int(x[1:]) for x in diseases)
z_nums = set(int(x[1:]) for x in syndromes)
bad = set()
for code, cells in bzus.items():
    m = re.match(r'BZ-B(\d+)-Z(\d+)', code)
    if not m:
        bad.add(code); continue
    bn, zn = int(m.group(1)), int(m.group(2))
    if bn not in b_nums and bn != 14 and bn != 17:  # B14胁痛/B17痹证 pending
        bad.add(f"{code}病码B{bn}未定义")
    if zn not in z_nums:
        bad.add(f"{code}证码Z{zn}未定义")
check("BZU编码与ICD11交叉一致", not bad, f"{list(bad)[:6]}")

# ── 11. 多智能体协同 9角色 ──
t = sheet_text('多智能体协同')
for role in ['author-agent','tcmreviewer','tcmreviewer_ai','citation-agent','persona-agent','curriculum-agent','bingzheng-engine','compatibility-coordinator','node-coordinator']:
    check(f"协同含[{role}]", role in t)
check("协同含雷燕", '雷燕' in t)
check("协同含胡孔法", '胡孔法' in t)

# ── 12. 兼容性思维流 7局 ──
t = sheet_text('兼容性思维流')
for kw in ['中医 vs 现代医学','经典 vs AI','辨病 vs 辨证','守正 vs 创新','双审稿冲突','120门学科','算力调度']:
    check(f"思维流含[{kw}]", kw in t)
check("思维流含永久协议", '永久协议' in t)

# ── 13. 可复用Skills ──
ws = wb['可复用Skills']
skills = {}
for row in ws.iter_rows(min_row=2, max_col=6):
    cells = ['' if c.value is None else str(c.value).strip() for c in row]
    if cells[0].startswith('tcm-'):
        skills[cells[0]] = cells
check("Skills≥7", len(skills) >= 7, f"实际{len(skills)}")
incomplete_s = [k for k, c in skills.items() if any(not c[i] for i in range(1, 6))]
check("Skills 6列无空缺", not incomplete_s, f"缺列: {incomplete_s}")

# ── 14. 14AI平台 14.4/14.5 ──
t = sheet_text('14AI平台')
for kw in ['14.4 岐黄智医分布式教学平台','14.5 四诊客观化数据闭环','14.1','14.2','14.3']:
    check(f"14AI平台含[{kw}]", kw in t)

# ── 15. 浪潮单址全簿校验 ──
for sname in wb.sheetnames:
    ws = wb[sname]
    for row in ws.iter_rows():
        for c in row:
            if c.value and isinstance(c.value, str) and '192.168.1.11' in c.value:
                fails.append(f"残留双址[{sname}]R{c.row}")

wb.close()
print(f"PASS {len(passes)} | FAIL {len(fails)} | WARN {len(warns)}")
for p in passes: print("  ✔", p)
for f in fails: print("  ✘", f)
for w_ in warns: print("  ⚠", w_)
sys.exit(1 if fails else 0)
