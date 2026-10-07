# -*- coding: utf-8 -*-
"""
生成《中医知识树》新学科构建素材 →  <桌面>\中医知识树.xlsx
=====================================================================
流程：**GitBook（Markdown 书稿）→ Excel**（技能 gitbook-to-excel）＋ 平台数据页。

     kg/tree/book/  (SUMMARY.md + 10 章 *.md，含目录结构与正文内容)
            │  scripts/gitbook_to_excel.py:write_book()
            ▼
     0封面 / 0目录 / 0正文总表 / 第一章…第十章
            ＋
     D07-S04 中医知识树（5 列大纲，替代原表） · 知识树总览 · 图谱接口 ·
     embedding-code（ICD-11 / FTS5 / RRF / 上下文工程） · 构建与部署

数据源：kg/tree/tcm-knowledge-tree.json（build_knowledge_tree.py 生成）+ 书稿 md
用法：python scripts/gen_knowledge_tree_xlsx.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
from gitbook_to_excel import write_book, sanitize  # noqa: E402

TREE_JSON = REPO / "kg" / "tree" / "tcm-knowledge-tree.json"
BOOK = REPO / "kg" / "tree" / "book"
OUT = Path.home() / "Desktop" / "中医知识树.xlsx"

INDIGO, INDIGO_L, GOLD, GRAY_L, WHITE = "1F3A5F", "D6E4F0", "C9A227", "F2F2F2", "FFFFFF"
GREEN_L, BLUE_L, ORANGE_L, PURPLE_L = "E2EFDA", "DDEBF7", "FCE4D6", "E4DFEC"
F_TITLE = Font(name="微软雅黑", size=15, bold=True, color=WHITE)
F_H1 = Font(name="微软雅黑", size=12, bold=True, color=INDIGO)
F_BODY = Font(name="微软雅黑", size=10, color="333333")
F_BODY_B = Font(name="微软雅黑", size=10, bold=True, color="333333")
F_CODE = Font(name="Consolas", size=9, color="1B5E20")
F_SMALL = Font(name="微软雅黑", size=9, color="666666")
THIN = Side(style="thin", color="BBBBBB")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
AL_L = Alignment(horizontal="left", vertical="top", wrap_text=True)
AL_C = Alignment(horizontal="center", vertical="center", wrap_text=True)


def pf(c):
    return PatternFill(patternType="solid", fgColor=c) if c else None


class SW:
    def __init__(self, ws, widths):
        self.ws, self.r = ws, 1
        for i, w in enumerate(widths, 1):
            ws.column_dimensions[get_column_letter(i)].width = w

    @staticmethod
    def _pick(seq, i, default=None):
        if seq is None:
            return default
        if isinstance(seq, (list, tuple)):
            if not seq:
                return default
            return (seq[i] if i < len(seq) else seq[-1]) or default
        return seq

    def row(self, cells, fill=None, font=None, align=None, h=None):
        for ci, v in enumerate(cells, 1):
            c = self.ws.cell(self.r, ci, v)
            c.border = BORDER
            c.font = self._pick(font, ci - 1, F_BODY)
            c.alignment = self._pick(align, ci - 1, AL_L)
            f = self._pick(fill, ci - 1, None)
            if f:
                c.fill = f
        if h:
            self.ws.row_dimensions[self.r].height = h
        self.r += 1

    def title(self, text, span):
        self.row([text] + [""] * (span - 1), pf(INDIGO), F_TITLE, AL_C, 28)
        self.ws.merge_cells(start_row=self.r - 1, start_column=1, end_row=self.r - 1, end_column=span)

    def section(self, text, span, fill=INDIGO_L):
        self.row([text] + [""] * (span - 1), pf(fill), F_H1, AL_L, 20)
        self.ws.merge_cells(start_row=self.r - 1, start_column=1, end_row=self.r - 1, end_column=span)

    def head(self, cells):
        self.row(cells, pf(INDIGO_L), F_BODY_B, AL_C, 18)


# ── 课程大纲（D07-S04 5 列范式用的篇·章·节）──
PEI = {
    "第1篇": ("树图一体原理篇", [
        ("第一章  绪论——从知识图谱到中医知识树", "concept", [
            ("1.1", "知识图谱的成就与局限", "theory"), ("1.2", "中医药知识的两层结构：层次与关系", "theory"),
            ("1.3", "中医知识树的定义与核心隐喻（须—根—干—枝—叶）", "concept"),
            ("1.4", "树图一体：知识图谱如何成为知识树的经脉", "concept"),
            ("1.5", "知识树的编码体系：五级点分编码", "concept"),
            ("1.6", "中医知识树的平台意义与技术挑战", "practice")]),
        ("第二章  中医药知识的表示基础", "concept", [
            ("2.1", "知识表示方法概览（框架/语义网络/本体/属性图）", "theory"),
            ("2.2", "RDF/OWL 与属性图（LPG）", "concept"), ("2.3", "树结构与图结构的数学基础", "concept"),
            ("2.4", "中医药领域本体设计（七步法）", "principle"),
            ("2.5", "知识图谱嵌入（TransE/RotatE）与树的向量表示", "principle")]),
    ]),
    "第2篇": ("树骨架构建篇", [
        ("第三章  须与根：哲学根基与核心公理", "principle", [
            ("3.1", "须层：象数阴阳/五行/精气神/天人相应/藏象经络/恒动整体", "concept"),
            ("3.2", "根层：整体观念/辨证论治/恒动平衡/治未病", "concept"),
            ("3.3", "须→根的滋养边构建", "principle"), ("3.4", "根基层的动态更新与学术演进", "practice")]),
        ("第四章  干与枝：院系域与学科分枝", "principle", [
            ("4.1", "干层：八大院系域的划分原则", "theory"), ("4.2", "枝层：120 门学科的挂接", "data"),
            ("4.3", "学科前置依赖的抽取与图化", "principle"),
            ("4.4", "教材四级目录（篇·章·节·目）到树编码的映射", "principle"),
            ("4.5", "技能挂点：教育技能如何绑定学科枝", "practice")]),
    ]),
    "第3篇": ("叶与图经脉篇", [
        ("第五章  叶层：章节知识点与病证单元", "data", [
            ("5.1", "章节知识点的抽取与编址", "data"), ("5.2", "病证单元（DSU）作为最小编写原子", "concept"),
            ("5.3", "中医智能服务单元的正名与降格（学科正名／服务降格）", "practice"),
            ("5.4", "叶节点的属性与质量门禁", "data"), ("5.5", "叶级检索与定位", "practice")]),
        ("第六章  跨枝经脉：五行与经络、六经", "principle", [
            ("6.1", "五行生克乘侮的图建模", "concept"), ("6.2", "十二经脉流注与表里相合", "concept"),
            ("6.3", "六经传变与病证桥接", "principle"), ("6.4", "方证对应、君臣佐使、引经报使", "concept"),
            ("6.5", "经脉边的推理与路径发现", "principle")]),
        ("第七章  病证桥接与 ICD-11 编码", "data", [
            ("7.1", "病侧与证侧的双向锚定", "concept"), ("7.2", "内网 ICD-11 镜像与本地编码库", "data"),
            ("7.3", "病证桥接的证据等级体系", "data"), ("7.4", "编码映射的校验与冲突消解", "practice")]),
    ]),
    "第4篇": ("平台落地与实验篇", [
        ("第八章  构建管线与工程实现", "principle", [
            ("8.1", "单一事实源与生成器模式", "principle"), ("8.2", "多源异构数据的容错解析", "data"),
            ("8.3", "知识树的 Schema 设计与校验", "data"), ("8.4", "构建的自检与质量门禁", "practice"),
            ("8.5", "与 Embedding 引擎的双向绑定（TF-IDF+FTS5+RRF+上下文工程）", "principle")]),
        ("第九章  知识树的应用", "practice", [
            ("9.1", "教材编排与目录对齐", "practice"), ("9.2", "教育资源技能路由", "practice"),
            ("9.3", "以病索证／以证溯病的检索", "practice"), ("9.4", "六者 Agent 的知识边界加载", "practice"),
            ("9.5", "医圣成长路径的可量化考核", "practice"), ("9.6", "知识树可视化与终端呈现", "practice")]),
        ("第十章  实验", "experiment", [
            ("10.1", "实验一：运行构建器生成知识树", "experiment"),
            ("10.2", "实验二：用查询引擎做树导航与图邻接", "experiment"),
            ("10.3", "实验三：基于知识树的中医问答／辨证辅助", "experiment"),
            ("10.4", "课程项目：知识树驱动的学科概览 App", "experiment")]),
    ]),
}
MU = {
    "concept": ["核心概念", "方法与要点", "平台对齐实践", "典型应用"],
    "theory": ["基本概念与内涵", "主要内容与范畴", "发展历程与现状", "在中医药领域的意义"],
    "principle": ["核心原理与流程", "关键实现步骤", "性能评估与对比", "中医药场景适配"],
    "data": ["数据来源与采集", "数据结构与标准", "质量控制与清洗", "平台对接与入库"],
    "practice": ["应用场景分析", "典型案例拆解", "实施步骤与要点", "效果评估与总结"],
    "experiment": ["实验目标与环境", "操作步骤", "结果与分析", "实验报告要求"],
}

# ── embedding-code 页：真实平台代码与实测 ──
EMBED_CODE = [
    ("① Document 构建（病侧＋证侧 → 单文本）", """# scripts/tcm_embed.py · build_document()
