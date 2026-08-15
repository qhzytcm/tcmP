# -*- coding: utf-8 -*-
"""cmrl_convert_titles.py — 把 ch{NN} 分节文件标题转换为无标记科普标题

旧: ## [科普] N.N 旧标题      →  新: ## N.N 新标题（toc_v2 目录）
正文段落原样保留。仅替换每个文件首行标题。
用法: python scripts/cmrl_convert_titles.py --ch 1
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from cmrl_toc_v2 import CHAPTERS_V2  # noqa: E402

DRAFTS = Path(r'C:\Users\DELL\textbook-project\drafts\cmrl')


def convert(ch: int):
    n, sheet, title, src, anchor, secs = CHAPTERS_V2[ch - 1]
    d = DRAFTS / f'ch{ch:02d}'
    if not d.exists():
        print(f'[skip] ch{ch:02d} 目录不存在')
        return 0
    changed = 0
    for i, sec in enumerate(secs, 1):
        f = d / f'0{i}-{n}.{i}.md'
        if not f.exists():
            print(f'[warn] 缺 {f.name}')
            continue
        text = f.read_text(encoding='utf-8')
        lines = text.splitlines(keepends=True)
        if not lines:
            continue
        # 替换首行标题（兼容 [科普]/[Part1]/[Part2] 前缀或无前缀旧标题）
        new_head = f'## {n}.{i} {sec}\n'
        lines[0] = re.sub(r'^##\s+.*$', new_head.rstrip('\n'), lines[0].rstrip('\r\n')) + '\n'
        f.write_text(''.join(lines), encoding='utf-8')
        changed += 1
    print(f'[ch{ch:02d}] 转换 {changed}/8 个文件标题 → 无标记科普标题')
    return changed


if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--ch', type=int, required=True)
    args = ap.parse_args()
    convert(args.ch)
