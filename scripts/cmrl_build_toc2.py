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
from cmrl_toc_v2 import VOLUMES, CHAPTERS_V2, CHAP_WORDS, SEC_WORDS, SUB_WORDS, PARA_WORDS  # noqa: E402

DRAFTS = Path(r'C:\Users\DELL\textbook-project\drafts\cmrl')
TOC2 = DRAFTS / 'toc_v2'
XLSX = Path(r'C:\Users\DELL\Desktop\强化学习的数学原理-赵世钰.xlsx')


def wrange(x: int) -> str:
    """字数区间: X → 0.8X-1.2X"""
    return f'{int(x * 0.8)}-{int(x * 1.2)}'


def sub_sections(sec_title: str, sec_words: int):
    """每节 3 小节: 明确具体概念/方法（主概念派生），各 sec_words/3 字"""
    main = sec_title.split('：')[0] if '：' in sec_title else sec_title
    w = sec_words // 3
    return [(f'{main}：概念与内涵', w),
            (f'{main}：方法与实现', w),
            (f'{main}：小结与衔接', w)]


def chapter_lines(ch):
    """每章生成 Markdown 四列表格（章|节|小节|段落 各存纯数字，标题|预计字数）"""
    n, sheet, title, src, anchor, secs = ch
    lines = [f'# 第{n}章 {title}（预算 {wrange(CHAP_WORDS)} 字）',
             f'> 内容映射：{src}；{anchor}',
             '',
             '| 章 | 节 | 小节 | 段落 | 标题 | 预计字数 |',
             '|---|---|---|---|---|---|']
    lines.append(f'| {n} | | | | {title} | {wrange(CHAP_WORDS)} |')
    for i, sec in enumerate(secs, 1):
        lines.append(f'| {n} | {i} | | | {sec} | {wrange(SEC_WORDS)} |')
        for j, (sub, w) in enumerate(sub_sections(sec, SEC_WORDS), 1):
            lines.append(f'| {n} | {i} | {j} | | {sub} | {wrange(SUB_WORDS)} |')
            for k in (1, 2):
                lines.append(f'| {n} | {i} | {j} | {k} | '
                             f'段落{k} | {wrange(PARA_WORDS)} |')
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
    """重建 0cmrl目录 sheet: 四级编码分列（章/节/小节/段落各一列）"""
    from openpyxl import load_workbook
    from openpyxl.styles import Alignment, PatternFill, Font
    wb = load_workbook(XLSX)
    ws = wb['0cmrl目录']
    if ws.max_row > 0:
        ws.delete_rows(1, ws.max_row)
    # 表头: 四级编码分列
    headers = ['章', '节', '小节', '段落', '标题', '内容定位', '预计字数',
               '主编(user.md)', '中医药主审(tcmreviewer.md)', '智能主审(aireviewer.md)',
               '双目标/职业标注']
    ws.append(headers)
    for c in ws[1]:
        c.font = Font(bold=True, color='FFFFFF')
        c.fill = PatternFill('solid', fgColor='4472C4')
    ws.freeze_panes = 'A2'
    # 映射说明 3 行 + 篇幅预算 1 行（适配新列: A=说明, E=名称, F=说明, G=专业, H/I/J=三审, K=现实映射）
    mapping_notes = [
        ('0映射1 · user.md', '主编人选初稿：统筹十章结构、双目标（教材+平台）决策、终审定稿',
         '专业能力：全局规划+AI趋势研判', '✓ 主编主责', '○ 协审', '○ 协审',
         '现实映射：主编=项目负责人；每章引言/小结由主编统筹'),
        ('0映射2 · tcmreviewer.md', '中医药主审初稿：辨证准确性/方剂合规/医学术语规范/医案真实性',
         '专业能力：中医药本体+数字化适配', '○ 协审', '✓ 主审主责', '○ 协审',
         '现实映射：中医药专家；辨证/医案/语境小节主审'),
        ('0映射3 · aireviewer.md', '智能主审初稿：数学公式/算法正确性/代码与数据校验/平台接口一致性',
         '专业能力：AI技术+趋势适应（RL前沿）', '○ 协审', '○ 协审', '✓ 主审主责',
         '现实映射：AI 审校（门禁自动化）；数学/算法/接口小节主审'),
    ]
    for note in mapping_notes:
        ws.append(['映射说明', '', '', '', note[0], note[1], note[2],
                   note[3], note[4], note[5], note[6]])
        for c in ws[ws.max_row]:
            c.font = Font(italic=True, color='7F6000')
    ws.append(['篇幅预算', '', '', '', '全书 ≤300,000 字',
               f'每章 {wrange(CHAP_WORDS)}：知识节 {wrange(SEC_WORDS)}×6 + '
               f'系统定位 {wrange(SEC_WORDS)} + 六者和谐 {wrange(SEC_WORDS)}；'
               f'小节 {wrange(SUB_WORDS)}；段落 {wrange(PARA_WORDS)}',
               '—', '—', '—', '—',
               '保障每章正文内容充分展开，10 章合计 30 万字上限'])
    # 目录行: 章/节/小节/段落 分列填充
    lv_fill = {'章': '4472C4', '节': 'DDEBF7', '小节': 'E2EFDA'}
    for ch in CHAPTERS_V2:
        n, sheet, title, src, anchor, secs = ch
        e, t, a = reviewer_cols('章', title)
        ws.append([n, '', '', '', title,
                   f'内容映射:{src}；{anchor}', wrange(CHAP_WORDS), e, t, a,
                   '三编：提高认知·确认信仰·追求幸福'])
        r = ws.max_row
        ws.cell(r, 1).fill = PatternFill('solid', fgColor=lv_fill['章'])
        ws.cell(r, 1).font = Font(bold=True)
        for i, sec in enumerate(secs, 1):
            e, t, a = reviewer_cols('节', sec)
            note = '知识节：概念与方法（举一反三）' if i <= 6 else (
                '分布式系统科学视角：个人定位+场景生存最适度+环境共荣最适度' if i == 7 else
                '六者和谐·和谐社会·人类命运共同体；tcmP 教育平台一句话带过')
            ws.append([n, i, '', '', sec, note,
                       wrange(SEC_WORDS), e, t, a, ''])
            ws.cell(ws.max_row, 2).fill = PatternFill('solid', fgColor=lv_fill['节'])
            for j, (sub, w) in enumerate(sub_sections(sec, SEC_WORDS), 1):
                e, t, a = reviewer_cols('小节', sub)
                ws.append([n, i, j, '', sub,
                           sub, wrange(SUB_WORDS), e, t, a, ''])
                ws.cell(ws.max_row, 3).fill = PatternFill('solid', fgColor=lv_fill['小节'])
                for k in (1, 2):
                    ws.append([n, i, j, k,
                               f'{sub[:8]}·段落{k}', '段落正文',
                               wrange(PARA_WORDS), e, t, a, ''])
    for col, width in zip('ABCDEFGHIJK',
                          (8, 10, 12, 14, 34, 44, 12, 12, 14, 12, 40)):
        ws.column_dimensions[col].width = width
    for r in range(2, ws.max_row + 1):
        ws.cell(r, 6).alignment = Alignment(wrap_text=True, vertical='top')
        ws.cell(r, 11).alignment = Alignment(wrap_text=True, vertical='top')
    wb.save(XLSX)
    print(f'[xlsx] 0cmrl目录 已重建: 四级编码分列（{ws.max_row} 行）')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--no-xlsx', action='store_true')
    args = ap.parse_args()
    build_md()
    if not args.no_xlsx:
        update_xlsx()
