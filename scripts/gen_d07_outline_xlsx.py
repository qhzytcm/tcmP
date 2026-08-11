# -*- coding: utf-8 -*-
"""
gen_d07_outline_xlsx.py — D07 中医智能学院 15 门学科教材四级目录生成器
====================================================================
输入: domain-specs/DOMAIN_SPEC_D07.md（14 门学科，章+节两级）
       + 本脚本内置 D07-S15（中医大模型与智能体应用，手写四级目录）
输出: 桌面 D007textbooks.xlsx（每课一个 sheet，四级目录：篇→章→节→目）

四级目录结构（教材编写大纲）:
  一级 篇   —— 模块划分（基础/核心/应用/实验）
  二级 章   —— 沿用规范章节目录（141 章）
  三级 节   —— 沿用规范节（891 节）
  四级 目   —— 知识条目（规则生成：每节 3-4 个，可修订）

平台对齐: 每门课标注 tcmP 平台对应能力（端点/SOUL/图谱/医圣），
          S15 全课映射 ai-curriculum L1-L6 教学切片。

用法: python scripts/gen_d07_outline_xlsx.py [--out 路径] [--spec 路径]
"""
from __future__ import annotations
import argparse
import re
import sys
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

# ───────────────── 1. 解析领域规范（章 + 节） ─────────────────
def parse_spec(spec_path: Path) -> list:
    text = spec_path.read_text(encoding="utf-8")
    blocks = re.split(r"^### D07-S\d+：", text, flags=re.M)
    subjects = []
    for i, b in enumerate(blocks[1:], 1):
        name = b.strip().splitlines()[0].strip()
        m = re.search(r"#### 章节目录\s*\n```(.*?)```", b, re.S)
        chapters = []
        if m:
            cur = None
            for line in m.group(1).splitlines():
                lm = re.match(r"^\s*(第[一二三四五六七八九十百\d]+章\s*\S+.*?)\s*$", line)
                if lm:
                    if cur:
                        chapters.append(cur)
                    cur = {"title": lm.group(1).strip(), "sections": []}
                elif cur:
                    sm = re.match(r"^\s*(\d+\.\d+)\s*(.+?)\s*$", line)
                    if sm:
                        cur["sections"].append({"no": sm.group(1),
                                                 "title": sm.group(2).strip()})
            if cur:
                chapters.append(cur)
        subjects.append({"id": f"D07-S{i:02d}", "name": name,
                         "chapters": chapters})
    return subjects


