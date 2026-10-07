# -*- coding: utf-8 -*-
"""
GitBook → Excel 转换器（tcmP 平台技能 gitbook-to-excel 的实现）
=====================================================================
把一本 GitBook 结构的 Markdown 书稿（SUMMARY.md + 各章 *.md）转换为
结构化 .xlsx 工作簿：目录结构一个 sheet，每章正文一个 sheet，并附
「正文总表」（章｜节｜类型｜内容）供下游（教材管线 / 评阅 / LLM）消费。

约定
----
book/
  SUMMARY.md        目录结构（GitBook 语法：# 书名 / ## 章 / - [节](file.md)）
  README.md         卷首（可选，作封面正文）
  01-xxx.md ...     各章 Markdown（各级标题 = 节/小节；``` 代码块 = 代码；
                    | 表格保留；其余段落 = 正文）
用法
----
  python gitbook_to_excel.py --book <book_dir> --out <out.xlsx> [--title 书名]
  # 作为库：from gitbook_to_excel import write_book; write_book(wb, book_dir, meta)
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

INDIGO, INDIGO_L, GOLD, GRAY_L, WHITE = "1F3A5F", "D6E4F0", "C9A227", "F2F2F2", "FFFFFF"
GREEN_L, BLUE_L, ORANGE_L, PURPLE_L = "E2EFDA", "DDEBF7", "FCE4D6", "E4DFEC"

F_TITLE = Font(name="微软雅黑", size=15, bold=True, color=WHITE)
F_H1 = Font(name="微软雅黑", size=12, bold=True, color=INDIGO)
F_H2 = Font(name="微软雅黑", size=10.5, bold=True, color=INDIGO)
F_BODY = Font(name="微软雅黑", size=10, color="333333")
F_BODY_B = Font(name="微软雅黑", size=10, bold=True, color="333333")
F_CODE = Font(name="Consolas", size=9.5, color="1B5E20")
F_SMALL = Font(name="微软雅黑", size=9, color="666666")
THIN = Side(style="thin", color="BBBBBB")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
AL_L = Alignment(horizontal="left", vertical="top", wrap_text=True)
AL_C = Alignment(horizontal="center", vertical="center", wrap_text=True)


def pf(c):
    if not c:
        return None
    return PatternFill(patternType="solid", fgColor=c)


# ── 解析 ──────────────────────────────────────────────────────────
SUM_H2 = re.compile(r"^##\s+(.+?)\s*$")
SUM_LINK = re.compile(r"^\s*-\s*\[(.+?)\]\((.+?)\)\s*$")
H_RE = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")


def parse_summary(path: Path):
    """返回 outline = [(part_title, [(chap_title, chap_file)]), ...]"""
    title, outline, cur_part = path.stem, [], None
    for ln in path.read_text(encoding="utf-8").splitlines():
        if ln.startswith("# ") and not ln.startswith("## "):
            title = ln[2:].strip()
            continue
        m = SUM_H2.match(ln)
        if m:
            cur_part = (m.group(1), [])
            outline.append(cur_part)
            continue
        m = SUM_LINK.match(ln)
        if m:
            entry = (m.group(1).strip(), m.group(2).strip())
            if cur_part is None:
                cur_part = ("正文", [])
                outline.append(cur_part)
            cur_part[1].append(entry)
    return title, outline


def parse_chapter(path: Path):
    """把一章 md 解析为 blocks：('h',level,text) / ('p',text) / ('code',lang,text) / ('table',text)"""
    blocks, buf, in_code, code_lang, code_buf, table_buf = [], [], False, "", [], []
    for raw in path.read_text(encoding="utf-8").splitlines():
        if raw.strip().startswith("```"):
            if not in_code:
                in_code, code_lang, code_buf = True, raw.strip()[3:].strip(), []
            else:
                blocks.append(("code", code_lang, "\n".join(code_buf)))
                in_code = False
            continue
        if in_code:
            code_buf.append(raw)
            continue
        if raw.strip().startswith("|"):
            table_buf.append(raw)
            continue
        elif table_buf:
            blocks.append(("table", "", "\n".join(table_buf)))
            table_buf = []
        hm = H_RE.match(raw)
        if hm:
            if buf:
                blocks.append(("p", "", " ".join(buf).strip()))
                buf = []
            blocks.append(("h", len(hm.group(1)), hm.group(2)))
            continue
        if raw.strip() == "":
            if buf:
                blocks.append(("p", "", " ".join(buf).strip()))
                buf = []
            continue
        buf.append(raw.strip())
    if table_buf:
        blocks.append(("table", "", "\n".join(table_buf)))
    if buf:
        blocks.append(("p", "", " ".join(buf).strip()))
    return blocks


def flatten_blocks(blocks):
    """把 code/table 块拆成逐行原子块，避免「超长多行单元格」在反复保存时被 openpyxl 截断。"""
    out = []
    for b in blocks:
        if b[0] in ("code", "table"):
            for ln in b[2].split("\n"):
                out.append((b[0], b[1], ln))
        else:
            out.append(b)
    return out


class SW:
    """极简 sheet 写入器（与 gen_knowledge_tree_xlsx 风格一致）。"""

    def __init__(self, ws, widths):
        self.ws, self.r = ws, 1
        for i, w in enumerate(widths, 1):
            ws.column_dimensions[get_column_letter(i)].width = w

    def row(self, cells, fill=None, font=None, align=None, h=None):
        for ci, v in enumerate(cells, 1):
            c = self.ws.cell(self.r, ci, v)
            c.border = BORDER
            c.font = (font[ci - 1] if isinstance(font, (list, tuple)) and ci - 1 < len(font)
                      else (font[-1] if isinstance(font, (list, tuple)) and font else font)) or F_BODY
            c.alignment = (align[ci - 1] if isinstance(align, (list, tuple)) and ci - 1 < len(align)
                           else (align[-1] if isinstance(align, (list, tuple)) and align else align)) or AL_L
            f = fill[ci - 1] if isinstance(fill, (list, tuple)) and ci - 1 < len(fill) else fill
            if f:
                c.fill = f
        if h:
            self.ws.row_dimensions[self.r].height = h
        self.r += 1

    def title(self, text, span):
        self.row([text] + [""] * (span - 1), pf(INDIGO), F_TITLE, AL_C, 28)
        self.ws.merge_cells(start_row=self.r - 1, start_column=1, end_row=self.r - 1, end_column=span)

    def section(self, text, span, fill=INDIGO_L):
        self.row([text] + [""] * (span - 1), pf(fill) if fill else None, F_H1, AL_L, 20)
        self.ws.merge_cells(start_row=self.r - 1, start_column=1, end_row=self.r - 1, end_column=span)

    def head(self, cells):
        self.row(cells, pf(INDIGO_L), F_BODY_B, AL_C, 18)


def sanitize(name: str, used: set) -> str:
    s = re.sub(r"[\\/*?:\[\]]", "_", name)[:28] or "sheet"
    base, i = s, 1
    while s in used:
        s = f"{base[:24]}-{i}"
        i += 1
    used.add(s)
    return s


def write_book(wb: Workbook, book_dir: Path, meta: dict, used_names=None):
    """把一本 GitBook 写入工作簿：0封面 / 0目录 / 0正文总表 / 每章一个 sheet。返回摘要 dict。"""
    book_dir = Path(book_dir)
    used = used_names if used_names is not None else set(wb.sheetnames)
    title, outline = parse_summary(book_dir / "SUMMARY.md")
    title = meta.get("title") or title

    # 扁平化章列表
    chapters = [(part, ct, cf) for part, chs in outline for ct, cf in chs]
    files = {cf for _, _, cf in chapters}

    # ── 0封面 ──
    ws = wb.create_sheet(sanitize("0封面", used))
    sw = SW(ws, [18, 92])
    sw.title(f"《{title}》· 教材正文（GitBook → Excel）", 2)
    sw.section("【教材元数据卡】", 2, GREEN_L)
    for k, v in meta.get("meta", {}).items():
        sw.row([k, v], [pf(BLUE_L), None], [F_BODY_B, F_BODY], [AL_C, AL_L],
               max(18, 14 * (len(str(v)) // 44 + 1)))
    if meta.get("notes"):
        sw.section(meta.get("notes_title", "【说明】"), 2, ORANGE_L)
        for t in meta["notes"]:
            sw.row([t, ""], [None, None], [F_BODY, F_BODY], [AL_L, AL_L],
                   max(16, 13 * (len(t) // 44 + 1) + 3))
            ws.merge_cells(start_row=sw.r - 1, start_column=1, end_row=sw.r - 1, end_column=2)
    readme = book_dir / "README.md"
    if readme.exists():
        sw.section("【卷首 · README】", 2, PURPLE_L)
        for b in parse_chapter(readme):
            txt = b[2] if b[0] != "p" else b[2]
            sw.row([{"h": "标题", "p": "正文", "code": "代码", "table": "表格"}[b[0]], txt],
                   [pf(GRAY_L), None], [F_BODY_B, F_CODE if b[0] == "code" else F_BODY], [AL_C, AL_L],
                   max(16, 14 * (len(txt) // 44 + 1)))

    # ── 0目录 ──
    ws = wb.create_sheet(sanitize("0目录", used))
    sw = SW(ws, [10, 50, 26, 8])
    sw.title(f"《{title}》目录结构（{len(outline)} 篇 · {len(chapters)} 章）", 4)
    sw.head(["层级", "标题", "文件", "节数"])
    for part, chs in outline:
        sw.row(["篇", part, "", ""], [pf(INDIGO_L)] * 4, F_BODY_B, [AL_C, AL_L, AL_C, AL_C], 18)
        for ct, cf in chs:
            nsec = sum(1 for b in parse_chapter(book_dir / cf) if b[0] == "h" and b[1] == 2)
            sw.row(["章", ct, cf, nsec], [None] * 4, F_BODY, [AL_C, AL_L, AL_L, AL_C], 16)

    # ── 0正文总表 ──
    ws = wb.create_sheet(sanitize("0正文总表", used))
    sw = SW(ws, [16, 40, 10, 80])
    sw.title("正文总表（章 ｜ 层级 ｜ 类型 ｜ 内容）—— 供教材管线 / 评阅 / LLM 消费", 4)
    sw.head(["章", "标题/位置", "类型", "内容"])
    total_blocks = 0
    for part, ct, cf in chapters:
        p = book_dir / cf
        if not p.exists():
            continue
        for b in flatten_blocks(parse_chapter(p)):
            kind = {"h": "标题", "p": "正文", "code": "代码", "table": "表格"}[b[0]]
            label = b[2] if b[0] == "h" else ""
            text = b[2]
            sw.row([ct, label, kind, text], [None] * 4,
                   [F_BODY, F_BODY_B if b[0] == "h" else F_BODY,
                    F_SMALL, F_CODE if b[0] == "code" else F_BODY],
                   [AL_C, AL_L, AL_C, AL_L], max(15, 13 * (len(text) // 80 + 1)))
            total_blocks += 1

    # ── 每章一个 sheet ──
    for part, ct, cf in chapters:
        p = book_dir / cf
        if not p.exists():
            continue
        ws = wb.create_sheet(sanitize(ct, used))
        sw = SW(ws, [12, 96])
        sw.title(f"{ct}  ·  {part}", 2)
        for b in flatten_blocks(parse_chapter(p)):
            if b[0] == "h":
                lvl = "章" if b[1] == 1 else ("节" if b[1] == 2 else "小节")
                fill = {"章": INDIGO_L, "节": GRAY_L, "小节": PURPLE_L}[lvl]
                sw.row([lvl, b[2]], [pf(fill), None],
                       [F_BODY_B, F_H2 if b[1] <= 2 else F_BODY], [AL_C, AL_L], 18)
            elif b[0] == "code":
                sw.row(["代码", b[2]], [pf(GREEN_L), None], [F_SMALL, F_CODE],
                       [AL_C, AL_L], max(15, 13 * (len(b[2]) // 96 + 1) + 4))
            elif b[0] == "table":
                sw.row(["表格", b[2]], [pf(ORANGE_L), None], [F_SMALL, F_BODY],
                       [AL_C, AL_L], max(15, 13 * (len(b[2]) // 96 + 1) + 4))
            else:
                sw.row(["正文", b[2]], [None, None], [F_SMALL, F_BODY], [AL_C, AL_L],
                       max(15, 13 * (len(b[2]) // 44 + 1) + 3))

    return {"title": title, "parts": len(outline), "chapters": len(chapters),
            "blocks": total_blocks, "files": sorted(files)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--book", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--title", default=None)
    args = ap.parse_args()
    wb = Workbook()
    wb.remove(wb.active)
    summary = write_book(wb, Path(args.book), {"title": args.title, "meta": {}})
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    wb.save(args.out)
    print("saved:", args.out)
    print("sheets:", wb.sheetnames)
    print("summary:", summary)


if __name__ == "__main__":
    main()
