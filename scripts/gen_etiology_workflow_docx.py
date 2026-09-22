# -*- coding: utf-8 -*-
"""
gen_etiology_workflow_docx.py —— 中医「工作流程」架构图 → docx（存桌面）
============================================================
来源：tcmP 病因辨证模块（docs/病因辨证模块设计-2026-09-05.md + etiology/engine.py）
1) matplotlib 绘制《中医工作流程架构图》（辨因→辨证→论治）
2) python-docx 组装标题/图片/流程说明/三因对照表/制品清单/Roadmap
3) 输出 C:\\Users\\DELL\\Desktop\\中医工作流程架构图.docx
"""
from __future__ import annotations

import tempfile
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import FancyBboxPatch

# ── 中文字体 ──────────────────────────────────────────────
FONT_SIMHEI = r"C:\Windows\Fonts\simhei.ttf"
font_manager.fontManager.addfont(FONT_SIMHEI)
plt.rcParams["font.family"] = "SimHei"
plt.rcParams["axes.unicode_minus"] = False

# 配色
C_INPUT = ("#FEF5E7", "#D35400")     # 输入层 橙
C_ENG   = ("#FCFDFD", "#4A6B8A")     # 引擎主框 蓝灰
C_NEI   = ("#FADBD8", "#B03A2E")     # 内因 朱
C_WAI   = ("#D6EAF8", "#1F618D")     # 外因 蓝
C_BNEI  = ("#D5F5E3", "#1E8449")     # 不内外因 绿
C_DOWN  = ("#F4ECF7", "#6C3483")     # 下游 紫
C_SUP   = ("#FBF5E6", "#9C640C")     # 支撑 棕金
C_BASE  = ("#EAECEE", "#5D6D7E")     # 平台条
C_STEP  = ("#FFFFFF", "#7F8C8D")
ARROW   = "#566573"


def box(ax, x, y, w, h, text, fc="#FFFFFF", ec="#555555", fs=8.5,
        tc="#222222", bold=False, lw=1.1, ls="-", rounding=0.012,
        linespacing=1.4, ha="center", va="center", zorder=3):
    p = FancyBboxPatch((x, y), w, h,
                       boxstyle=f"round,pad=0.004,rounding_size={rounding}",
                       linewidth=lw, edgecolor=ec, facecolor=fc,
                       linestyle=ls, zorder=zorder)
    ax.add_patch(p)
    weight = "bold" if bold else "normal"
    ax.text(x + w / 2, y + h / 2, text, ha=ha, va=va, fontsize=fs,
            color=tc, fontweight=weight, linespacing=linespacing, zorder=4)


def arrow(ax, x1, y1, x2, y2, color=ARROW, lw=1.5, ms=13, dashed=False):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="-|>", color=color, lw=lw,
                                mutation_scale=ms,
                                linestyle="--" if dashed else "-"),
                zorder=5)


def vlabel(ax, x, y, text, fs=11, color="#34495E", rot=90):
    ax.text(x, y, text, fontsize=fs, color=color, rotation=rot,
            ha="center", va="center", fontweight="bold", zorder=6)


