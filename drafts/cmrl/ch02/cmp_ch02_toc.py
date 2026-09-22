# -*- coding: utf-8 -*-
"""ch02 目录与正文口径自动比对：提取 ch02 各制品文档的标题/引用 → 找不一致（旧口径）
比对对象: 正文 01-1.1.md~08-1.8.md 实际节标题 vs
          chapter-02-figures.md / changelog / selfcheck / exercises / 目录 toc
"""
import re
from pathlib import Path

CH = Path(r'C:\Users\DELL\textbook-project\drafts\cmrl\ch02')
TOC = Path(r'C:\Users\DELL\textbook-project\drafts\cmrl\toc_v2\ch02_toc.md')

# ① 正文实际节标题（01-1.1.md 等首行 # ）
body_files = sorted(CH.glob('*.md'))
titles = {}
for f in body_files:
    if not re.match(r'\d{2}-\d\.\d\.md', f.name):
        continue
    txt = f.read_text(encoding='utf-8', errors='ignore')
    m = re.search(r'^##\s+(.+)$', txt, re.M)
    if m:
        titles[f.name] = m.group(1).strip()
print('===== 正文节标题（ch02 实际结构）=====')
for name, t in titles.items():
    print(f'  {name}: {t[:60]}')

# ② 制品文档中对章节/图/术语的引用（候选旧口径）
print('\n===== 制品文档引用扫描 =====')
for f in body_files:
    if f.name in titles or f.name in ('chapter-02-changelog.md',):
        continue
    txt = f.read_text(encoding='utf-8', errors='ignore')
    # 找 "第X章" / "第X节" / "2.X节" / "图2-" 引用
    refs = re.findall(r'(第[一二三四五六七八九十]+章|第[一二三四五六七八九十]+节|\d\.\d节?|图\s?\d+-\d+|2\.\d\.\d)', txt)
    if refs:
        print(f'  {f.name}: {refs[:15]}')

# ③ 与 toc 规划对照（节标题差异）
print('\n===== 目录规划节（toc_v2）vs 正文实际节 =====')
toc_txt = TOC.read_text(encoding='utf-8', errors='ignore')
toc_secs = re.findall(r'\|\s*2\s*\|\s*(\d)\s*\|\s*\|\s*\|?\s*([^|]+?)\s*\|', toc_txt)
print('  目录节:', [s[1].strip()[:20] for s in toc_secs][:10])
print('  正文节数:', len(titles))