text = (f"疾病：{disease}；ICD-11编码：{icd}；{dcat}。"
        f"西医症状：{dsym}。"
        f"中医证候：{syndrome}（{pat}），脏腑：{zf}，六经：{six}。"
        f"主症：{ssym}。主方：{formula}。")"""),
    ("② 中文分词（字符 bigram + 英文词）", """# scripts/tcm_embed.py · tokenize()
for seg in re.findall(r"[\\u4e00-\\u9fff]+", text):
    toks += [seg[i:i+2] for i in range(len(seg)-1)] if len(seg) > 1 else [seg]"""),
    ("③ TF-IDF 字符 n-gram 向量（零依赖起步）", """from sklearn.feature_extraction.text import TfidfVectorizer
vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(1, 3))
X = vec.fit_transform([d["text"] for d in docs])   # 每片叶一行"""),
    ("④ SQLite FTS5 全文索引（BM25）", """con.execute("CREATE VIRTUAL TABLE fts USING fts5("
            "id UNINDEXED, text, tokenize='unicode61')")
con.executemany("INSERT INTO fts VALUES (?,?)", [(d["id"], d["text"]) for d in docs])"""),
    ("⑤ RRF 融合（向量 Top-K ∪ FTS5 Top-K，k=60）", """def rrf(rank_lists, k=60):
    score = {}
    for rl in rank_lists:
        for i, doc in enumerate(rl):
            score[doc] = score.get(doc, 0) + 1.0 / (k + i + 1)
    return sorted(score, key=score.get, reverse=True)"""),
    ("⑥ 上下文工程（只送 Top-5 叶 ≈1.5K token，↓95%）", """# 装配顺序由知识树决定：path(叶)给学科坐标 → neighbors(叶)给关系证据 → 按证据等级排序
ctx = [{"where": path(leaf), "why": neighbors(leaf, rels=["manifests_as","icd11_map","bridge"]),
        "text": leaf_text} for leaf in top5]
# LLM 只消费 ctx（小上下文），检索/排序/融合全部内网完成，零 token"""),
    ("⑦ ICD-11 客户端（双通道）", """# scripts/icd11_client.py
ICD_API_HEADERS = {"Accept": "application/json", "Accept-Language": "zh", "API-Version": "v2"}
# 通道1：内网 API 192.168.0.111:8080（中文搜索 → Foundation ID）
# 通道2：本地 data/icd11_mms.db（31,838 实体；Foundation ID → MMS 标准编码）
def code_by_id(foundation_id):
    return conn.execute("SELECT id, code, title FROM entities WHERE id=?",
                        (str(foundation_id),)).fetchone()"""),
    ("⑧ 知识树查询（本课程新增）", """# kg/tree/tcm_tree.py
t.path("DSU-00001")        # → D01 → D01-S13 → DSU-00001（学科坐标）
t.neighbors_full("DSU-00001")  # → bridge / manifests_as / disease_is / icd11_map / hierarchy"""),
]
EMBED_RUN = [
    ("/semantic-search?q=失眠", "DSU-00035 · 心脾两虚证 · 归脾汤 · ICD-11 MC81 · score 0.1601（向量 0.160 + FTS 0）"),
    ("/diag?q=恶寒,发热,无汗", "CA00 普通感冒 · 麻黄汤（论著 RAG 范式验证记录）"),
    ("/bianzheng?q=口苦,咽干", "肝胆湿热证"),
    ("/kg/stats", "total 103 · files 7（病证单元）"),
    ("/icd/search?q=高血压（华为云公网）", "降级：ICD-11 API 不可达 → 英文检索兜底；内网/本地 db 可补编码"),
    ("/tree/stats（本课程新增）", "nodes 3063 · edges 3370 · 章节覆盖 120/120 学科"),
]


