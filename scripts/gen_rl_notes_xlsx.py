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
from rl_v2_data import PROGRAMMING_GUIDE, REVIEW_MAPPING  # noqa: E402
from rl_v4_toc import toc_rows      # noqa: E402

CHAPTERS = CHAPTERS_A + CHAPTERS_B + CHAPTERS_C
OUT = Path(r"C:\Users\DELL\Desktop\强化学习的数学原理-赵世钰.xlsx")

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

    # 0) 四级目录（0cmrl目录，置于最前）
    ws = wb.create_sheet(title="0cmrl目录")
    ws.append(["层级", "四级编码", "标题", "内容定位", "双目标标注"])
    for c in ws[1]:
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = HDR_FILL
    ws.freeze_panes = "A2"
    toc = toc_rows()
    lv_fill = {"章": "4472C4", "节": "DDEBF7", "小节": "E2EFDA", "段落": None}
    for lv, code, title, note, tag in toc:
        ws.append([lv, code, title, note, tag])
        r = ws.max_row
        f = lv_fill.get(lv)
        if f:
            ws.cell(r, 1).fill = PatternFill("solid", fgColor=f)
            ws.cell(r, 1).font = Font(bold=True)
        ws.cell(r, 4).alignment = Alignment(wrap_text=True, vertical="top")
        ws.cell(r, 5).alignment = Alignment(wrap_text=True, vertical="top")
    for col, width in zip("ABCDE", (8, 12, 30, 52, 44)):
        ws.column_dimensions[col].width = width

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

    rv = REVIEW_MAPPING
    ws = wb.create_sheet(title=rv["sheet"])
    ws.append(HEADERS)
    ws.append(["映射角色", rv["title"], "由主编确认后补全"])
    for c in ws[2]:
        c.font = Font(bold=True)
    for i, (mod, content) in enumerate(rv["rows"], 1):
        ws.append([i, mod, content])
    style_sheet(ws, len(rv["rows"]))

    wb.save(OUT)
    n_p1 = sum(1 for ch in CHAPTERS for m, _ in ch["rows"] if m.startswith("[Part1"))
    n_p2 = sum(1 for ch in CHAPTERS for m, _ in ch["rows"] if m.startswith("[Part2"))
    chars = sum(len(c) for ch in CHAPTERS for _, c in ch["rows"])
    print(f"✅ 已生成: {OUT}")
    print(f"   Sheets: {len(wb.sheetnames)} = RL01-RL10(10) + 编程指导 + 审校占位")
    print(f"   十章正文: Part1 {n_p1} 节 + Part2 {n_p2} 节，总字数约 {chars//1000}K 字")


if __name__ == "__main__":
    main()
