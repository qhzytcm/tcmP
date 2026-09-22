# -*- coding: utf-8 -*-
"""S50 构建全书阅读序文本流 + 分析【】标记与三段标记"""
import os, re, json, glob
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ocr_fix_rules import fix as safe_t2s          # 统一校字规则（含 t2s + 书眉归一）
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, 'data', 'bingyuan3_ocr')
DIST = os.path.join(ROOT, 'dist'); os.makedirs(DIST, exist_ok=True)


def nbands_of(pg):
    """版式规格：目录区（扫描 12–58，即「目录01–47」）每页 **4 栏**；
    正文区（扫描 59 起，即正文0001–1121）每页 **3 栏**；其余按 3 栏"""
    return 4 if 12 <= pg <= 58 else 3


def page_cols(pg, xthr=45, nbands=None):
    """
    竖排版式：每页分 nbands 条「栏」（横向条带）；
    阅读序 = **栏自上而下**（3栏=上/中/下；4栏=上/中上/中下/下）
             → 栏内列「右→左」 → 列内字「上→下」。
    """
    nb = nbands if nbands else nbands_of(pg)
    fp = os.path.join(RES, f'page_{pg:04d}.json')
    if not os.path.exists(fp):
        return []
    d = json.load(open(fp, encoding='utf-8'))
    L = []
    for x in d['lines']:
        xs = [p[0] for p in x['box']]; ys = [p[1] for p in x['box']]
        if x['text'].strip():
            L.append((sum(xs) / 4, sum(ys) / 4, x['text'].strip()))
    if not L:
        return []
    ymin = min(i[1] for i in L); ymax = max(i[1] for i in L)
    span = max(1.0, ymax - ymin)
    out = []
    for b in range(nb):
        lo = ymin + span * b / nb
        seg = ([i for i in L if lo <= i[1] < ymin + span * (b + 1) / nb]
               if b < nb - 1 else [i for i in L if i[1] >= lo])
        if not seg:
            continue
        cols = []
        for cx, cy, t in sorted(seg, key=lambda z: -z[0]):
            for c in cols:
                if abs(c['cx'] - cx) < xthr:
                    c['segs'].append((cy, t)); break
            else:
                cols.append({'cx': cx, 'segs': [(cy, t)]})
        cols.sort(key=lambda c: -c['cx'])
        out.extend(''.join(t for _, t in sorted(c['segs'])) for c in cols)
    return out


def build_stream(lo=59, hi=1179):
    """正文流：扫描 59–1179 = 正文0001–1118 + 增补1119–1121（**每页 3 栏**）"""
    parts = []
    for pg in range(lo, hi + 1):
        cols = page_cols(pg)
        if cols:
            parts.append((''.join(cols), pg))
    return parts


def build_toc_stream(lo=12, hi=58):
    """目录流：扫描 12–58 = 目录01–47（**每页 4 栏**）"""
    parts = []
    for pg in range(lo, hi + 1):
        cols = page_cols(pg)
        if cols:
            parts.append((''.join(cols), pg))
    return parts


if __name__ == '__main__':
    parts = build_stream()
    full = ''.join(p for p, _ in parts)
    print('页数:', len(parts), '| 总字数:', len(full))
    n_b = full.count('【')
    print('【 数:', n_b, '| 】 数:', full.count('】'))
    for w in ('病源', '病状', '治法', '参见'):
        print(f'  {w}: {full.count(w)}')
    # 【】标记是否成对
    marks = re.findall(r'【([^】]{0,20})】?', full)
    print('\n标记样本:', marks[100:115])
    lens = [len(m) for m in re.findall(r'【([^】]{0,20})】', full)]
    from collections import Counter
    print('完整【…】词目数:', len(lens), '| 长度分布:', Counter(lens).most_common(8))
    s = safe_t2s(full)
    json.dump({'full': s}, open(os.path.join(DIST, 'pdf3_stream.json'), 'w', encoding='utf-8'), ensure_ascii=False)
    print('已写 dist/pdf3_stream.json', len(s), '字')
    # 目录流（4 栏）
    tp = build_toc_stream()
    tf = ' '.join(p for p, _ in tp)
    json.dump({'pages': [{'scan': pg, 'text': safe_t2s(t)} for t, pg in tp]},
              open(os.path.join(DIST, 'pdf3_toc_stream.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('目录流:', len(tp), '页（4栏）|', len(tf), '字 → dist/pdf3_toc_stream.json')
    print('  目录首 150 字:', safe_t2s(tf)[:150])
