# -*- coding: utf-8 -*-
"""cmrl_review_view.py — 审核目录（Markdown 四列表格：章|节|小节|段落）"""
import sys
from pathlib import Path

sys.path.insert(0, r'C:\Users\DELL\textbook-project\scripts')
from cmrl_toc_v2 import VOLUMES, CHAPTERS_V2  # noqa: E402


def wrange(x):
    return f'{int(x * 0.8)}-{int(x * 1.2)}'


OUT = Path(r'C:\Users\DELL\textbook-project\drafts\cmrl\toc_v2\00-审核目录.md')
lines = ['# 中医场景「强化学习」正文四级编码目录（审核版 v6·四列）',
         '',
         '> 三编 × 10 章 × 8 节 × 3 小节 × 2 段落；四级编码分列（章/节/小节/段落），'
         '字数均为区间 [0.8X-1.2X]。',
         '> 数学基础为强化学习题中之义；术语尽量中文，面对读者不作技术抽象。',
         '> 审核通过后由 Hermes-Agent 编写正文。',
         '']
for vol, name, desc in VOLUMES:
    lines.append(f'## {vol} {name}')
    lines.append(f'> {desc}')
    for ch in CHAPTERS_V2:
        in_vol = (vol == "上编" and ch[0] <= 3) or (vol == "中编" and 4 <= ch[0] <= 6) \
            or (vol == "下编" and ch[0] >= 7)
        if not in_vol:
            continue
        n, sheet, title, src, anchor, secs = ch
        lines.append('')
        lines.append(f'### 第{n}章 {title}（{src}；预算 {wrange(30000)} 字）')
        lines.append('')
        lines.append('| 章 | 节 | 小节 | 段落 | 标题 | 预计字数 |')
        lines.append('|---|---|---|---|---|---|')
        lines.append(f'| {n} | | | | {title} | {wrange(30000)} |')
        for i, sec in enumerate(secs, 1):
            lines.append(f'| {n} | {i} | | | {sec} | {wrange(3000)} |')
            for j, (sub, w) in enumerate(
                    [('概念与内涵', 1000), ('方法与实现', 1000), ('小结与衔接', 1000)], 1):
                lines.append(f'| {n} | {i} | {j} | | '
                             f'{sec.split("：")[0] if "：" in sec else sec}：{sub} | '
                             f'{wrange(1000)} |')
                for k in (1, 2):
                    lines.append(f'| {n} | {i} | {j} | {k} | '
                                 f'段落{k} | {wrange(500)} |')
    lines.append('')
OUT.write_text('\n'.join(lines), encoding='utf-8')
print(f'[write] {OUT} ({len(lines)} 行)')
