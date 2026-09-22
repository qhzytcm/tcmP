# -*- coding: utf-8 -*-
"""cmrl_merge.py — cmrl 分节 Markdown 正文 → 章节数据 / Excel 合并管线

分节文件约定（drafts/cmrl/ch{NN}/）：
  00-intro.md      章引言（~1500 字）
  01-1.1.md ~ 06-*.md   知识节（每节 ~3000 字，Part1 忠实正文 + Part2 平台改写）
  07-平台实践.md    平台实践与实训（~2400 字）
  08-语境职业.md    中医药语境 + 职业应用（~2500 字）
  09-小结.md        章末小结与习题（~1500 字）

md 内部格式：
  ## [Part1] 1.1 智能体与环境：网格世界
  正文段落……（一段一自然段，多段不限）
  ## [Part2] 1.1 平台语境改写
  正文段落……

用法：
  python scripts/cmrl_merge.py --ch 1          # 合并第1章 md → rl_v6_ch01.py
  python scripts/cmrl_merge.py --all           # 合并全部已有章节
  python scripts/cmrl_merge.py --ch 1 --xlsx   # 合并并生成/更新桌面 Excel
"""
import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from gen_rl_notes_xlsx import CHAPTERS as V3_CHAPTERS, SHEET_NAMES  # noqa: E402

DRAFTS = Path(r'C:\Users\DELL\textbook-project\drafts\cmrl')
OUT_SCRIPTS = Path(r'C:\Users\DELL\textbook-project\scripts')
OUT = Path(r'C:\Users\DELL\Desktop\强化学习的数学原理-赵世钰.xlsx')

CHAP_META = {
    1: ("RL01", "1cmrl-conceptions", "第1章 基本概念（Basic Concepts）"),
    2: ("RL02", "2cmrl-bellman", "第2章 状态价值与贝尔曼方程（State Values and Bellman Equation）"),
    3: ("RL03", "3cmrl-optimality", "第3章 最优状态价值与贝尔曼最优方程（Optimal State Values and Bellman Optimality Equation）"),
    4: ("RL04", "4cmrl-iteration", "第4章 价值迭代与策略迭代（Value Iteration and Policy Iteration）"),
    5: ("RL05", "5cmrl-montecarlo", "第5章 蒙特卡洛方法（Monte Carlo Methods）"),
    6: ("RL06", "6cmrl-approximation", "第6章 随机逼近（Stochastic Approximation）"),
    7: ("RL07", "7cmrl-tdlearning", "第7章 时序差分方法（Temporal-Difference Methods）"),
    8: ("RL08", "8cmrl-valuefunction", "第8章 价值函数方法（Value Function Approximation）"),
    9: ("RL09", "9cmrl-policygradient", "第9章 策略梯度方法（Policy Gradient Methods）"),
    10: ("RL10", "10cmrl-acloop", "第10章 Actor-Critic 方法（Actor-Critic Methods）"),
}


def parse_md(text: str):
    """解析 md → [(mod, content), ...]；mod 为 '## 标题' 文本（无标记前缀）
    '##' 为分节标记；'###' 及更深标题行忽略(子标题不进入正文)"""
    rows = []
    cur_mod = None
    buf = []
    for line in text.splitlines():
        s = line.strip()
        m = re.match(r'^##\s+(.+)$', s)
        if m:
            if cur_mod and buf:
                rows.append((cur_mod, '\n'.join(buf).strip()))
            cur_mod = m.group(1).strip()
            buf = []
        elif s.startswith('#') or not s:
            continue
        elif s.startswith('**图') or s.startswith('![') \
                or s.startswith('图注：') or s.startswith('【图'):
            continue   # 图块行（图题/图体/图注）不进入正文（兼容 **图 与 **图7 无空格）
        else:
            buf.append(s)
    if cur_mod and buf:
        rows.append((cur_mod, '\n'.join(buf).strip()))
    return rows


def split_paragraphs(rows):
    """把 (mod, content) 中 content 按段落拆分为多行（每行一段，同 mod）"""
    out = []
    for mod, content in rows:
        for seg in content.split('\n'):
            seg = seg.strip()
            if seg:
                out.append((mod, seg))
    return out


