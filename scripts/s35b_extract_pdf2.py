# -*- coding: utf-8 -*-
"""
S35b 从第二份 PDF 的 OCR 页提取指定条目正文（双书页版式 + 繁简归一）
版式：A4 横向 = 左右两书页；每书页竖排右起 → 右半先，每半内按列 x 降序、列内 y 升序
输入 dist/pdf2_locate.json → 输出 data/pdf2_extract.json
"""
import os, json, re
import opencc
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, 'data', 'bingyuan2_ocr')
t2s = opencc.OpenCC('t2s')
v12 = {t['no']: t for t in json.load(open(os.path.join(ROOT, 'data', 'bingyuan_terms_v12.json'), encoding='utf-8'))}


def cx(L):
    return sum(p[0] for p in L['box']) / len(L['box'])


def cy(L):
    return sum(p[1] for p in L['box']) / len(L['box'])


def ordered_lines(pg):
    fp = os.path.join(RES, f'page_{pg:04d}.json')
    if not os.path.exists(fp):
        return []
    lines = json.load(open(fp, encoding='utf-8'))['lines']
    if not lines:
        return []
    xs = [cx(L) for L in lines]
    mid = (min(xs) + max(xs)) / 2
    out = []
    for lo, hi in ((mid, max(xs) + 1), (min(xs) - 1, mid)):
        half = [L for L in lines if lo <= cx(L) < hi]
        if not half:
            continue
        cols = []
        for L in sorted(half, key=lambda x: -cx(x)):
            for c in cols:
                if abs(c['cx'] - cx(L)) < 45:
                    c['segs'].append(L); break
            else:
                cols.append({'cx': cx(L), 'segs': [L]})
        cols.sort(key=lambda c: -c['cx'])
        for c in cols:
            for L in sorted(c['segs'], key=cy):
                out.append(L['text'])
    return out


def extract(pg, keys):
    ls = ordered_lines(pg)
    if not ls:
        return None
    for k in keys:
        for i, s in enumerate(ls):
            if f'【{k}】' in s or (len(k) >= 3 and k in s):
                segs = [s.split('】')[-1] if '】' in s else s]
                for j in range(i + 1, min(i + 40, len(ls))):
                    if re.search(r'【[^】]{1,12}】', ls[j]):
                        break
                    segs.append(ls[j])
                body = t2s.convert(re.sub(r'[\s\u3000]', '', ''.join(segs)))
                if len(body) >= 12:
                    return {'page': pg, 'key': k, 'body': body[:1500]}
    return None


def main():
    loc = json.load(open(os.path.join(ROOT, 'dist', 'pdf2_locate.json'), encoding='utf-8'))
    out = {}
    for no, v in loc.items():
        got = None
        for pg in v['pages']:
            got = extract(pg, v['keys'])
            if got:
                break
        out[no] = {'head': v['head'], 'keys': v['keys'], 'pages': v['pages'], 'extract': got}
    json.dump(out, open(os.path.join(ROOT, 'data', 'pdf2_extract.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    ok = [(no, v) for no, v in out.items() if v.get('extract')]
    print(f'提取成功 {len(ok)} / {len(out)}')
    for no, v in ok[:10]:
        e = v['extract']
        print(f"  {no} {v['head'][:14]} p{e['page']} ({len(e['body'])}字): {e['body'][:80]}")


if __name__ == '__main__':
    main()
