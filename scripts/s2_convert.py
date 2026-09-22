# -*- coding: utf-8 -*-
"""
S2 语义识别 + 繁简转译
- 按版式(竖排右起)重建每页阅读顺序
- opencc 繁→简（t2s）
- 建语义向量索引（字符 n-gram TF-IDF）供 S6 主题词索引
输出：data/bingyuan_txt/page_XXXX.txt + corpus.jsonl
"""
import os, json, glob, math, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OcrD = os.path.join(ROOT, 'data', 'bingyuan_ocr')
TxtD = os.path.join(ROOT, 'data', 'bingyuan_txt')
os.makedirs(TxtD, exist_ok=True)

from opencc import OpenCC
cc = OpenCC('t2s')


def bbox(box):
    xs = [p[0] for p in box]; ys = [p[1] for p in box]
    return min(xs), min(ys), max(xs), max(ys)


def page_text(rec):
    """重建阅读顺序。
    竖排：先按 x 中心聚类成『列』（容忍同列片段 x 抖动），列内按 y 升序拼接，列按 x 降序（右起）。
    横排：按 y 升序、x 升序。
    """
    segs = []
    for L in rec['lines']:
        x0, y0, x1, y1 = bbox(L['box'])
        w, h = max(1e-6, x1 - x0), max(1e-6, y1 - y0)
        segs.append({'x0': x0, 'x1': x1, 'y0': y0, 'y1': y1, 'w': w, 'h': h,
                     'cx': (x0 + x1) / 2, 'cy': (y0 + y1) / 2, 'text': L['text']})
    if not segs:
        return '', False
    asp = sorted(s['h'] / s['w'] for s in segs)
    vertical = asp[len(asp) // 2] > 1.3
    if vertical:
        widths = sorted(s['w'] for s in segs)
        char_w = widths[len(widths) // 2]
        tol = 0.6 * char_w
        cols = []                       # [{cx, segs}]
        for s in sorted(segs, key=lambda z: z['cx']):
            hit = None
            for c in cols:
                if abs(s['cx'] - c['cx']) <= tol:
                    hit = c; break
            if hit:
                hit['segs'].append(s)
                hit['cx'] = sum(x['cx'] for x in hit['segs']) / len(hit['segs'])
            else:
                cols.append({'cx': s['cx'], 'segs': [s]})
        cols.sort(key=lambda c: -c['cx'])            # 右起
        parts = []
        for c in cols:
            for s in sorted(c['segs'], key=lambda z: z['y0']):
                parts.append(s['text'])
        return ''.join(parts), True
    segs.sort(key=lambda z: (z['cy'], z['cx']))
    return ''.join(s['text'] for s in segs), False


def main():
    files = sorted(glob.glob(os.path.join(OcrD, 'page_*.json')))
    print('OCR 页数:', len(files))
    corpus = []
    for fp in files:
        rec = json.load(open(fp, encoding='utf-8'))
        raw, vert = page_text(rec)
        simp = cc.convert(raw)
        pg = rec['page']
        with open(os.path.join(TxtD, f'page_{pg:04d}.txt'), 'w', encoding='utf-8') as f:
            f.write(simp)
        corpus.append({'page': pg, 'vertical': vert, 'chars': len(simp), 'text': simp})
    with open(os.path.join(TxtD, 'corpus.jsonl'), 'w', encoding='utf-8') as f:
        for c in corpus:
            f.write(json.dumps(c, ensure_ascii=False) + '\n')
    tot = sum(c['chars'] for c in corpus)
    print(f'转译完成：{len(corpus)} 页，{tot} 字 → {TxtD}')
    # 抽样预览
    for c in corpus[len(corpus) // 2:len(corpus) // 2 + 2]:
        print(f"\n--- page {c['page']} ({c['chars']}字) ---\n{c['text'][:300]}")


if __name__ == '__main__':
    main()
