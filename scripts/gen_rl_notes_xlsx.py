# -*- coding: utf-8 -*-
"""
gen_rl_notes_xlsx.py — 《强化学习的数学原理-赵世钰》教材正文生成器（v3）
=====================================================================
参考: 赵世钰(Shiyu Zhao) Mathematical Foundation of Reinforcement Learning
数据: rl_v3_a.py / rl_v3_b.py / rl_v3_c.py（10 章教材正文）
      + rl_v2_data.py（tcmP 平台对接编程技术指导 + 审校映射占位）
输出: 桌面《强化学习的数学原理-赵世钰.xlsx》
      RL01-RL10（每章：Part1 忠实听课正文 + Part2 hermes 平台改写正文）
      + tcmP平台对接编程技术指导 + 审校映射(待补全)
用法: python scripts/gen_rl_notes_xlsx.py
"""
from __future__ import annotations
import sys
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from rl_v3_a import CHAPTERS_A      # noqa: E402
from rl_v3_b import CHAPTERS_B      # noqa: E402
from rl_v3_c import CHAPTERS_C      # noqa: E402
from rl_v2_data import PROGRAMMING_GUIDE  # noqa: E402
from rl_v4_toc import toc_rows      # noqa: E402
from rl_v5_reviewers import REVIEW_SHEETS  # noqa: E402

CHAPTERS = CHAPTERS_A + CHAPTERS_B + CHAPTERS_C
OUT = Path(r"C:\Users\DELL\Desktop\强化学习的数学原理-赵世钰.xlsx")

# 章节 sheet 命名映射（RL01-RL10 → 1cmrl-* ~ 10cmrl-*，置于 0cmrl目录 之后）
SHEET_NAMES = {
    "RL01": "1cmrl-conceptions",      # 第1章 基本概念
    "RL02": "2cmrl-bellman",          # 第2章 状态价值与贝尔曼方程
    "RL03": "3cmrl-optimality",       # 第3章 最优状态价值与贝尔曼最优方程
    "RL04": "4cmrl-iteration",        # 第4章 价值迭代与策略迭代
    "RL05": "5cmrl-montecarlo",       # 第5章 蒙特卡洛方法
    "RL06": "6cmrl-approximation",    # 第6章 随机逼近
    "RL07": "7cmrl-tdlearning",       # 第7章 时序差分方法
    "RL08": "8cmrl-valuefunction",    # 第8章 价值函数方法
    "RL09": "9cmrl-policygradient",   # 第9章 策略梯度方法
    "RL10": "10cmrl-acloop",          # 第10章 Actor-Critic 方法
}

HEADERS = ["序号", "模块", "内容"]
P1_FILL = PatternFill("solid", fgColor="DDEBF7")     # Part1 原文正文：浅蓝
P2_FILL = PatternFill("solid", fgColor="E2EFDA")     # Part2 平台改写：浅绿
GUIDE_FILL = PatternFill("solid", fgColor="FCE4D6")  # 编程指导：浅橙
HDR_FILL = PatternFill("solid", fgColor="4472C4")


def style_sheet(ws, n_rows):
    ws.freeze_panes = "A2"
    for c in ws[1]:
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = HDR_FILL
    for r in range(3, 3 + n_rows):
        mod = ws.cell(r, 2).value or ""
        fill = P1_FILL if mod.startswith("[Part1") else (
            P2_FILL if mod.startswith("[Part2") else GUIDE_FILL)
        ws.cell(r, 2).fill = fill
        ws.cell(r, 3).alignment = Alignment(wrap_text=True, vertical="top")
    ws.column_dimensions["A"].width = 6
    ws.column_dimensions["B"].width = 30
    ws.column_dimensions["C"].width = 115