# ───────────────── 2. 篇映射（每门课 4-5 篇，按章节语义） ─────────────────
# 格式: {"D07-S01": [("篇名", 起始章序号, 结束章序号), ...]} 章序号从 1 开始
PART_MAP = {
    "D07-S01": [("基础与认知篇", 1, 1), ("AI核心原理篇", 2, 7),
                ("伦理与素养篇", 8, 8), ("实验与实训篇", 9, 10)],
    "D07-S02": [("基础与标准化篇", 1, 2), ("信息技术与系统篇", 3, 5),
                ("数据与挖掘篇", 6, 7), ("前沿与实验篇", 8, 10)],
    "D07-S03": [("数据科学基础篇", 1, 2), ("数据工程与特征篇", 3, 4),
                ("建模与深度学习篇", 5, 7), ("项目与实验篇", 8, 10)],
    "D07-S04": [("图谱基础篇", 1, 2), ("知识抽取篇", 3, 4),
                ("融合存储与推理篇", 5, 7), ("应用与实验篇", 8, 10)],
    "D07-S05": [("智能诊断总论篇", 1, 1), ("四诊智能化篇", 2, 5),
                ("辨证与处方智能化篇", 6, 8), ("系统与实验篇", 9, 11)],
    "D07-S06": [("NLP基础篇", 1, 3), ("核心任务篇", 4, 6),
                ("生成与问答篇", 7, 9), ("综合实验篇", 10, 10)],
    "D07-S07": [("问诊系统总论篇", 1, 2), ("语言理解与辨证篇", 3, 6),
                ("系统与评估篇", 7, 9), ("实验与项目篇", 10, 10)],
    "D07-S08": [("机器学习基础篇", 1, 3), ("无监督与深度学习篇", 4, 5),
                ("高级方法篇", 6, 9), ("实验与项目篇", 10, 10)],
    "D07-S09": [("影像基础篇", 1, 2), ("图像分析技术篇", 3, 5),
                ("中医影像专题篇", 6, 7), ("系统与实验篇", 8, 11)],
    "D07-S10": [("电子病历基础篇", 1, 2), ("数据建模与分析篇", 3, 4),
                ("CDSS决策篇", 5, 8), ("集成部署与实验篇", 9, 10)],
    "D07-S11": [("仪器总论篇", 1, 2), ("四诊仪器篇", 3, 5),
                ("治疗与可穿戴篇", 6, 7), ("系统集成篇", 8, 9)],
    "D07-S12": [("计算中医总论篇", 1, 2), ("数学与计算方法篇", 3, 5),
                ("智能计算应用篇", 6, 8), ("前沿与实验篇", 9, 10)],
    "D07-S13": [("数字化诊疗总论篇", 1, 2), ("核心系统与数据篇", 3, 5),
                ("智能诊疗应用篇", 6, 8), ("部署与实验篇", 9, 10)],
    "D07-S14": [("伦理基础篇", 1, 2), ("AI伦理专题篇", 3, 6),
                ("中医药AI治理篇", 7, 9), ("综合研讨篇", 10, 10)],
    "D07-S15": [("大模型总论篇", 1, 1), ("核心技术篇（对齐L1-L4）", 2, 5),
                ("智能体与编排篇（对齐L5-L6）", 6, 7),
                ("微调评测篇", 8, 8), ("平台工程与实训篇", 9, 10)],
}


def assign_parts(subject_id: str, chapters: list) -> list:
    """章节 → 篇标注（返回每章的篇名）"""
    parts = PART_MAP.get(subject_id)
    n = len(chapters)
    if not parts:
        parts = [("基础篇", 1, 1), ("核心原理篇", 2, max(2, n - 2)),
                 ("应用篇", max(3, n - 1), n - 1), ("实验篇", n, n)]
    out = []
    for i, ch in enumerate(chapters, 1):
        part = next((p for p in parts if p[1] <= i <= p[2]), parts[-1])
        out.append(part[0])
    return out


# ───────────────── 3. 目生成规则（节标题 → 3-4 个知识条目） ─────────────────
def gen_items(sec_title: str) -> list:
    t = sec_title
    if any(k in t for k in ("概述", "导论", "概论", "简介", "绪论", "引言", "总论")):
        return ["基本概念与内涵", "主要内容与范畴", "发展历程与现状",
                "在中医药领域的意义"]
    if any(k in t for k in ("原理", "机制", "模型", "算法", "方法", "技术", "流程",
                            "框架", "设计")):
        return ["核心原理与流程", "关键实现步骤", "性能评估与对比",
                "中医药场景适配"]
    if any(k in t for k in ("数据", "标准", "规范", "库", "集", "标注")):
        return ["数据来源与采集", "数据结构与标准", "质量控制与清洗",
                "平台对接与入库"]
    if any(k in t for k in ("应用", "实践", "案例", "实验", "实训", "实战", "项目",
                            "系统")):
        return ["应用场景分析", "典型案例拆解", "实施步骤与要点",
                "效果评估与总结"]
    if any(k in t for k in ("伦理", "安全", "隐私", "责任", "治理", "法规", "公平")):
        return ["基本原则", "风险与边界", "合规要求", "平台落地约束"]
    if any(k in t for k in ("辨证", "证候", "诊断", "处方", "问诊")):
        return ["领域知识要点", "数字化表示方法", "智能化流程", "临床验证要求"]
    return ["核心概念", "方法与要点", "平台对齐实践", "典型应用"]