def draw_figure(out_png: Path):
    fig = plt.figure(figsize=(13.2, 10.2), dpi=190)
    fig.patch.set_facecolor("white")
    fig.suptitle("中医工作流程架构图（病因辨证模块 · 辨因 → 辨证 → 论治）",
                 fontsize=14.5, fontweight="bold", y=0.985, color="#1B2631")
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")

    # ── 输入层 ──────────────────────────────
    box(ax, 0.30, 0.875, 0.40, 0.072,
        "患者主诉 / 诱因文本\n自由文本 text ｜ 结构化 symptoms + trigger",
        fc=C_INPUT[0], ec=C_INPUT[1], fs=9.5, bold=True)
    arrow(ax, 0.50, 0.872, 0.50, 0.838)   # → 引擎

    # ── 引擎主框 ────────────────────────────
    box(ax, 0.055, 0.330, 0.705, 0.505,
        "", fc=C_ENG[0], ec=C_ENG[1], lw=1.6)
    ax.text(0.4075, 0.812, "中医病因辨证引擎  ·  etiology.engine（三因辨证）",
            ha="center", va="center", fontsize=11, fontweight="bold",
            color="#2C3E50", zorder=4)

    # L1 输入清洗
    box(ax, 0.235, 0.740, 0.345, 0.052,
        "① 输入清洗\n标点粗切短句 · 滤除时序/量词噪声 · 去重保序",
        fc=C_STEP[0], ec=C_STEP[1], fs=7.6)
    arrow(ax, 0.4075, 0.738, 0.4075, 0.708)

    # L2 门类评分
    box(ax, 0.19, 0.654, 0.435, 0.052,
        "② 三因门类评分\n门类触发词一票 +2.0（生气/受凉/暴食…）· 知识库症状命中逐条 +1.0",
        fc=C_STEP[0], ec=C_STEP[1], fs=7.6)
    ax.text(0.4075, 0.643, "▼  三因并行 · 门类内候选排序 Top-3",
            ha="center", va="center", fontsize=7.4, color="#7F8C8D", zorder=4)

    # L3 三因并行三列
    col_y, col_h = 0.462, 0.172
    box(ax, 0.095, col_y, 0.185, col_h, "", fc="#FFFFFF", ec="#D5DBDB", lw=0.9)
    box(ax, 0.295, col_y, 0.205, col_h, "", fc="#FFFFFF", ec="#D5DBDB", lw=0.9)
    box(ax, 0.515, col_y, 0.200, col_h, "", fc="#FFFFFF", ec="#D5DBDB", lw=0.9)

    # 列1 内因
    box(ax, 0.095, col_y + 0.128, 0.185, 0.044,
        "内因 · 七情辨证（nei）", fc=C_NEI[0], ec=C_NEI[1], fs=8.2, bold=True,
        rounding=0.008)
    ax.text(0.1875, col_y + 0.075,
            "怒 喜 悲 思 恐 忧 惊\n→ 五脏主情\n肝怒·心喜·肺悲·脾思·肾恐",
            ha="center", va="center", fontsize=7.0, color="#212F3D",
            linespacing=1.55, zorder=4)
    ax.text(0.1875, col_y + 0.018, "五段：刺激感应→脏腑响应→情绪涌现→情绪劫持→病机固着",
            ha="center", va="center", fontsize=5.8, color="#7B241C", zorder=4)

    # 列2 外因
    box(ax, 0.295, col_y + 0.128, 0.205, 0.044,
        "外因 · 六淫辨证（wai）", fc=C_WAI[0], ec=C_WAI[1], fs=8.2, bold=True,
        rounding=0.008)
    ax.text(0.3975, col_y + 0.075,
            "风 寒 暑 湿 燥 热\n→ 签名 E_k = (λ有形性, α三维归因, s强度)\n邪之三条件：共生/主宰/所用",
            ha="center", va="center", fontsize=7.0, color="#212F3D",
            linespacing=1.55, zorder=4)
    ax.text(0.3975, col_y + 0.018, "五段：S1感 → S2侵 → S3传 → S4化 → S5损",
            ha="center", va="center", fontsize=5.8, color="#1B4F72", zorder=4)

    # 列3 不内外因
    box(ax, 0.515, col_y + 0.128, 0.200, 0.044,
        "不内外因辨证（bunei）", fc=C_BNEI[0], ec=C_BNEI[1], fs=8.2, bold=True,
        rounding=0.008)
    ax.text(0.615, col_y + 0.075,
            "7 板块 × 68 细目\nI1饮食 I2劳逸 I3外伤 I4虫兽\nI5中毒 I6医过 I7先天",
            ha="center", va="center", fontsize=7.0, color="#212F3D",
            linespacing=1.55, zorder=4)
    ax.text(0.615, col_y + 0.018, "五段：p1损 → p2滞 → p3虚 → p4变 → p5败",
            ha="center", va="center", fontsize=5.8, color="#145A32", zorder=4)

    # 列底 → 归一
    arrow(ax, 0.1875, 0.462, 0.1875, 0.4375)
    arrow(ax, 0.3975, 0.462, 0.3975, 0.4375)
    arrow(ax, 0.615, 0.462, 0.615, 0.4375)

    # L4 归一置信
    box(ax, 0.155, 0.388, 0.505, 0.049,
        "③ 三因归一置信 → 主判\n内因 / 外因 / 不内外因 各门类置信（conf 0–1）",
        fc=C_STEP[0], ec=C_STEP[1], fs=7.6)
    arrow(ax, 0.4075, 0.386, 0.4075, 0.353)

    # L5 辨证卡输出
    box(ax, 0.155, 0.333, 0.505, 0.049,
        "④ 辨证卡输出\n病因 / 病机 / 五阶段序列 / 治则 / 方 / 穴 / 经脉 / 经文 + report() 简明报告",
        fc="#FEF9E7", ec="#B7950B", fs=7.6, bold=True)
    arrow(ax, 0.4075, 0.331, 0.4075, 0.293)

    # ── 下游：辨证 → 论治 ───────────────────
    box(ax, 0.055, 0.185, 0.705, 0.105, "", fc=C_DOWN[0], ec=C_DOWN[1], lw=1.6)
    ax.text(0.4075, 0.277, "⑤ 病证检索（辨证）→ 论治建议", ha="center",
            va="center", fontsize=9.5, fontweight="bold", color="#4A235A", zorder=4)
    box(ax, 0.085, 0.196, 0.265, 0.062,
        "sage-api 病证检索\n/diag · /bianzheng · /semantic-search\n病证单元 DSU（病侧×证侧×临床）",
        fc="#FFFFFF", ec="#8E44AD", fs=6.9)
    arrow(ax, 0.362, 0.227, 0.418, 0.227)
    box(ax, 0.425, 0.196, 0.30, 0.062,
        "论治建议（可衔接）\n推荐方 / 穴位 / 调护\n与病因辨证卡上下游闭合",
        fc="#FFFFFF", ec="#8E44AD", fs=6.9)
    ax.text(0.4075, 0.192, "辨因（病因引擎）输出 → 辨证定证 → 论治处方，形成「辨因→辨证→论治」上游链路",
            ha="center", va="center", fontsize=6.8, color="#5B2C6F", zorder=4)

    # ── 右侧支撑体系 ────────────────────────
    sx, sw = 0.795, 0.19
    box(ax, sx, 0.660, sw, 0.170, "", fc=C_SUP[0], ec=C_SUP[1], lw=1.3)
    ax.text(sx + sw / 2, 0.808, "framework.py 符号体系\n（四文件统一契约）",
            ha="center", va="center", fontsize=8.2, fontweight="bold",
            color="#7E5109", zorder=4)
    ax.text(sx + sw / 2, 0.762,
            "脏腑/经脉 四层拓扑 · 强度 5 区间\n（L1虚甚→L5亢盛，高斯归一 σ=0.42）\n五阶段对齐 · 三因签名 E_k",
            ha="center", va="center", fontsize=6.7, color="#3E2C06",
            linespacing=1.5, zorder=4)

    box(ax, sx, 0.462, sw, 0.170, "", fc=C_SUP[0], ec=C_SUP[1], lw=1.3)
    ax.text(sx + sw / 2, 0.610, "三因知识库（data/*.json）",
            ha="center", va="center", fontsize=8.2, fontweight="bold",
            color="#7E5109", zorder=4)
    ax.text(sx + sw / 2, 0.565,
            "nei_yin.json       7情 × 五脏\nwai_yin.json      6淫 × 签名\nbu_nei_wai.json  7板块 × 68细目",
            ha="center", va="center", fontsize=6.8, color="#3E2C06",
            linespacing=1.65, zorder=4)
    ax.text(sx + sw / 2, 0.505,
            "经络循行 / 方穴 / 经文锚点 verse（素问·灵枢）",
            ha="center", va="center", fontsize=6.4, color="#6E5600", zorder=4)

    box(ax, sx, 0.330, sw, 0.104, "", fc=C_SUP[0], ec=C_SUP[1], lw=1.1)
    ax.text(sx + sw / 2, 0.408, "上游数据源（桌面·醒了么张仲景）",
            ha="center", va="center", fontsize=7.4, fontweight="bold",
            color="#7E5109", zorder=4)
    ax.text(sx + sw / 2, 0.368,
            "内因七情.xlsx · 外因六淫.xlsx\nHDNJ音频理解.xls · 黄帝内经全文.xls",
            ha="center", va="center", fontsize=6.3, color="#3E2C06",
            linespacing=1.5, zorder=4)

    # 引擎 ↔ 支撑 双向虚线
    arrow(ax, 0.762, 0.62, 0.793, 0.62, lw=1.1, dashed=True, ms=9)
    arrow(ax, 0.793, 0.53, 0.762, 0.53, lw=1.1, dashed=True, ms=9)

    # ── 平台背景条 ──────────────────────────
    box(ax, 0.055, 0.045, 0.93, 0.098, "", fc=C_BASE[0], ec=C_BASE[1], lw=1.2)
    ax.text(0.52, 0.121, "tcmP 平台 · 六者·中医医院AI网络教育平台（病证知识图谱 · 医圣成长引擎）",
            ha="center", va="center", fontsize=8.6, fontweight="bold",
            color="#283747", zorder=4)
    ax.text(0.52, 0.080,
            "P2 医者 chat 自动触发 · 数字人七情安抚（诗琴书画棋/药食同源）｜P3 规者/法者质控证据链｜平台使用数据 → 教材修订（CI/CD 闭环）",
            ha="center", va="center", fontsize=6.6, color="#4D5656", zorder=4)
    ax.text(0.52, 0.056,
            "验证：2026-09-05 实测 20/20 通过（寒→麻黄汤 / 怒→柴胡疏肝散 / 饮食→保和丸 / 过劳→补中益气…）",
            ha="center", va="center", fontsize=6.4, color="#6E7B8B", zorder=4)

    # ── 阶段竖排标签 ────────────────────────
    vlabel(ax, 0.022, 0.60, "辨 因", fs=11, color="#B03A2E")
    vlabel(ax, 0.022, 0.235, "辨证 · 论治", fs=10.5, color="#6C3483")

    fig.savefig(out_png, dpi=190, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"PNG_SAVED={out_png}")


