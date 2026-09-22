# -*- coding: utf-8 -*-
"""
S35 从第二份 PDF 的 OCR 页中提取指定条目正文
版式：A4 横向，一本 = 左右两书页；每书页竖排右起
做法：按 x 中位线切左右半 → 右半先（右起） → 每半内按列 x 降序、列内 y 升序 → 拼成阅读序文本
输入：dist/pdf2_locate.json（条目→页码）；输出 data/pdf2_extract.json
"""
import os, json, re
import opencc
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, 'data', 'bingyuan2_ocr')
cc = opencc.OpenCC('t2s')
cct = opencc.OpenCC('s2t')


def cx(L):
    xs = [p[0] for p in L['box']]
    return sum(xs) / len(xs)


def cy(L):
    ys = [p[1] for p in L['box']]
    return sum(ys) / len(ys)


def order_lines(lines):
    """按 x 中位线切左右 → 右半先 → 每半内列聚类(右起)+列内 y 升序"""
    if not lines:
        return []
    xs = [cx(L) for L in lines]
    mid = (min(xs) + max(xs)) / 2
    out = []
    for lo, hi in ((mid, max(xs) + 1), (min(xs) - 1, mid)):     # 右半, 左半
        half = [L for L in lines if lo <= cx(L) < hi]
        if not half:
            continue
        cols = []
        for L in sorted(half, key=lambda x: -cx(x)):
            for c in cols:
                if abs(c['cx'] - cx(L)) < 40:
                    c['segs'].append(L); break
            else:
                cols.append({'cx': cx(L), 'segs': [L]})
        cols.sort(key=lambda c: -c['cx'])
        for c in cols:
            for L in sorted(c['segs'], key=cy):
                out.append(L['text'])
    return out


def page_text(pg):
    fp = os.path.join(RES, f'page_{pg:04d}.json')
    if not os.path.exists(fp):
        return None
    d = json.load(open(fp, encoding='utf-8'))
    return order_lines(d['lines'])


def extract(pg, head_t, span=6):
    """在页内找 【head_t】 后、下一条目 【…】 前的文本"""
    txt = page_text(pg)
    if not txt:
        return None
    joined = '\n'.join(txt)
    i = joined.find(f'【{head_t}】')
    if i < 0:
        i = joined.find(head_t, max(0, joined.find(head_t) - 100)) if head_t in joined else -1
    if i < 0:
        return None
    tail = joined[i + len(head_t) + 2:]
    m = re.search(r'【[^】]{1,12}】', tail)
    if m and m.start() < 4000:
        tail = tail[:m.start()]
    return re.sub(r'\s+', '', tail)[:3000]


def main():
    loc = json.load(open(os.path.join(ROOT, 'dist', 'pdf2_locate.json'), encoding='utf-8'))
    out = {}
    for no, v in loc.items():
        got = None
        for pg in v['pages']:
            t = extract(pg, v['head_t'])
            if t and len(t) >= 12:
                got = {'page': pg, 'trad': t, 'simp': cc.convert(t)}
                break
        out[no] = {'head': v['head'], 'head_t': v['head_t'], 'pages': v['pages'], 'extract': got}
    json.dump(out, open(os.path.join(ROOT, 'data', 'pdf2_extract.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    ok = [no for no, v in out.items() if v.get('extract')]
    print(f'提取成功 {len(ok)} / {len(out)}')
    for no in ok[:8]:
        v = out[no]['extract']
        print(f"  {no} {out[no]['head']} p{v['page']} | 简体 {len(v['simp'])} 字: {v['simp'][:70]}")


if __name__ == '__main__':
    main()