# ───────────────── 4. 平台对齐（学科 → tcmP 能力） ─────────────────
PLATFORM_MAP = {
    "D07-S01": "tcmP 平台总览：六者架构/医圣 SOUL/教材-图谱-平台闭环",
    "D07-S02": "ICD-11 桥接（icd11_mms.db，31838 实体）+ 病证单元数据规范",
    "D07-S03": "tcmP data/ 病证 JSON + kg/samples 数据集（103+ DSU 真实样本）",
    "D07-S04": "kg/schema.json（DSU 六段式 Schema）+ 病证知识图谱 60000+ 节点",
    "D07-S05": "/diag、/bianzheng 病证检索辨证引擎（TF-IDF+FTS5+RRF）",
    "D07-S06": "tokenize 中文 bigram 分词 + tcm_embed.py embedding 引擎",
    "D07-S07": "/patients/symptom-check 症状自查 + 导诊路由（患者 Agent）",
    "D07-S08": "tcm_embed.py 模型训练范式（内网零 token 降级设计）",
    "D07-S09": "/devices/imaging 影像辅助 + 械者 Agent 设备端",
    "D07-S10": "/api/sages/rag RAG 诊断报告（检索 Top-K + LLM 精修）",
    "D07-S11": "/devices/maintenance 设备维护 + 可穿戴数据接入",
    "D07-S12": "kg 图谱 + 病证桥接（bridge 段：分子靶点↔证候场论）",
    "D07-S13": "六者平台集成：医者枢纽 + 药者审方 + 规者质控流水线",
    "D07-S14": "法者 Agent（/legals/risk 纠纷预防）+ 规者 Agent（质控治理）",
    "D07-S15": "六者平台全栈 + ai-curriculum L1-L6 教学切片（tcm_embed→RAG→SOUL→编排）",
}

