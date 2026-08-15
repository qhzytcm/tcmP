# -*- coding: utf-8 -*-
"""cmrl_build_toc2.py — 生成 v2 目录（三编：提高认知·确认信仰·追求幸福）

产出:
  1. drafts/cmrl/toc_v2/ 下: 00-总纲.md + ch01~ch10_toc.md（章/节/小节/段落四级）
  2. 更新桌面 xlsx 的 0cmrl目录 sheet（保留前 5 行映射说明，替换目录行为 v2）

用法: python scripts/cmrl_build_toc2.py [--no-xlsx]
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from cmrl_toc_v2 import VOLUMES, CHAPTERS_V2, CHAP_WORDS, SEC_WORDS  # noqa: E402

DRAFTS = Path(r'C:\Users\DELL\textbook-project\drafts\cmrl')
TOC2 = DRAFTS / 'toc_v2'
XLSX = Path(r'C:\Users\DELL\Desktop\强化学习的数学原理-赵世钰.xlsx')


def sub_sections(sec_title: str, sec_words: int):
    """每节生成 3 小节（知识要点/方法与示例/小结与衔接），各 sec_words/3 字"""
    w = sec_words // 3
    return [("知识要点", w), ("方法与示例", w), ("小结与衔接", w)]


def chapter_lines(ch):
    n, sheet, title, src, anchor, secs = ch
    lines = [f"# 第{n}章 {title}  预算 {CHAP_WORDS} 字",
             f"  内容映射: {src}",
             f"  哲学锚点: {anchor}"]
    for i, sec in enumerate(secs, 1):
        lines.append(f"## {n}.{i} {sec}  ({SEC_WORDS}字)")
        for j, (sub, w) in enumerate(sub_sections(sec, SEC_WORDS), 1):
            lines.append(f"### {n}.{i}.{j} {sub}  ({w}字)")
            for k in (1, 2):
                lines.append(f"  - {n}.{i}.{j}.{k} 段落{k}  (500字)")
    return lines


def build_md():
    TOC2.mkdir(parents=True, exist_ok=True)
    # 总纲
    g = ["# 中医场景「强化学习」正文目录 v2 —— 提高认知 · 确认信仰 · 追求幸福", ""]
    for vol, name, desc in VOLUMES:
        g.append(f"## {vol} {name}")
        g.append(f"> {desc}")
        for ch in CHAPTERS_V2:
            if (vol == "上编" and ch[0] <= 3) or (vol == "中编" and 4 <= ch[0] <= 6) \
               or (vol == "下编" and ch[0] >= 7):
                g.append(f"- 第{ch[0]}章 {ch[2]}（{ch[3]}）")
        g.append("")
    g.append("## 结语：最适度而非最优化")
    g.append("> 四个最适度（生理/心理/社会/环境潜能）绝非最优化——"
             "最优化的极端破坏尺度伸缩的整体潜能。全书以约束、正则、熵、信赖域等"
             "数学工具落实「适度」哲学（对应第7章奖励设计、第10章稳健更新）。")
    (TOC2 / '00-总纲.md').write_text('\n'.join(g), encoding='utf-8')
    print(f'[md] {TOC2 / "00-总纲.md"} ({len(g)} 行)')
    # 各章
    for ch in CHAPTERS_V2:
        lines = chapter_lines(ch)
        f = TOC2 / f'ch{ch[0]:02d}_toc.md'
        f.write_text('\n'.join(lines) + '\n', encoding='utf-8')
        print(f'[md] {f.name} ({len(lines)} 行)')


def reviewer_cols(lvl: str, title: str):
    """三审列: 章/系统定位/和谐共同体/小结=主编主责;
    含四诊/辨证/方剂/疗效/健康/医患/信仰/幸福/适度=中医药主审; 其余=智能主审"""
    if lvl == '章' or any(k in title for k in ('系统', '定位', '和谐', '共同体', '愿景', '小结')):
        return ('✓', '○', '○')
    if any(k in title for k in ('四诊', '辨证', '方剂', '疗效', '证候', '健康', '医患',
                                '治未病', '传变', '望闻问切', '信仰', '幸福', '适度',
                                '循证', '审方', '药')):
        return ('○', '✓', '○')
    return ('○', '○', '✓')


def update_xlsx():
    from openpyxl import load_workbook
    from openpyxl.styles import Alignment, PatternFill, Font
    wb = load_workbook(XLSX)
    ws = wb['0cmrl目录']
    # 保留前 5 行（映射说明+篇幅预算），删除第 6 行起的旧目录
    if ws.max_row > 5:
        ws.delete_rows(6, ws.max_row - 5)
    lv_fill = {'章': '4472C4', '节': 'DDEBF7', '小节': 'E2EFDA'}
    for ch in CHAPTERS_V2:
        n, sheet, title, src, anchor, secs = ch
        e, t, a = reviewer_cols('章', title)
        ws.append(['章', f'第{n}章', title,
                   f'内容映射:{src}；{anchor}', CHAP_WORDS, e, t, a,
                   '三编：提高认知·确认信仰·追求幸福'])
        r = ws.max_row
        ws.cell(r, 1).fill = PatternFill('solid', fgColor=lv_fill['章'])
        ws.cell(r, 1).font = Font(bold=True)
        for i, sec in enumerate(secs, 1):
            is_harmony = i == 8  # 第8节: 六者和谐与共同体（tcmP 平台一句带过）
            e, t, a = reviewer_cols('节', sec)
            note = '科普语言讲解（RL 理论方法不变）' if i <= 6 else (
                '分布式系统科学视角：个人定位+场景生存最适度+环境共荣最适度' if i == 7 else
                '六者和谐·和谐社会·人类命运共同体；tcmP 教育平台一句话带过')
            ws.append(['节', f'{n}.{i}', sec, note,
                       SEC_WORDS, e, t, a, ''])
            ws.cell(ws.max_row, 1).fill = PatternFill('solid', fgColor=lv_fill['节'])
            for j, (sub, w) in enumerate(sub_sections(sec, SEC_WORDS), 1):
                e, t, a = reviewer_cols('小节', sub)
                ws.append(['小节', f'{n}.{i}.{j}', f'{sec[:8]}·{sub}',
                           sub, w, e, t, a, ''])
                ws.cell(ws.max_row, 1).fill = PatternFill('solid', fgColor=lv_fill['小节'])
    for col, width in zip('ABCDEFGHI', (8, 12, 34, 46, 10, 12, 14, 12, 40)):
        ws.column_dimensions[col].width = width
    for r in range(6, ws.max_row + 1):
        ws.cell(r, 4).alignment = Alignment(wrap_text=True, vertical='top')
    wb.save(XLSX)
    print(f'[xlsx] 0cmrl目录 已替换为 v2 目录（{ws.max_row} 行）')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--no-xlsx', action='store_true')
    args = ap.parse_args()
    build_md()
    if not args.no_xlsx:
        update_xlsx()
