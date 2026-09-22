# -*- coding: utf-8 -*-
"""
S68 目录词典约束的正文病名校正（**确定性**，不依赖 LLM）

判据：**正文病名必须能在目录中找到**（目录=权威词表）。
  · 在词表中 → 一致，不动
  · 不在词表 → 讹形/误识 → 取目录中「编辑距离最近」的名校正（阈值内才改）
免序对齐困扰 —— 只依赖「名集合」而非「名序」。
"""
import os, re, json, sys
from collections import Counter
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, 'dist')
UNITS_F = os.path.join(ROOT, 'data', 'pdf3_units_v2.json')
UNITS = json.load(open(UNITS_F, encoding='utf-8'))
TOC = json.load(open(os.path.join(DIST, 'pdf3_toc_stream.json'), encoding='utf-8'))['pages']


def lev(a, b, cap=3):
    """带上限的编辑距离（超 cap 提前返回 cap+1）"""
    if abs(len(a) - len(b)) > cap:
        return cap + 1
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        if min(cur) > cap:
            return cap + 1
        prev = cur
    return prev[-1]


def main():
    T = ''.join(p['text'].replace('病源辞典', '') for p in TOC)
    # 目录词表：正文名中能在目录串里找到的 → 视为目录认可的「正名」
    names = Counter((u.get('name') or '').strip() for u in UNITS)
    vocab = {n for n in names if len(n) >= 2 and n != '病名待定' and n in T}
    print(f'正文名种类 {len(names)} | 目录认可的正名 {len(vocab)}')

    dubious = [(i, u['name']) for i, u in enumerate(UNITS)
               if u['name'] not in vocab and u['name'] != '病名待定']
    print(f'**不在目录词表中的正文病名**: {len(dubious)} 个')
    prop, unk = [], []
    V = sorted(vocab, key=len)
    for i, n in dubious[:400]:
        best, bd = None, 99
        for v in V:
            if abs(len(v) - len(n)) > 2:
                continue
            d = lev(n, v)
            if d < bd:
                best, bd = v, d
                if bd == 1:
                    break
        if bd <= 1 and best:
            prop.append((i, n, best, bd))
        else:
            unk.append((i, n))
    print(f'  可确定性校正（编辑距离≤1）: {len(prop)}')
    for i, n, b, d in prop[:20]:
        print(f'     {i+1:04d} {n} → {b}')
    print(f'  无法确定（待人工/继续排查）: {len(unk)}')
    print('   样本:', [n for _, n in unk[:16]])
    json.dump({'propose': prop, 'unknown': unk, 'vocab': sorted(vocab)},
              open(os.path.join(DIST, 'pdf3_name_audit.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    print('→ dist/pdf3_name_audit.json')


if __name__ == '__main__':
    main()
