# -*- coding: utf-8 -*-
"""runner: tempfile OS-safe 生成 hermes-verify- 脚本 → 运行 → 自动清理（ad-hoc）"""
import os, subprocess, sys, tempfile

BODY = r'''# -*- coding: utf-8 -*-
"""hermes-verify-dfzx-v2.py — qhzy-东方哲学概论.xlsx (gen_dfzx_stepE 完善后) 聚焦验证（ad-hoc）"""
import sys, re, openpyxl

PATH = r'C:\Users\DELL\Desktop\qhzy-东方哲学概论.xlsx'
fails, passes = [], []

def check(name, cond, detail=""):
    (passes if cond else fails).append(f"{name}{(' | ' + detail) if detail and not cond else ''}")

wb = openpyxl.load_workbook(PATH, read_only=True)

def sheet_text(sname):
    ws = wb[sname]
    return "\n".join(str(c.value) for row in ws.iter_rows() for c in row if c.value)

# 1. 17 Sheet 结构与顺序
EXPECT = ['0历史','0分布式体系','平台建设与依赖','可复用Skills','0映射1','0映射2','0映射3','0封面','0目录',
          '1感知','2行规','3数理','4传承','5逻辑','6生态','7附件','8通雅']
check("Sheet数=17", len(wb.sheetnames) == 17, f"实际{len(wb.sheetnames)}")
check("Sheet顺序", wb.sheetnames == EXPECT)
check("无空Sheet", not [s for s in wb.sheetnames if wb[s].max_row == 0])

# 2. 0分布式体系（A800 + node-coordinator）
t = sheet_text('0分布式体系')
for kw in ['华为云服务器','GitHub 仓库服务器','华为硬服务器','浪潮硬服务器(含A800)','台式机 T1-T4',
           '2云 + 2硬 + 4台式机','A800','192.168.0.102','概念向量表','历代圣贤决策数据集',
           'node-coordinator','算力池化','故障降级','CI/CD']:
    check(f"0分布式体系含[{kw}]", kw in t)
check("无双址残留", '192.168.1.11' not in t and '双址' not in t)

# 3. 6.4 节 + 学时归属（gen_dfzx_stepE 新增）
t = sheet_text('6生态')
check("6生态含6.4", '6.4 岐黄智医分布式教学平台' in t)
check("6生态含6.4.3", '6.4.3' in t and '人机实练数据闭环' in t)
check("6生态含A800", 'A800' in t)
t = sheet_text('0目录')
check("0目录含6.4学时归属", '6.4 岐黄智医分布式教学平台（qhzy 增补·学时含于' in t)

# 4. 平台建设与依赖
t = sheet_text('平台建设与依赖')
for kw in ['A. tcmP','B. 教材章节','C. 平台安装','D. 平台部署','概念向量表','历代圣贤决策数据集','阴阳五行模型','requirements.txt','A800','torch']:
    check(f"平台依赖含[{kw}]", kw in t)

# 5. 可复用Skills 4 规格
ws = wb['可复用Skills']
skills = {}
for row in ws.iter_rows(min_row=2, max_col=6):
    cells = ['' if c.value is None else str(c.value).strip() for c in row]
    if cells[0].startswith('tcm-'):
        skills[cells[0]] = cells
check("Skills=4", len(skills) == 4, f"实际{len(skills)}")
for k in ['tcm-dongfang-zhexue-seed','tcm-concept-vector-rag','tcm-sage-decision-dataset','tcm-distributed-node-orchestration']:
    check(f"Skills含[{k}]", k in skills)

# 6. 目录↔正文双向一致（160↔160）
toc_nums = set()
for row in wb['0目录'].iter_rows(max_col=3):
    for cell in row:
        if cell.value and isinstance(cell.value, str):
            m = re.match(r'^(\d+\.\d+(?:\.\d+)*)\s', cell.value.strip())
            if m:
                toc_nums.add(m.group(1))
body_nums = set()
for s in ['1感知','2行规','3数理','4传承','5逻辑','6生态']:
    ws2 = wb[s]
    for row in ws2.iter_rows(max_col=3):
        for cell in row:
            if cell.value and isinstance(cell.value, str):
                m = re.match(r'^(\d+\.\d+(?:\.\d+)*)\s', cell.value.strip())
                if m:
                    body_nums.add(m.group(1))
check("目录↔正文双向一致", toc_nums == body_nums and len(toc_nums) == 160, f"目录{len(toc_nums)} 正文{len(body_nums)}")

# 7. 六级闭环六章完整性
for s, ch in [('1感知','第1章 感知在地'),('2行规','第2章 仿行立规'),('3数理','第3章 抽象建模'),
              ('4传承','第4章 传承延绵'),('5逻辑','第5章 逻辑升维'),('6生态','第6章 寰宇共生')]:
    t = sheet_text(s)
    check(f"{s}含章标题", ch in t)
    check(f"{s}含目标块+DSU+闭环+门禁", '知识目标' in t and '病证单位锚点(DSU)' in t and '人机闭环路径' in t and '质量门禁' in t)

# 8. 7附件C 分布式衔接（gen_dfzx_stepE 新增）
t = sheet_text('7附件')
check("7附件含A/B/C", 'A. 东方哲学核心概念向量表' in t and 'B. 历代圣贤决策数据集说明' in t and 'C. 人机闭环实验伦理规范' in t)
check("7附件C含分布式采集衔接", '分布式采集' in t and '台式机T1-T4' in t)

# 9. 0历史/0封面/8通雅
check("0历史含2026", '2026' in sheet_text('0历史') and '分布式' in sheet_text('0历史'))
t = sheet_text('0封面')
check("封面98号+30学时", ('第98号' in t or '九十八' in t) and '30' in t and '2学分' in t)
check("封面含v2.0-qhzy", 'v2.0-qhzy' in t)
check("通雅预留位", '预留' in sheet_text('8通雅'))

wb.close()
print(f"PASS {len(passes)} | FAIL {len(fails)}")
for p in passes:
    print("  ✔", p)
for f in fails:
    print("  ✘", f)
sys.exit(1 if fails else 0)
'''

fd, tmp_path = tempfile.mkstemp(prefix='hermes-verify-dfzx-v2-', suffix='.py', dir=tempfile.gettempdir())
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