def merge_chapter(ch: int, write_py: bool = True):
    d = DRAFTS / f'ch{ch:02d}'
    if not d.exists():
        print(f'[skip] ch{ch:02d} 目录不存在: {d}')
        return None
    md_files = sorted(f for f in d.glob('*.md') if not f.name.startswith('chapter-'))
    if not md_files:
        print(f'[skip] ch{ch:02d} 无 md 分节文件')
        return None
    all_rows = []
    for f in md_files:
        rows = parse_md(f.read_text(encoding='utf-8'))
        if not rows:
            print(f'[warn] {f.name} 解析出 0 行')
        all_rows.extend(rows)
    total = sum(len(r[1]) for r in all_rows)
    prefix, sheet, title = CHAP_META[ch]
    print(f'[ok] ch{ch:02d} {sheet}: {len(all_rows)} 段, {total} 字 (目标 30000)')
    if write_py:
        lines = [
            '# -*- coding: utf-8 -*-',
            f'"""rl_v6_ch{ch:02d}.py — {title} 正文（cmrl_merge 自动生成）"""',
            'from __future__ import annotations',
            '',
            f'CHAPTER = {{',
            f' "sheet": "{sheet}",',
            f' "title": "{title}",',
            ' "rows": [',
        ]
        for mod, content in all_rows:
            c = content.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
            lines.append(f'  ("{mod}", "{c}"),')
        lines.append(' ],')
        lines.append('}')
        lines.append('')
        out = OUT_SCRIPTS / f'rl_v6_ch{ch:02d}.py'
        out.write_text('\n'.join(lines), encoding='utf-8')
        print(f'[write] {out}')
    return {'prefix': prefix, 'sheet': sheet, 'title': title, 'rows': all_rows, 'words': total}


def build_all():
    chapters = []
    for ch in range(1, 11):
        r = merge_chapter(ch, write_py=False)
        if r:
            chapters.append({'sheet': r['sheet'], 'title': r['title'], 'rows': r['rows']})
    return chapters


def to_xlsx(chapters):
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill
    wb = Workbook()
    wb.remove(wb.active)
    # 目录 sheet（复用 v4 toc + 三审映射）
    from rl_v4_toc import toc_rows  # noqa: E402
    ws = wb.create_sheet(title='0cmrl目录')
    ws.append(['层级', '四级编码', '标题', '内容定位', '预计字数',
               '主编(user.md)', '中医药主审(tcmreviewer.md)', '智能主审(aireviewer.md)', '双目标/职业标注'])
    for c in ws[1]:
        c.font = Font(bold=True, color='FFFFFF')
        c.fill = PatternFill('solid', fgColor='4472C4')
    ws.freeze_panes = 'A2'
    for row in toc_rows():
        ws.append(list(row))
    for col, width in zip('ABCDEFGHI', (8, 12, 30, 46, 10, 12, 14, 12, 40)):
        ws.column_dimensions[col].width = width
    # 章节 sheets
    p1_fill = PatternFill('solid', fgColor='DDEBF7')
    p2_fill = PatternFill('solid', fgColor='E2EFDA')
    for ch in chapters:
        ws = wb.create_sheet(title=ch['sheet'])
        ws.append(['序号', '模块', '内容'])
        ws.append(['章', ch['title'],
                   '《Mathematical Foundation of Reinforcement Learning》赵世钰 (Shiyu Zhao), Springer'])
        for i, (mod, content) in enumerate(ch['rows'], 1):
            ws.append([i, mod, content])
        for r in range(3, ws.max_row + 1):
            mod = ws.cell(r, 2).value or ''
            ws.cell(r, 2).fill = p1_fill if mod.startswith('[Part1') else p2_fill
            ws.cell(r, 3).alignment = Alignment(wrap_text=True, vertical='top')
        ws.freeze_panes = 'A2'
        ws.column_dimensions['A'].width = 6
        ws.column_dimensions['B'].width = 30
        ws.column_dimensions['C'].width = 115
    out = OUT
    wb.save(out)
    total = sum(len(r[1]) for ch in chapters for r in ch['rows'])
    print(f'[xlsx] {out}  ({len(chapters)} 章, {total} 字)')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--ch', type=int, help='合并单章 (1-10)')
    ap.add_argument('--all', action='store_true', help='合并全部已有章节')
    ap.add_argument('--xlsx', action='store_true', help='合并后生成桌面 Excel')
    args = ap.parse_args()
    if args.xlsx:
        chapters = build_all()
        to_xlsx(chapters)
    elif args.ch:
        merge_chapter(args.ch)
    elif args.all:
        build_all()
    else:
        ap.print_help()
