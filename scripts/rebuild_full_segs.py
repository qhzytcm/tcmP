# -*- coding: utf-8 -*-
"""FULL 篇（57,63-80）segs 重建：从源 Excel 提取真实讲解（基于 auto_segs 顺序分段法）
- SW57 有 原文/注释/理解 前缀 → 标准提取
- SW63-80 为倪师口语转写（oth 行）→ 无原文引用篇目，oth 行作讲解源（auto_segs 兜底逻辑）
用法: python rebuild_full_segs.py [--apply] [--ch 63,64]
"""
import json
import re
import sys
from pathlib import Path

import pandas as pd

XLSX = r'C:\Users\DELL\Desktop\HDNJ音频理解(2).xls'
HDNJ_QUANWEN = r'C:\Users\DELL\Desktop\醒了么(张仲景)\黄帝内经全文.xls'
DOCS = Path(r'C:\Users\DELL\tcmP\docs\视频')

CH_NAMES = {
    57: '经络论', 63: '缪刺论', 64: '四时刺逆从论', 65: '标本病传论',
    66: '天元纪大论', 67: '五运行大论', 68: '六微旨大论', 69: '气交变大论',
    70: '五常政大论', 71: '六元正纪大论', 72: '刺法论', 73: '本病论',
    74: '至真要大论', 75: '著至教论', 76: '示从容论', 77: '疏五过论',
    78: '徵四失论', 79: '阴阳类论', 80: '方盛衰论',
}

AD_KWS = ["搜索人纪求真", "搜索人际求真", "人纪求真下载", "应用商店搜索", "视频一听就懂",
          "告别学了后面忘", "快速梳理知识框架", "手机应用商店", "人纪求真", "一目了然"]
HERMES_RE = re.compile(r'Hermes独立理解《[^》]*》[:：]')


def clean_part(p):
    # Hermes 元分析整行丢弃（含 注释-Hermes独立理解/理解- 伪装行）
    if p.startswith('Hermes独立理解') or 'Hermes独立理解' in p[:30]:
        return ''
    p = HERMES_RE.sub('', p)
    p = re.sub(r'^[一二三四五六七八九十]+、', '', p)
    for k in AD_KWS:
        p = p.replace(k, '')
    p = p.replace('（鼓掌）', '').replace('（笑）', '').replace('（掌声）', '')
    return p.strip()


_QW_CACHE = {}


def load_quanwen_orig(ch):
    """从《黄帝内经全文.xls》取第 ch 篇原文行（类型=原文）"""
    if ch in _QW_CACHE:
        return _QW_CACHE[ch]
    df = pd.read_excel(HDNJ_QUANWEN, sheet_name=f'SW{ch:02d}')
    origs = []
    for _, r in df.iterrows():
        vals = [str(v).strip() for v in r.values]
        # 行格式: 序号|类型(原文/注释)|内容
        if len(vals) >= 3 and vals[1] == '原文' and len(vals[2]) > 5:
            origs.append(vals[2])
    _QW_CACHE[ch] = origs
    return origs