# ───────────────── 5. D07-S15 手写四级目录（中医大模型与智能体应用） ─────────────────
# 全课映射 ai-curriculum L1-L6 与 tcmP 平台，作为第 15 门补齐学科
S15 = {
    "id": "D07-S15", "name": "中医大模型与智能体应用", "book": "AI-15",
    "chapters": [
        ("大模型与中医药融合总论", [
            ("1.1", "大语言模型技术概览", "Transformer 原理/预训练范式/能力边界"),
            ("1.2", "中医药大模型发展现状", "领域模型盘点/应用场景/差距分析"),
            ("1.3", "平台大模型技术选型", "DeepSeek API/本地量化/降 token 设计"),
        ]),
        ("文本表示与向量检索（对齐 L1）", [
            ("2.1", "中文分词技术", "bigram/词典/预训练分词"),
            ("2.2", "TF-IDF 文本表示", "词频/逆文档频率/向量化"),
            ("2.3", "余弦相似度与 Top-K 检索", "归一化/稀疏向量/排序"),
            ("2.4", "平台实战：tcm_embed.py", "病证单元 Document 构建/内网检索"),
        ]),
        ("倒排索引与混合检索（对齐 L2）", [
            ("3.1", "倒排索引原理", "posting list/OR-AND/复杂度"),
            ("3.2", "FTS5 全文检索", "SQLite FTS5/中文分词局限"),
            ("3.3", "RRF 融合排序", "倒数秩融合/tiebreaker"),
            ("3.4", "平台实战：/semantic-search", "向量+关键词融合检索调用"),
        ]),
        ("RAG 与病证知识问答（对齐 L3）", [
            ("4.1", "RAG 四步管线", "Retrieve/Augment/Generate"),
            ("4.2", "上下文组装与防幻觉指令", "Top-K 摘要/引用约束"),
            ("4.3", "双模式生成", "本地模板降级/LLM 精修"),
            ("4.4", "faithfulness 评估", "可溯源覆盖率"),
            ("4.5", "平台实战：/api/sages/rag", "诊断→辨证→方剂建议问答链"),
        ]),
        ("结构化输出与数据契约（对齐 L4）", [
            ("5.1", "JSON Schema 契约", "type/required/enum/pattern"),
            ("5.2", "校验器实现", "错误定位/重试喂回"),
            ("5.3", "response_format 结构化生成", "json_object/重试降级"),
            ("5.4", "平台实战：schema.json", "DSU 六段式数据契约/Pydantic"),
        ]),
        ("智能体与医圣人格（对齐 L5）", [
            ("6.1", "Agent 四件套", "SOUL/工具/记忆/反馈回路"),
            ("6.2", "医圣 SOUL 设计", "身份/学识边界/六经表/语录"),
            ("6.3", "师带徒回路", "user_level 深度映射"),
            ("6.4", "平台实战：/api/sages/consult", "张仲景人格问诊带教"),
        ]),
        ("多智能体编排与六者协作（对齐 L6）", [
            ("7.1", "六者角色分工", "医患药械规法边界与使命"),
            ("7.2", "路由与流水线", "问题分派/就诊四步闭环"),
            ("7.3", "医者枢纽协调", "辨证→审方→质控触发链"),
            ("7.4", "协作日志与进化信号", "对话→图谱→调优→上线闭环"),
            ("7.5", "平台实战：agents/ 六目录", "六者 Agent 调用与协作"),
        ]),
        ("中医大模型微调与评测", [
            ("8.1", "领域微调方法", "SFT/LoRA/QLoRA"),
            ("8.2", "中医药评测基准", "辨证准确率/方剂推荐/术语一致性"),
            ("8.3", "对齐与安全", "RLHF/防幻觉/知识边界"),
            ("8.4", "平台实战：模型评测报告", "病证问答评测用例设计"),
        ]),
        ("平台工程与部署", [
            ("9.1", "FastAPI 服务架构", "端点设计/请求校验"),
            ("9.2", "Nginx 与 HTTPS 部署", "反代/证书/安全组"),
            ("9.3", "CI/CD 流水线", "audit_lessons 门禁/自动部署"),
            ("9.4", "三服务器拓扑", "开发机/华为云/浪潮协同"),
        ]),
        ("综合实训：搭建六者平台原型", [
            ("10.1", "项目需求与架构设计", "六者功能矩阵/数据流"),
            ("10.2", "检索与 RAG 模块开发", "tcm_embed 复刻/rag 问答"),
            ("10.3", "医圣 SOUL 与师带徒实现", "人格组装/深度教学"),
            ("10.4", "六者编排与流水线联调", "路由/审方/质控闭环"),
            ("10.5", "部署演示与答辩", "线上验证/评测报告/总结"),
        ]),
    ],
}

# ───────────────── 6. xlsx 生成 ─────────────────
HEADERS = ["层级", "编号", "标题", "内容要点", "平台对齐"]
LEVEL_STYLE = {
    1: PatternFill("solid", fgColor="DDEBF7"),   # 篇：浅蓝
    2: PatternFill("solid", fgColor="E2EFDA"),   # 章：浅绿
    3: PatternFill("solid", fgColor="FFF2CC"),   # 节：浅黄
    4: None,                                      # 目：无
}


