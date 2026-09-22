# -*- coding: utf-8 -*-
"""
S75 噪声普查：扫出正文中的「…」与扫描污染符号（非汉字/非标准标点）
"""
import os, re, json, sys
from collections import Counter
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
from s77_clean import clean as clean_noise      # 审「清理后」文本
U = json.load(open(os.path.join(ROOT, 'data', 'pdf3_units_v2.json'), encoding='utf-8'))
# LLM 校本（取最新）
outs = {}
fp = os.path.join(ROOT, 'data', 'pdf3_llm_out.jsonl')
P = os.path.join(ROOT, 'dist')
for line in open(fp, encoding='utf-8', errors='replace'):
    line = line.strip()
    if line:
        try:
            r = json.loads(line)
        except Exception:
            continue
        if r['i'] not in outs or (r.get('ok') and not outs[r['i']].get('ok')):
            outs[r['i']] = r
texts = []
for i, u in enumerate(U):
    r = outs.get(i)
    t = (r['out'] if (r and r.get('ok')) else u['body']) if r else u['body']
    texts.append(clean_noise(t))
FULL = ''.join(texts)
print(f'单元 {len(U)} | 正文字符 {len(FULL)}')

# 标准标点白名单（LLM 补的 + 原文应有的）
OK = set('，。、；：？！「」『』（）《》〈〉·—…～％%﹒·,.;:?!()[]{}<>/\\|"\'　 \n【】〔〕')
bad = Counter()
for ch in FULL:
    if ch in OK:
        continue
    o = ord(ch)
    if 0x4E00 <= o <= 0x9FFF:          # 汉字
        continue
    if ch.isdigit() or ch.isalpha():
        continue
    bad[ch] += 1
print('\n=== 非汉字/非标点字符（噪声候选）===')
for ch, n in bad.most_common(40):
    print(f'  {repr(ch):10s} U+{ord(ch):04X} ×{n}')

print('\n=== 「…」与「...」统计 ===')
for pat in ('…', '...', '．', '··', '。', '「', '」'):
    print(f'  {pat!r}: {FULL.count(pat)}')

noisy = [i for i, t in enumerate(texts) if bad and any(c in t for c in bad)]
print(f'\n含噪声的单元数: {len(noisy)} / {len(U)}')
for i in noisy[:5]:
    t = texts[i]
    ex = [c for c in t if c in bad]
    print(f'  idx{i} 【{U[i]["name"]}】噪声字 {Counter(ex).most_common(5)}')
    print(f'      {t[:80]}')