def auto_extract(sheet, ch):
    """行序 10 等份切段（v1 思路）+ 段内独立提取：
    - 每段内容取自该区间全部行，不跨段复用（杜绝重复段）
    - talk 为空/过短时：放宽阈值重取该段所有 oth 行（保证非空真实讲解）
    - orig 行归属本段；本段无 orig 则尝试从《黄帝内经全文.xls》按等份补原文；再兜底复用前段
    """
    df = pd.read_excel(XLSX, sheet_name=sheet)
    rows = []
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
        elif t.startswith('总结-'):
            rows.append(('sum', t[3:].strip()))
        else:
            rows.append(('oth', t))
    if not rows:
        return None
    has_orig = any(r[0] == 'orig' for r in rows)
    # 行序 10 等份（讲解行也要有——若某等份完全无讲解行则并入相邻）
    n = len(rows)
    seg_size = max(1, n // 10)
    bounds = []
    for i in range(10):
        lo = i * seg_size
        hi = (i + 1) * seg_size if i < 9 else n
        if lo >= n:
            break
        bounds.append((lo, hi))
    CN = "一二三四五六七八九十"
    segs = []
    prev_orig = ''
    qw_origs = load_quanwen_orig(ch) if ch >= 16 else []
    for bi, (lo, hi) in enumerate(bounds):
        part = rows[lo:hi]
        if not part:
            continue
        origs, talks = [], []
        for typ, content in part:
            if typ == 'orig' and len(content) > 3:
                if not any(content in o or o in content for o in origs):
                    origs.append(content)
            elif typ == 'note':
                # 注释- = 倪师白话讲解，主 talk 源
                c = clean_part(content)
                if len(c) > 8 and not any(c == q or (len(c) > 20 and (c in q or q in c)) for q in talks):
                    talks.append(c)
            elif typ == 'oth' and not has_orig:
                # 无原文篇目：口语转写行作讲解源
                c = clean_part(content)
                if len(c) > 8 and not any(c == q or (len(c) > 20 and (c in q or q in c)) for q in talks):
                    talks.append(c)
            # 理解-/总结-（und/sum）为 Hermes 元分析风格，排除出 talk（防 AI 腔混入讲课）
        orig = '，'.join(origs)
        # 段内无原文 → 从全文 xls 按 10 等份补（各段取对应 1/10 原文段）
        if not orig and qw_origs:
            nq = len(qw_origs)
            q_lo = bi * nq // 10
            q_hi = (bi + 1) * nq // 10 if bi < 9 else nq
            piece = qw_origs[q_lo:q_hi]
            if piece:
                orig = '，'.join(piece)
                if len(orig) > 380:
                    orig = orig[:380] + '…'
        if not orig:
            orig = prev_orig
        prev_orig = orig or prev_orig
        talk = '。'.join(talks)
        # talk 空/过短（该段讲解行稀疏）：放宽阈值取该段全部行（仍排除 und/sum 总结风格）
        if len(talk) < 40:
            talks2 = []
            for typ, content in part:
                if typ == 'note' or (typ == 'oth' and not has_orig):
                    c = clean_part(content)
                    if len(c) > 4 and not any(c == q or (len(c) > 20 and (c in q or q in c)) for q in talks2):
                        talks2.append(c)
            if talks2:
                talk = '。'.join(talks2)
        # 480 上限：按最后一个句号截断保整句（避免断裂）
        if len(talk) > 480:
            cut = talk[:480]
            last_dot = max(cut.rfind('。'), cut.rfind('！'), cut.rfind('？'))
            talk = cut[:last_dot + 1] if last_dot > 100 else cut[:480] + '。'
        title = (origs[0][:12] + '…') if origs else f'第 {bi + 1} 段讲解'
        segs.append({'title': f'第{CN[bi]}段 · {title}', 'orig': orig, 'talk': talk})
    return segs


def main():
    apply = '--apply' in sys.argv
    chs = [57] + list(range(63, 81))
    # --ch 覆盖
    if '--ch' in sys.argv:
        chs = [int(x) for x in sys.argv[sys.argv.index('--ch') + 1].split(',')]
    for ch in chs:
        sheet = f'SW{ch}' if ch >= 16 else f'{ch}-{CH_NAMES[ch]}'
        segs = auto_extract(sheet, ch)
        if not segs:
            print(f'素问{ch}: ❌ Excel 无数据')
            continue
        total = sum(len(s['orig']) + len(s['talk']) for s in segs)
        if apply:
            out = DOCS / f'segs_suwen{ch}.json'
            out.write_text(json.dumps(segs, ensure_ascii=False, indent=1), encoding='utf-8')
        print(f'素问{ch} [{sheet}]: 重建 10 段, 总字数 {total}, talk最短段={min(len(s["talk"]) for s in segs)}')


if __name__ == '__main__':
    main()
