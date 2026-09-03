# -*- coding: utf-8 -*-
"""cmrl 十章正文完整度审计：rl_v3_a/b/c 各章行数、Part1/Part2 字数统计"""
import sys
from pathlib import Path

HERE = Path(r'C:\Users\DELL\textbook-project\scripts')
sys.path.insert(0, str(HERE))
from rl_v3_a import CHAPTERS_A
from rl_v3_b import CHAPTERS_B
from rl_v3_c import CHAPTERS_C

def audit(chaps, tag):
    total_words = 0
    print(f'===== {tag} ({len(chaps)} 章) =====')
    for ch in chaps:
        sheet = ch['sheet']
        rows = ch['rows']
        p1 = sum(1 for r in rows if r[0].startswith('[Part1]'))
        p2 = sum(1 for r in rows if r[0].startswith('[Part2]'))
        w1 = sum(len(r[1]) for r in rows if r[0].startswith('[Part1]'))
        w2 = sum(len(r[1]) for r in rows if r[0].startswith('[Part2]'))
        total_words += w1 + w2
        empty = sum(1 for r in rows if not r[1].strip())
        print(f'  {sheet:<28} rows={len(rows):<4} P1={p1:<3} P2={p2:<3} w1={w1:<6} w2={w2:<6} empty={empty}')
    print(f'  --- {tag} 合计字数: {total_words}\n')
    return total_words

t = 0
t += audit(CHAPTERS_A, 'CHAPTERS_A (rl_v3_a)')
t += audit(CHAPTERS_B, 'CHAPTERS_B (rl_v3_b)')
t += audit(CHAPTERS_C, 'CHAPTERS_C (rl_v3_c)')
print(f'===== 全书合计字数: {t} =====')
