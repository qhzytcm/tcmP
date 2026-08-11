# -*- coding: utf-8 -*-
"""
gen_rl_notes_xlsx.py — 《强化学习的数学原理-赵世钰》读书笔记生成器（v2）
=====================================================================
参考: 赵世钰(Shiyu Zhao) Mathematical Foundation of Reinforcement Learning
      (Springer, https://github.com/MathFoundationRL/Book-Mathematical-Foundation-of-Reinforcement-Learning)
数据: scripts/rl_v2_data.py（10 章 Part1 老师原文译读 + Part2 hermes 改写；
      另含 tcmP 平台对接编程技术指导 sheet 与审校映射占位 sheet）
输出: 桌面《强化学习的数学原理-赵世钰.xlsx》，12 个 sheet：
      RL01-RL10（每章：Part1 老师原文文字 + Part2 hermes 改写文字）
      + tcmP平台对接编程技术指导 + 审校映射(待补全)

用法: python scripts/gen_rl_notes_xlsx.py
"""
from __future__ import annotations
import sys
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

sys.path.insert(0, str(Path(__file__).parent))
from rl_v2_data import CHAPTERS, PROGRAMMING_GUIDE, REVIEW_MAPPING  # noqa: E402

OUT = Path(r"C:\Users\DELL\Desktop\强化学习的数学原理-赵世钰.xlsx")

# ───────────────── xlsx 生成 ─────────────────
HEADERS = ["序号", "模块", "内容"]
P1_FILL = PatternFill("solid", fgColor="DDEBF7")     # Part1 原文：浅蓝
P2_FILL = PatternFill("solid", fgColor="E2EFDA")     # Part2 改写：浅绿
GUIDE_FILL = PatternFill("solid", fgColor="FCE4D6")  # 编程指导：浅橙
HDR_FILL = PatternFill("solid", fgColor="4472C4")


def style_sheet(ws, n_content_rows: int, guide: bool = False):
    ws.freeze_panes = "A2"
    for c in ws[1]:
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = HDR_FILL
    for r in range(3, 3 + n_content_rows):
        mod = ws.cell(r, 2).value or ""
        fill = P1_FILL if mod.startswith("[Part1") else (
            P2_FILL if mod.startswith("[Part2") else GUIDE_FILL)
        ws.cell(r, 2).fill = fill
        ws.cell(r, 3).alignment = Alignment(wrap_text=True, vertical="top")
    ws.column_dimensions["A"].width = 6
    ws.column_dimensions["B"].width = 26
    ws.column_dimensions["C"].width = 110


def main():
    wb = Workbook()
    wb.remove(wb.active)

    # 1) 十章：RL01-RL10（Part1 老师原文 + Part2 hermes 改写）
    for ch in CHAPTERS:
        ws = wb.create_sheet(title=ch["sheet"])
        ws.append(HEADERS)
        ws.append(["章", ch["title"],
                   "《Mathematical Foundation of Reinforcement Learning》赵世钰 (Shiyu Zhao), Springer"])
        for c in ws[2]:
            c.font = Font(bold=True)
        for i, (mod, content) in enumerate(ch["rows"], 1):
            ws.append([i, mod, content])
        style_sheet(ws, len(ch["rows"]))

    # 2) tcmP 平台对接编程技术指导
    g = PROGRAMMING_GUIDE
    ws = wb.create_sheet(title=g["sheet"])
    ws.append(HEADERS)
    ws.append(["主题", g["title"],
               "与 tcmP 教育平台对接的代码级指导（hermes-generating-content）"])
    for c in ws[2]:
        c.font = Font(bold=True)
    for i, (mod, content) in enumerate(g["rows"], 1):
        ws.append([i, mod, content])
    style_sheet(ws, len(g["rows"]), guide=True)

    # 3) 审校映射占位
    rv = REVIEW_MAPPING
    ws = wb.create_sheet(title=rv["sheet"])
    ws.append(HEADERS)
    ws.append(["映射角色", rv["title"], "由主编确认后补全"])
    for c in ws[2]:
        c.font = Font(bold=True)
    for i, (mod, content) in enumerate(rv["rows"], 1):
        ws.append([i, mod, content])
    style_sheet(ws, len(rv["rows"]), guide=True)

    wb.save(OUT)
    n_p1 = sum(1 for ch in CHAPTERS for m, _ in ch["rows"] if m.startswith("[Part1"))
    n_p2 = sum(1 for ch in CHAPTERS for m, _ in ch["rows"] if m.startswith("[Part2"))
    print(f"✅ 已生成: {OUT}")
    print(f"   Sheets: {len(wb.sheetnames)} = RL01-RL10(10) + 编程指导 + 审校占位")
    print(f"   十章内容: Part1 老师原文 {n_p1} 行 + Part2 hermes 改写 {n_p2} 行"
          f"（共 {n_p1 + n_p2} 行）")
    print(f"   编程指导 {len(g['rows'])} 行 · 审校占位 {len(rv['rows'])} 行")


if __name__ == "__main__":
    main()