def write_subject_sheet(wb: Workbook, subj: dict, platform: str):
    ws = wb.create_sheet(title=f"{subj['id']} {subj['name']}"[:31])
    ws.append(HEADERS)
    for c in ws[1]:
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor="4472C4")
    ws.freeze_panes = "A2"

    # 书信息行
    book_no = subj.get("book", f"AI-{subj['id'][-2:].lstrip('0')}")
    ws.append(["教材信息", book_no, f"《{subj['name']}》",
               f"D07 中医智能学院 · {subj['id']}", platform])

    parts = assign_parts(subj["id"], subj["chapters"])
    part_seq, ch_seq = {}, {}
    manual = subj.get("manual_items", {})   # {节号: [目, ...]} 手写目（S15）
    for ch, part_name in zip(subj["chapters"], parts):
        if part_name not in part_seq:
            part_seq[part_name] = len(part_seq) + 1
            ws.append(["一级·篇", f"第{part_seq[part_name]}篇", part_name,
                       f"本模块定位：{part_name}（含 {parts.count(part_name)} 章）",
                       platform])
            r = ws.max_row
            for c in ws[r]:
                c.fill = LEVEL_STYLE[1]
                c.font = Font(bold=True)
        ch_seq[part_name] = ch_seq.get(part_name, 0) + 1
        ws.append(["二级·章", ch["title"], ch["title"],
                   f"共 {len(ch['sections'])} 节", platform])
        r = ws.max_row
        for c in ws[r]:
            c.fill = LEVEL_STYLE[2]
        for sec in ch["sections"]:
            ws.append(["三级·节", sec["no"], sec["title"],
                       "节内容概述", platform])
            r = ws.max_row
            for c in ws[r]:
                c.fill = LEVEL_STYLE[3]
            items = manual.get(sec["no"]) or gen_items(sec["title"])
            for j, item in enumerate(items, 1):
                ws.append(["四级·目", f"{sec['no']}.{j}", item,
                           "知识条目（编写要点）", platform])

    ws.append([])
    ws.append(["统计", f"篇 {len(part_seq)} 个 · 章 {len(subj['chapters'])} 个 · "
                       f"节 {sum(len(c['sections']) for c in subj['chapters'])} 个",
               f"目 {sum(len(c['sections']) * 4 for c in subj['chapters'])} 个（规则生成，可修订）",
               "四级目录：篇→章→节→目", platform])
    for col, width in zip("ABCDE", (14, 14, 34, 42, 40)):
        ws.column_dimensions[get_column_letter(ord(col) - 64)].width = width


def build_s15() -> dict:
    chapters = []
    manual = {}
    for ch_title, sections in S15["chapters"]:
        secs = []
        for no, title, points in sections:
            secs.append({"no": no, "title": title})
            manual[no] = [p.strip() for p in points.split("/") if p.strip()]
        chapters.append({"title": ch_title, "sections": secs})
    return {"id": "D07-S15", "name": "中医大模型与智能体应用",
            "book": "AI-15", "chapters": chapters,
            "manual_items": manual}


def main():
    ap = argparse.ArgumentParser(description="D07 15 门学科四级目录 → D007textbooks.xlsx")
    ap.add_argument("--out", default=r"C:\Users\DELL\Desktop\D007textbooks.xlsx")
    ap.add_argument("--spec", default=r"C:\Users\DELL\textbook-project\domain-specs\DOMAIN_SPEC_D07.md")
    args = ap.parse_args()

    subjects = parse_spec(Path(args.spec))
    subjects.append(build_s15())          # 补齐第 15 门

    wb = Workbook()
    wb.remove(wb.active)
    for s in subjects:
        write_subject_sheet(wb, s, PLATFORM_MAP.get(s["id"], "tcmP 平台"))

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    wb.save(out)

    # 统计
    total_parts = total_ch = total_sec = total_items = 0
    for s in subjects:
        parts = len(PART_MAP.get(s["id"], [])) if s["id"] != "D07-S15" else 5
        nch = len(s["chapters"])
        nsec = sum(len(c["sections"]) for c in s["chapters"])
        total_parts += parts
        total_ch += nch
        total_sec += nsec
        total_items += nsec * 4
    print(f"✅ 已生成: {out}")
    print(f"   学科 {len(subjects)} 门 · 篇 {total_parts} · 章 {total_ch} · "
          f"节 {total_sec} · 目 {total_items}")
    print(f"   Sheets: {wb.sheetnames[:3]} ... 共 {len(wb.sheetnames)} 个")


if __name__ == "__main__":
    main()