def main():
    wb = Workbook()
    wb.remove(wb.active)

    # 0) 四级目录（0cmrl目录，置于最前；结合三审现实映射重建）
    ws = wb.create_sheet(title="0cmrl目录")
    ws.append(["层级", "四级编码", "标题", "内容定位", "预计字数",
               "主编(user.md)", "中医药主审(tcmreviewer.md)", "智能主审(aireviewer.md)",
               "双目标/职业标注"])
    for c in ws[1]:
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = HDR_FILL
    ws.freeze_panes = "A2"
    # 三审映射说明（0映射1/2/3 初稿语义）
    mapping_notes = [
        ("映射说明", "0映射1 · user.md", "主编人选初稿：统筹十章结构、双目标（教材+平台）决策、终审定稿",
         "专业能力：全局规划+AI趋势研判", "—", "✓ 主编主责", "○ 协审", "○ 协审",
         "现实映射：主编=项目负责人；每章引言/职业应用/小结由主编统筹"),
        ("映射说明", "0映射2 · tcmreviewer.md", "中医药主审初稿：辨证准确性/方剂合规/医学术语规范/医案真实性",
         "专业能力：中医药本体+数字化适配", "—", "○ 协审", "✓ 主审主责", "○ 协审",
         "现实映射：中医药专家；语境/医案/辨证小节主审"),
        ("映射说明", "0映射3 · aireviewer.md", "智能主审初稿：数学公式/算法正确性/代码与数据校验/平台接口一致性",
         "专业能力：AI技术+趋势适应（RL前沿）", "—", "○ 协审", "○ 协审", "✓ 主审主责",
         "现实映射：AI 审校（门禁自动化）；数学/算法/接口小节主审"),
        ("篇幅预算", "全书 ≤300,000 字", "每章 3 万字：知识节 3000×6 + 平台实践 2400 + 语境 3000 + 职业应用 3000 + 章末 1500",
         "段落基准 500 字/段", "—", "—", "—", "—",
         "保障每章正文内容充分展开，10 章合计 30 万字上限"),
    ]
    for note in mapping_notes:
        ws.append(list(note))
        for c in ws[ws.max_row]:
            c.font = Font(italic=True, color="7F6000")
    toc = toc_rows()
    lv_fill = {"章": "4472C4", "节": "DDEBF7", "小节": "E2EFDA", "段落": None}
    for row in toc:
        ws.append(list(row))
        r = ws.max_row
        f = lv_fill.get(row[0])
        if f:
            ws.cell(r, 1).fill = PatternFill("solid", fgColor=f)
            ws.cell(r, 1).font = Font(bold=True)
        for col in (4, 8):
            ws.cell(r, col).alignment = Alignment(wrap_text=True, vertical="top")
    for col, width in zip("ABCDEFGHI", (8, 12, 30, 46, 10, 12, 14, 12, 40)):
        ws.column_dimensions[col].width = width

    for ch in CHAPTERS:
        sheet_name = ch["sheet"]
        for prefix, new_name in SHEET_NAMES.items():
            if sheet_name.startswith(prefix):
                sheet_name = new_name
                break
        ws = wb.create_sheet(title=sheet_name)
        ws.append(HEADERS)
        ws.append(["章", ch["title"],
                   "《Mathematical Foundation of Reinforcement Learning》赵世钰 (Shiyu Zhao), Springer"])
        for c in ws[2]:
            c.font = Font(bold=True)
        for i, (mod, content) in enumerate(ch["rows"], 1):
            ws.append([i, mod, content])
        style_sheet(ws, len(ch["rows"]))

    g = PROGRAMMING_GUIDE
    ws = wb.create_sheet(title=g["sheet"])
    ws.append(HEADERS)
    ws.append(["主题", g["title"],
               "与 tcmP 教育平台对接的代码级指导（hermes-generating-content）"])
    for c in ws[2]:
        c.font = Font(bold=True)
    for i, (mod, content) in enumerate(g["rows"], 1):
        ws.append([i, mod, content])
    style_sheet(ws, len(g["rows"]))

    rv = REVIEW_SHEETS
    for rs in rv:
        ws = wb.create_sheet(title=rs["sheet"])
        ws.append(HEADERS)
        ws.append(["映射角色", rs["title"], "三审现实映射初稿（结合 user.md / tcmreviewer.md / aireviewer.md）"])
        for c in ws[2]:
            c.font = Font(bold=True)
        for i, (mod, content) in enumerate(rs["rows"], 1):
            ws.append([i, mod, content])
        style_sheet(ws, len(rs["rows"]))

    wb.save(OUT)
    n_p1 = sum(1 for ch in CHAPTERS for m, _ in ch["rows"] if m.startswith("[Part1"))
    n_p2 = sum(1 for ch in CHAPTERS for m, _ in ch["rows"] if m.startswith("[Part2"))
    chars = sum(len(c) for ch in CHAPTERS for _, c in ch["rows"])
    print(f"✅ 已生成: {OUT}")
    print(f"   Sheets: {len(wb.sheetnames)} = RL01-RL10(10) + 编程指导 + 审校占位")
    print(f"   十章正文: Part1 {n_p1} 节 + Part2 {n_p2} 节，总字数约 {chars//1000}K 字")


if __name__ == "__main__":
    main()
