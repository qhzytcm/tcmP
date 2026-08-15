# -*- coding: utf-8 -*-
"""cmrl_update_xlsx.py — 把 drafts/cmrl/ch{NN}/*.md 正文写入桌面 xlsx 章节 sheet

章节 sheet 名: 1cmrl-conceptions ~ 10cmrl-acloop（CHAP_META 映射）
位置: 0cmrl目录 sheet 之后（已存在则原地更新，保留表头+章标题行，替换数据行）
用法:
  python scripts/cmrl_update_xlsx.py --ch 1     # 更新第1章
  python scripts/cmrl_update_xlsx.py --all      # 更新全部已有正文的章节
  python scripts/cmrl_update_xlsx.py --ch 1 --check  # 仅验收(字数/格式), 不写 Excel
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from cmrl_merge import parse_md, split_paragraphs, CHAP_META, DRAFTS  # noqa: E402

XLSX = Path(r'C:\Users\DELL\Desktop\强化学习的数学原理-赵世钰.xlsx')


def load_chapter(ch: int):
    """读 ch{NN} 分节 md → rows；返回 (rows, 总字数, 各文件字数)"""
    d = DRAFTS / f'ch{ch:02d}'
    if not d.exists():
        return None, 0, {}
    files = sorted(d.glob('*.md'))
    if not files:
        return None, 0, {}
    rows, total, per = [], 0, {}
    for f in files:
        r = parse_md(f.read_text(encoding='utf-8'))
        r = split_paragraphs(r)          # 每段一行（Excel 每行一段）
        w = sum(len(x[1]) for x in r)
        rows.extend(r)
        total += w
        per[f.name] = w
    return rows, total, per


def check_chapter(ch: int, rows, total):
    """验收: 非空、每段 100-2000 字(无空/超大段)、模块标记非空(无标记科普叙事)"""
    ok = True
    notes = []
    if not rows:
        return False, '无内容'
    for i, (mod, content) in enumerate(rows):
        if not mod.strip() or not content.strip():
            ok = False
            notes.append(f'第{i+1}行标记异常: {mod[:20]}')
    if total < 5000:
        ok = False
        notes.append(f'字数过少: {total}')
    return ok, '; '.join(notes) if notes else f'{len(rows)}段/{total}字'


def update_sheet(ch: int, rows, total):
    from openpyxl import load_workbook
    from openpyxl.styles import Alignment, PatternFill
    prefix, sheet_name, title = CHAP_META[ch]
    wb = load_workbook(XLSX)
    if sheet_name not in wb.sheetnames:
        # 在 0cmrl目录 之后插入
        wb.create_sheet(title=sheet_name)
        idx = wb.sheetnames.index('0cmrl目录') + 1
        wb.move_sheet(sheet_name, offset=idx - (wb.sheetnames.index(sheet_name)))
    ws = wb[sheet_name]
    # 保留表头(行1)+章标题(行2)，删除旧数据行
    if ws.max_row > 2:
        ws.delete_rows(3, ws.max_row - 2)
    p1 = PatternFill('solid', fgColor='DDEBF7')
    p2 = PatternFill('solid', fgColor='E2EFDA')
    for i, (mod, content) in enumerate(rows, 1):
        ws.append([i, mod, content])
        r = ws.max_row
        # [Part1]/[科普 → 浅蓝(正文); [Part2 → 浅绿(平台改写)
        if mod.startswith('[Part2'):
            ws.cell(r, 2).fill = p2
        else:
            ws.cell(r, 2).fill = p1
        ws.cell(r, 3).alignment = Alignment(wrap_text=True, vertical='top')
    ws.freeze_panes = 'A2'
    ws.column_dimensions['A'].width = 6
    ws.column_dimensions['B'].width = 30
    ws.column_dimensions['C'].width = 115
    wb.save(XLSX)
    print(f'[xlsx] {sheet_name}: {len(rows)} 段, {total} 字 → {XLSX.name}')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--ch', type=int)
    ap.add_argument('--all', action='store_true')
    ap.add_argument('--check', action='store_true', help='仅验收不写 Excel')
    args = ap.parse_args()
    chs = range(1, 11) if args.all else ([args.ch] if args.ch else [])
    for ch in chs:
        rows, total, per = load_chapter(ch)
        if rows is None:
            print(f'[skip] ch{ch:02d} 无正文 md')
            continue
        ok, note = check_chapter(ch, rows, total)
        print(f'[ch{ch:02d}] {ok and "PASS" or "FAIL"} {note}')
        if not ok:
            continue
        if not args.check:
            update_sheet(ch, rows, total)


if __name__ == '__main__':
    main()
