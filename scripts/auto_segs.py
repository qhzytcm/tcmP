# -*- coding: utf-8 -*-
"""素问 11-81 自动分段提取（顺序分段法: 按转写行序均匀切 10 段）
每段: 原文=段内"原文-"短句拼接; 讲解=段内"注释-"/"理解-"句拼接（忠实转写流）
"""
import json
import re
from pathlib import Path

import pandas as pd

XLSX = r'C:\Users\DELL\Desktop\HDNJ音频理解(2).xls'
DOCS = Path(r'C:\Users\DELL\tcmP\docs\视频')


def clean_part(p):
    p = re.sub(r'^Hermes独立理解《[^》]+》：.*?。', '', p)
    p = p.replace('（鼓掌）', '').replace('（笑）', '').replace('（掌声）', '')
    return p.strip()


def auto_extract(sheet, ch):
    """按行序切 10 段（原文+讲解）"""
    df = pd.read_excel(XLSX, sheet_name=sheet)
    rows = []  # (类型, 内容)
    for v in df['文本内容'].dropna():
        t = str(v).strip()
        if not t:
            continue
        if t.startswith('原文-'):
            rows.append(('orig', t[3:].strip()))
        elif t.startswith('注释-'):
            rows.append(('note', t[3:].strip()))
        elif t.startswith('理解-'):
            rows.append(('und', t[3:].strip()))
        else:
            rows.append(('oth', t))  # 无前缀行（对话式转写: 无原文引用的篇目兜底）
    if not rows:
        return None
    has_orig = any(r[0] == 'orig' for r in rows)
    # 均匀切 10 段（按行数）
    n = len(rows)
    seg_size = max(1, n // 10)
    segs = []
    prev_orig = ''
    prev_talk = ''
    for i in range(10):
        part = rows[i * seg_size: (i + 1) * seg_size if i < 9 else n]
        if not part:
            break
        origs = []
        talks = []
        for typ, content in part:
            if typ == 'orig' and len(content) > 3:
                if not any(content in o or o in content for o in origs):
                    origs.append(content)
            elif typ in ('note', 'und'):
                c = clean_part(content)
                if len(c) > 10 and not any(c == q or (len(c) > 20 and (c in q or q in c)) for q in talks):
                    talks.append(c)
            elif typ == 'oth' and not has_orig:
                # 无原文篇目: 无前缀行作讲解源（清洗口语）
                c = clean_part(content)
                if len(c) > 12 and not any(c == q or (len(c) > 20 and (c in q or q in c)) for q in talks):
                    talks.append(c)
        orig = '，'.join(origs)
        if not orig and prev_orig:
            orig = prev_orig  # 兜底: 复用前段原文（保证 TTS 有原文开头）
        prev_orig = orig or prev_orig
        talk = '。'.join(talks)
        if len(talk) < 20 and prev_talk:
            talk = prev_talk[-120:]  # 兜底: 复用前段讲解尾（保证非空）
        prev_talk = talk or prev_talk
        if len(talk) > 480:
            talk = talk[:480] + '。'
        # 段题: 第一条原文句（截 12 字）
        title = (origs[0][:12] + '…') if origs else f'第 {i + 1} 段'
        segs.append({'title': f'第{"一二三四五六七八九十"[i]}段 · {title}', 'orig': orig, 'talk': talk})
    # 若不足 10 段补齐（重复最后一段讲解）
    while len(segs) < 10:
        segs.append({'title': f'第{"一二三四五六七八九十"[len(segs)]}段 · 收束',
                     'orig': '', 'talk': segs[-1]['talk'] if segs else '（讲解）'})
    out = DOCS / f'segs_suwen{ch}.json'
    out.write_text(json.dumps(segs, ensure_ascii=False, indent=1), encoding='utf-8')
    total = sum(len(s['orig']) + len(s['talk']) for s in segs)
    print(f'[{sheet}] 自动分段 10 段, 总字数 {total}')
    return segs