def add_outline_sheet(wb, used):
    ws = wb.create_sheet(sanitize("D07-S04 中医知识树", used))
    sw = SW(ws, [12, 10, 44, 26, 30])
    sw.title("D07-S04《中医知识树》· 教材目录（层级 | 编号 | 标题 | 内容要点 | 平台对齐）", 5)
    sw.head(["层级", "编号", "标题", "内容要点", "平台对齐"])
    note = "中医知识树（tcm-knowledge-tree v1.0.0）"
    sw.row(["教材信息", "AI-4", "《中医知识树》", "D07 中医智能学院 · D07-S04 · 替代《中医知识图谱》(AI-04)", note],
           [pf(GREEN_L)] * 3 + [None, None], [F_BODY_B] * 3 + [F_BODY, F_BODY],
           [AL_C, AL_C, AL_L, AL_L, AL_L], 20)
    for p, (pname, chs) in PEI.items():
        sw.row(["一级·篇", p, pname, f"本模块定位：{pname}（含 {len(chs)} 章）", note],
               [pf(INDIGO_L)] * 3 + [None, None], [F_BODY_B] * 3 + [F_BODY, F_BODY],
               [AL_C, AL_C, AL_L, AL_L, AL_L], 18)
        for cname, cat, secs in chs:
            sw.row(["二级·章", cname.split("  ")[0], cname, f"共 {len(secs)} 节", note],
                   [pf(GRAY_L)] * 2 + [None] * 3, [F_BODY_B] * 3 + [F_BODY, F_BODY],
                   [AL_C, AL_C, AL_L, AL_L, AL_L], 18)
            for code, stitle, scat in secs:
                sw.row(["三级·节", code, stitle, "节内容概述", note],
                       [None, pf(BLUE_L), pf(BLUE_L), None, None], [F_BODY] * 5,
                       [AL_C, AL_C, AL_L, AL_L, AL_L], 16)
                for i, mu in enumerate(MU[scat], 1):
                    sw.row(["四级·目", f"{code}.{i}", mu, "知识条目（编写要点）", note],
                           [None] * 5, [F_BODY] * 5, [AL_C, AL_C, AL_L, AL_L, AL_L], 15)
    n_sec = sum(len(s) for _, chs in PEI.values() for _, _, s in chs)
    sw.row(["统计", f"篇 {len(PEI)} · 章 {sum(len(c) for _, c in PEI.values())} · 节 {n_sec}",
            f"目 {n_sec * 4}（规则生成，可修订）", "四级目录：篇→章→节→目", note],
           [pf(GRAY_L)] * 5, F_BODY_B, [AL_C, AL_C, AL_L, AL_L, AL_L], 18)


