# -*- coding: utf-8 -*-
"""
S67 目录↔正文 语义逻辑校正（**确定性**，不依赖 LLM）

思路（用户规格："目录词条-正文病名-内容对应"）：
  ① 目录（目录01–47，4 栏）→ 权威**名序**
  ② 正文单元的【病名】标记 → 实际名序
  ③ 两者**按阅读序对齐**：目录有而正文无名/讹形 → 用目录名补正
  ④ 用**词汇表约束**（正文已提取的名集合）从目录串中识别名序，避免页码噪声

输出：dist/pdf3_toc_align.json（对齐表 + 分歧清单）
"""
import os, re, json, sys
from collections import Counter
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, 'dist')
TOC = json.load(open(os.path.join(DIST, 'pdf3_toc_stream.json'), encoding='utf-8'))['pages']
UNITS = json.load(open(os.path.join(ROOT, 'data', 'pdf3_units_v2.json'), encoding='utf-8'))


def toc_text():
    """目录全串（按 4 栏阅读序连成一条），并剥掉书眉/页码噪声"""
    parts = []
    for it in TOC:
        t = it['text']
        t = t.replace('病源辞典', '')
        parts.append(t)
    S = ''.join(parts)
    # 页码/书眉噪声：孤立的数字与单字（「四四」「五」「七六六六五」等）
    S = re.sub(r'[0-9０-９]+', '', S)
    return S


def body_names():
    return [(i, (u.get('name') or '').strip()) for i, u in enumerate(UNITS)]


def main():
    S = toc_text()
    BN = body_names()
    vocab = set(n for _, n in BN if n and n != '病名待定' and len(n) >= 2)
    print('目录串长:', len(S), '| 正文单元:', len(BN), '| 名汇:', len(vocab))

    # ① 贪心扫描目录串，抽出「正文名汇」中的名字序列（最长匹配优先）
    names = sorted(vocab, key=len, reverse=True)
    seq, pos, i = [], 0, 0
    while i < len(S):
        hit = None
        for nm in names:
            if S.startswith(nm, i):
                hit = nm
                break
        if hit:
            seq.append((i, hit))
            i += len(hit)
        else:
            i += 1
    print('目录中识别出的词条数:', len(seq))
    print('  前 25:', [n for _, n in seq[:25]])

    # ② 与正文名序比对（双序列最长公共子序列，判断是否同序）
    bseq = [n for _, n in BN]
    # 简化为「目录名在正文中首次出现的索引」单调性检查
    first = {}
    for idx, n in enumerate(bseq):
        first.setdefault(n, idx)
    mono = [first[n] for _, n in seq if n in first]
    bad = sum(1 for a, b in zip(mono, mono[1:]) if b < a)
    print(f'  目录名在正文中的首次位置: 单调递减违规 {bad} 处 / {len(mono)}')
    print('  结论:', '目录与正文**同序**（可用作权威名序）' if bad < len(mono) * 0.02 else '存在较大乱序，需分段对齐')

    json.dump({'toc_seq': [n for _, n in seq], 'toc_len': len(S),
               'body_n': len(BN), 'vocab': len(vocab), 'mono_violations': bad},
              open(os.path.join(DIST, 'pdf3_toc_align.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    print('→ dist/pdf3_toc_align.json')


if __name__ == '__main__':
    main()