# ═══════════════════════ docx 组装 ═══════════════════════
def build_docx(png_path: Path, out_docx: Path):
    from docx import Document
    from docx.shared import Pt, Mm, Inches, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.enum.table import WD_TABLE_ALIGNMENT
    from docx.oxml.ns import qn

    FONT_CN = "微软雅黑"
    doc = Document()

    # 页面：A4 + 边距
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Mm(210), Mm(297)
    sec.left_margin = sec.right_margin = Mm(20)
    sec.top_margin = sec.bottom_margin = Mm(18)

    # 默认字体（含中文 eastAsia）
    def set_style_font(style, name=FONT_CN, size=10.5, color=None, bold=None):
        style.font.name = name
        style.font.size = Pt(size)
        if color:
            style.font.color.rgb = RGBColor(*color)
        if bold is not None:
            style.font.bold = bold
        rpr = style.element.get_or_add_rPr()
        rfonts = rpr.find(qn("w:rFonts"))
        if rfonts is None:
            rfonts = rpr.makeelement(qn("w:rFonts"), {})
            rpr.append(rfonts)
        rfonts.set(qn("w:eastAsia"), name)
        rfonts.set(qn("w:ascii"), name)
        rfonts.set(qn("w:hAnsi"), name)

    set_style_font(doc.styles["Normal"], size=10.5)
    for hname, hsize in [("Heading 1", 15), ("Heading 2", 12.5), ("Title", 19)]:
        try:
            set_style_font(doc.styles[hname], size=hsize)
        except KeyError:
            pass

    # ── 封面标题区 ──
    t = doc.add_paragraph()
    t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = t.add_run("中医「工作流程」架构图")
    r.font.size = Pt(21); r.font.bold = True
    r.font.color.rgb = RGBColor(0x1B, 0x26, 0x31)
    st = doc.add_paragraph()
    st.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r2 = st.add_run("—— 病因辨证模块 · 辨因 → 辨证 → 论治 ——")
    r2.font.size = Pt(13); r2.font.color.rgb = RGBColor(0xA3, 0x3A, 0x2B)

    meta = doc.add_paragraph()
    meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
    rm = meta.add_run("tcmP 平台（六者·中医医院AI网络教育平台） ｜ 模块版本 v0.1.0 ｜ 生成日期 2026-09-08")
    rm.font.size = Pt(9); rm.font.color.rgb = RGBColor(0x6E, 0x7B, 0x8B)

    # ── 一、架构图 ──
    doc.add_heading("一、中医工作流程架构图", level=1)
    doc.add_paragraph("本图源自 tcmP「中医病因辨证程序模块」设计文档（docs/病因辨证模块设计-2026-09-05.md）"
                      "与引擎实现（etiology/engine.py）：以中医「三因学说」（陈言《三因极一病证方论》框架 + 内经依据）为核心，"
                      "将「辨因 → 辨证 → 论治」临床工作流形式化为可计算的辨证引擎，衔接平台既有病证检索（/diag /bianzheng）。"
                      "模块落盘于 tcmP/etiology/（engine.py 引擎核心 + framework.py 符号体系 + data/ 三因知识库），"
                      "符号契约 framework_spec（v1.0 外因 / v2.0 内因 / v7.0 不内外因四层网络）。")
    pimg = doc.add_paragraph()
    pimg.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = pimg.add_run()
    run.add_picture(str(png_path), width=Inches(6.4))
    cap = doc.add_paragraph()
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    rc = cap.add_run("图 1  中医工作流程架构图（输入 → 三因辨证引擎 → 病证检索 → 论治建议；右侧为符号体系与知识库支撑）")
    rc.font.size = Pt(9); rc.font.color.rgb = RGBColor(0x56, 0x65, 0x73)

    # ── 二、工作流程分步说明 ──
    doc.add_heading("二、工作流程分步说明（引擎算法）", level=1)
    steps = [
        ("① 输入清洗", "文本按标点/空格粗切短句，滤除时序/量词噪声片段，去重保序；支持结构化输入 symptoms=[…] + trigger=…。"),
        ("② 三因门类评分", "门类特异诱因词一票 +2.0（内因：生气/受惊/焦虑…；外因：受凉/淋雨/秋燥…；不内外因：暴饮暴食/劳累/跌打…）；"
                            "知识库症状词命中逐条 +1.0；七情/六淫/板块的诱因归属词另 +1.5。"),
        ("③ 三因并行 · 类内候选排序", "三因并行辨证：内因七情（怒喜悲思恐忧惊 → 五脏主情）、外因六淫（风寒暑湿燥热 → E_k 签名）、"
                                      "不内外因（7 板块 × 68 细目）；每门类按命中分取 Top-3 候选。"),
        ("④ 三因归一置信 → 主判", "三因门类分数归一为 0–1 置信，主判（内因/外因/不内外因）+ 各门类置信度输出。"),
        ("⑤ 辨证卡输出（辨因 → 辨证 → 论治）", "每候选病因输出辨证卡：病因/病机/五阶段序列/舌脉/治则/方/穴/经脉/经文锚点；"
                                              "简明报告 report() 面向终端与 LLM 注入；下游衔接 sage-api 病证检索（/diag /bianzheng），"
                                              "推荐方药与调护，形成完整中医工作流。"),
    ]
    for title, body in steps:
        p = doc.add_paragraph(style="List Number")
        rt = p.add_run(title + "：")
        rt.bold = True
        p.add_run(body)
        p.paragraph_format.space_after = Pt(4)

    # ── 三、三因辨证门类对照 ──
    doc.add_heading("三、三因辨证门类对照表", level=1)
    rows = [
        ("门类", "候选项", "符号 / 知识模型", "五阶段对齐", "辨证卡要点"),
        ("内因·七情\n(nei_yin.json)",
         "怒·喜·悲·思·恐·忧·惊\n(+4 扩展情志)",
         "五脏主情：肝怒/心喜/肺悲/脾思/肾恐\n归因判据：怒=有形外归因 α+1；悲=无形内归因 α−1",
         "刺激感应 → 脏腑响应 → 情绪涌现 → 情绪劫持 → 病机固着",
         "病机/症状集/舌脉/传变序列/治则/方/穴/经脉/经文"),
        ("外因·六淫\n(wai_yin.json)",
         "风·寒·暑·湿·燥·热",
         "签名 E_k=(λ有形性, α三维归因[波动/能量/物质], s强度)\n入册三条件：共生/主宰/所用 全过",
         "S1感 → S2侵 → S3传 → S4化 → S5损",
         "病机/舌脉/治则/方/穴/经脉/经文"),
        ("不内外因\n(bu_nei_wai.json)",
         "I1饮食(12)/I2劳逸(10)/I3外伤(10)/I4虫兽(8)/I5中毒(10)/I6医过(10)/I7先天(8) = 68 细目",
         "板块-脏腑亲和 A_ji（I1→脾胃0.9、I2→肾脾0.8、I5→肝胃0.8、I7→肾0.9…）\n内经锚点 10 篇（饮食自倍/五劳所伤/缪刺恶血/疏五过/天癸肾气…）",
         "p1损 → p2滞 → p3虚 → p4变 → p5败",
         "病机/治则/方/穴/经脉/经文"),
    ]
    tbl = doc.add_table(rows=len(rows), cols=5)
    tbl.style = "Table Grid"
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    widths = [Mm(24), Mm(30), Mm(48), Mm(42), Mm(26)]
    for i, row in enumerate(rows):
        for j, val in enumerate(row):
            cell = tbl.cell(i, j)
            cell.width = widths[j]
            cell.text = ""
            para = cell.paragraphs[0]
            rr = para.add_run(val)
            rr.font.size = Pt(8.5)
            if i == 0:
                rr.bold = True
                shd = cell._tc.get_or_add_tcPr().makeelement(qn("w:shd"), {})
                shd.set(qn("w:fill"), "DCE6F1")
                cell._tc.get_or_add_tcPr().append(shd)

    # ── 四、模块制品清单 ──
    doc.add_heading("四、病因辨证模块制品清单", level=1)
    files = [
        ("etiology/engine.py", "辨证引擎核心（清洗→评分→分类→辨证卡→报告）", "14.9 KB"),
        ("etiology/framework.py", "符号体系常量（脏腑/经脉/5区间/五阶段/三因签名）", "8.4 KB"),
        ("etiology/data/nei_yin.json", "内因七情知识库（7情×五脏 + 4扩展情志）", "6.1 KB"),
        ("etiology/data/wai_yin.json", "外因六淫知识库（6淫×E_k签名）", "6.2 KB"),
        ("etiology/data/bu_nei_wai.json", "不内外因知识库（7板块×亲和×68细目框架）", "6.9 KB"),
        ("etiology/__init__.py", "包入口，公开 EtiologyEngine + framework", "1.6 KB"),
        ("scripts/etiology_api_demo.py", "FastAPI 接入示例（uvicorn :8411，/etiology/dialect）", "3.1 KB"),
    ]
    t2 = doc.add_table(rows=len(files) + 1, cols=3)
    t2.style = "Table Grid"
    hdr = ["文件", "职责", "规模"]
    for j, h in enumerate(hdr):
        c = t2.cell(0, j); c.text = ""
        rr = c.paragraphs[0].add_run(h); rr.bold = True; rr.font.size = Pt(9.5)
        shd = c._tc.get_or_add_tcPr().makeelement(qn("w:shd"), {})
        shd.set(qn("w:fill"), "DCE6F1")
        c._tc.get_or_add_tcPr().append(shd)
    for i, (f, d, s) in enumerate(files, start=1):
        for j, val in enumerate((f, d, s)):
            c = t2.cell(i, j); c.text = ""
            rr = c.paragraphs[0].add_run(val); rr.font.size = Pt(9)

    # ── 五、平台集成路径 ──
    doc.add_heading("五、平台集成路径（Roadmap）", level=1)
    rds = [
        ("P0（已完成）", "引擎 + 三因种子知识库 + 验证（2026-09-05 实测 20/20 通过）"),
        ("P1", "知识库全量扩展（68 细目/内经锚点全量入库）；FastAPI 端点入 sage-api（/etiology/dialect，华为云 8300）"),
        ("P2", "与六者 Agent 融合：医者 chat 自动触发；数字人七情辨证 → 情绪安抚策略（诗琴书画棋/药食同源，逆转七情逻辑）"),
        ("P3", "会诊引用：外因六淫五阶段 + 不内外因板块亲和 → 规者/法者质控证据链"),
    ]
    for tag, desc in rds:
        p = doc.add_paragraph()
        rt = p.add_run(tag + "："); rt.bold = True
        p.add_run(desc)
        p.paragraph_format.space_after = Pt(3)

    note = doc.add_paragraph()
    nr = note.add_run("注：本架构图数据来源为 tcmP 仓库病因辨证模块设计文档 v0.1.0 及引擎源码；"
                      "框架契约 framework_spec（v1.0 外因 / v2.0 内因 / v7.0 不内外因四层网络），四文件共用同一符号体系。")
    nr.font.size = Pt(8.5); nr.font.color.rgb = RGBColor(0x6E, 0x7B, 0x8B)

    doc.save(out_docx)
    print(f"DOCX_SAVED={out_docx}")


if __name__ == "__main__":
    DESKTOP = Path(r"C:\Users\DELL\Desktop")
    out_png = Path(tempfile.gettempdir()) / "etiology_workflow_arch.png"
    out_docx = DESKTOP / "中医工作流程架构图.docx"
    draw_figure(out_png)
    build_docx(out_png, out_docx)
    os_remove = __import__("os").remove
    try:
        os_remove(out_png)
    except OSError:
        pass
    print("DONE")