def add_tree_sheets(wb, used, tree):
    st, nodes = tree["stats"], tree["nodes"]
    # 知识树总览
    ws = wb.create_sheet(sanitize("知识树总览", used))
    sw = SW(ws, [10, 22, 60, 12])
    sw.title("中医知识树 · 五级骨架总览（实取自 kg/tree/tcm-knowledge-tree.json）", 4)
    sw.head(["级", "名称", "内容（选取）", "数量"])
    lv = st["levels"]
    xus = " · ".join(n["name"] for n in nodes if n["kind"] == "foundation")
    gens = " · ".join(n["name"] for n in nodes if n["kind"] == "axiom")
    trunks = " · ".join(f"{n['id']} {n['name']}" for n in nodes if n["kind"] == "domain")
    for li, lname, content, num in [
        ("L0", "须（哲学根基）", xus, lv["hair"]), ("L1", "根（核心公理）", gens, lv["root"]),
        ("L2", "干（院系域）", trunks, lv["trunk"]),
        ("L3", "枝（学科）", "120 门学科（CM/MM/AT/TU/OR/ENT/AI/MG）", lv["branch"]),
        ("L4", "叶（知识点/病证单元）", f"章节知识点 {st['knowledge_points']} + 病证单元 {st['dsu']}", lv["leaf"]),
        ("—", "概念丛（图节点）", f"五行/经脉/六经/证候/西医病/ICD-11/技能 = {lv['concept']}", lv["concept"]),
    ]:
        sw.row([li, lname, content, num], [None] * 4, [F_BODY_B, F_BODY_B, F_BODY, F_BODY],
               [AL_C, AL_C, AL_L, AL_C], max(18, 14 * (len(content) // 58 + 1)))
    sw.section("八域学科分布（干 → 枝）", 4, GREEN_L)
    sw.head(["域", "院系", "学科（示例）", "学科数"])
    for n in nodes:
        if n["kind"] == "domain":
            subs = [x["name"] for x in nodes if x.get("parent") == n["id"]]
            sw.row([n["id"], n["name"], "、".join(subs[:8]) + ("…" if len(subs) > 8 else ""), len(subs)],
                   [None] * 4, [F_BODY] * 4, [AL_C, AL_L, AL_L, AL_C], 30)
    # 图谱接口
    ws = wb.create_sheet(sanitize("图谱接口", used))
    sw = SW(ws, [22, 12, 54])
    sw.title("中医知识树 ↔ 知识图谱 · 接口与边型（实取自构建产物）", 3)
    sw.section("跨枝经脉图边", 3, BLUE_L)
    sw.head(["边型 (type)", "条数", "语义"])
    SEMA = {"hierarchy": "树骨架从属（父→子）", "prerequisite": "学科先修依赖", "manifests_as": "病证单元体现为某证候",
            "disease_is": "病证单元锚定西医病", "bridge": "病证桥接（证侧→六经）", "icd11_map": "标准编码映射",
            "skill_bind": "教育技能挂点学科", "spine": "核心公理支撑院系域", "meridian_liuzhu": "十二经脉流注",
            "nourish": "根须滋养公理", "meridian_biaoli": "经脉表里相合", "wuxing_sheng": "五行相生",
            "wuxing_ke": "五行相克", "six_chuanbian": "六经传变"}
    for k, v in st["edge_types"].items():
        sw.row([k, v, SEMA.get(k, "")], [pf(GRAY_L), None, None], [F_BODY_B, F_BODY, F_BODY],
               [AL_C, AL_C, AL_L], 16)
    sw.section("病证单元（DSU）样例 —— 树中的「叶」+ 图的「节点」", 3, GREEN_L)
    sw.head(["DSU", "ICD-11", "病 × 证（所属学科枝）"])
    cnt = 0
    for n in nodes:
        if n["kind"] == "dsu":
            a = n["attrs"]
            sw.row([n["id"], a.get("icd11", ""),
                    f"{a.get('disease','')} × {a.get('syndrome','')}（{n['parent']}）"],
                   [None, pf(ORANGE_L), None], [F_BODY_B, F_BODY, F_BODY], [AL_C, AL_C, AL_L], 16)
            cnt += 1
            if cnt >= 12:
                break


def add_embed_sheet(wb, used):
    ws = wb.create_sheet(sanitize("embedding-code", used))
    sw = SW(ws, [30, 96])
    sw.title("embedding-code · ICD-11 / TF-IDF / FTS5 / RRF / 上下文工程（tcmP 真实实现）", 2)
    sw.section("一、检索与编码引擎代码", 2, GREEN_L)
    for title, code in EMBED_CODE:
        sw.row([title, ""], [pf(BLUE_L), None], [F_BODY_B, F_BODY], [AL_L, AL_L], 18)
        ws.merge_cells(start_row=sw.r - 1, start_column=1, end_row=sw.r - 1, end_column=2)
        sw.row(["代码", code], [pf(GRAY_L), None], [F_SMALL, F_CODE], [AL_C, AL_L],
               max(16, 13 * (code.count("\n") + 1) + 4))
    sw.section("二、平台实测输出（2026-10 线上验证）", 2, ORANGE_L)
    sw.head(["端点", "实测返回"])
    for ep, out in EMBED_RUN:
        sw.row([ep, out], [pf(GRAY_L), None], [F_BODY_B, F_BODY], [AL_C, AL_L],
               max(16, 13 * (len(out) // 80 + 1)))


def add_deploy_sheet(wb, used):
    ws = wb.create_sheet(sanitize("构建与部署", used))
    sw = SW(ws, [34, 74])
    sw.title("中医知识树 · 构建、校验、部署、应用（可复现命令）", 2)
    for sec, items in [
        ("【书稿 → Excel】", [("python scripts/gitbook_to_excel.py --book kg/tree/book --out book.xlsx",
                           "GitBook(SUMMARY.md+各章.md) → Excel（技能 gitbook-to-excel）")]),
        ("【构建】", [("python scripts/build_knowledge_tree.py", "单一构建点：读 tcmP 真实资源 → knowledge-tree.json + schema.json")]),
        ("【校验】", [("python scripts/verify_knowledge_tree.py", "24 项端到端自检；或 python -m pytest tests/test_knowledge_tree.py")]),
        ("【查询】", [("python kg/tree/tcm_tree.py path DSU-00001", "根→域→学科→单元 定位"),
                    ("python kg/tree/tcm_tree.py neighbors DSU-00001", "图邻接（bridge/icd11_map/…）")]),
        ("【生成素材】", [("python scripts/gen_knowledge_tree_xlsx.py", "本工作簿（书稿正文 + 平台数据页 + embedding-code）")]),
        ("【部署】", [("powershell -File scripts/deploy-knowledge-tree.ps1", "开发机 → 华为云 sage-api（上传 + 注入 /tree/* + 重启 + 验收）")]),
        ("【线上端点】", [("GET /tree/stats · /tree/node/{id} · /tree/path/{id} · /tree/neighbors/{id} · /tree/search?q=",
                        "https://www.zyyywaccn.com.cn/api/sages/tree/*")]),
    ]:
        sw.section(sec, 2)
        for cmd, desc in items:
            sw.row([cmd, desc], [pf(GRAY_L), None], [F_BODY_B, F_BODY], [AL_L, AL_L], 18)


def main():
    tree = json.loads(TREE_JSON.read_text(encoding="utf-8"))
    st = tree["stats"]
    wb = Workbook()
    wb.remove(wb.active)
    used = set()

    # 1) GitBook → Excel（目录结构 + 正文 + 每章 sheet）
    summary = write_book(wb, BOOK, {
        "title": "中医知识树",
        "meta": {
            "学科编号": "D07-S04（原《中医知识图谱》，现正名《中医知识树》）",
            "教材编号": "AI-04", "所属院系": "D07 中医智能学院",
            "学段/学分/学时": "本科U4 · 3学分 / 54学时（理论30 + 实验24）",
            "前置学科": "D07-S01 中医药人工智能导论 · D07-S02 中医信息学",
            "考核方式": "期末考试 40% + 知识树构建项目 45% + 实验报告 15%",
            "核心命题": "知识图谱回答「谁和谁有关系」；知识树回答「谁从哪里来、该先学谁、在哪门课里」",
            "平台对齐": "tcmP · kg/tree（知识树） · kg/samples（病证图谱） · /tree/* 与 /kg/* 端点",
            "构建规模": f"{st['nodes']} 节点 · {st['edges']} 边 · 章节叶 {st['knowledge_points']} · 病证单元 {st['dsu']}",
        },
        "notes_title": "【替代说明：为何用「知识树」取代「知识图谱」】",
        "notes": [
            "① 单一「知识图谱」是扁平网络，无法直接承载中医知识的「从属／递进／教学先后」，与 120 门学科目录、四级编码脱节。",
            "② 中医知识树＝知识图谱（图）× 教材目录（树）× 学科体系（干枝）＝树图一体。",
            "③ 原知识图谱的全部节点与边（病证／ICD-11／桥接）被完整吸收为知识树的叶与经脉。",
            "④ 本素材由 GitBook 书稿（kg/tree/book）经 gitbook-to-excel 转换，数据取自 tcmP 真实资源，可复现、可校验。",
        ],
    }, used)

    # 2) 平台数据页
    add_outline_sheet(wb, used)
    add_tree_sheets(wb, used, tree)
    add_embed_sheet(wb, used)
    add_deploy_sheet(wb, used)

    wb.save(OUT)
    print("saved:", OUT)
    print("sheets:", wb.sheetnames)
    print("book:", summary)
    print(f"nodes={st['nodes']} edges={st['edges']} 章节叶={st['knowledge_points']} DSU={st['dsu']}")


if __name__ == "__main__":
    main()
