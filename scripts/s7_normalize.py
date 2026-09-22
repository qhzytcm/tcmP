# -*- coding: utf-8 -*-
"""
S7 简体中文规范化（为 ICD-11 术语统一 + 病证单元调整做准备）
- 二次繁简/异体归一（opencc t2s → tw2s）
- 去 OCR 残留噪声、标点全角归一
- 保守 OCR 校正词典（可扩充）
- 词条结构化：拆【病源/病状/治法】三节（原著凡例：一病名分三项记之）
输出：data/bingyuan_terms.json
"""
import os, re, json, glob, argparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TxtD = os.path.join(ROOT, 'data', 'bingyuan_txt')
STROKES = json.load(open(os.path.join(ROOT, 'data', 'strokes.json'), encoding='utf-8'))

from opencc import OpenCC
_cc1, _cc2 = OpenCC('t2s'), OpenCC('tw2s')

# 保守 OCR 校正（只收高置信、系统性误识；可扩充）
OCR_FIX = {
    '特源牌典': '病源辞典', '润源静典': '病源辞典', '烤源群典': '病源辞典',
    '病源静典': '病源辞典', '病源麟典': '病源辞典', '树源静典': '病源辞典',
    '源韵典': '病源辞典', '病源韵典': '病源辞典', '静典': '辞典',
    '病送': '病状', '病默': '病状', '病肤': '病状',
    '病愿': '病源', '洛法': '治法', '活法': '治法',
    '群见': '参见', '参看': '参见',
}
CJK = re.compile(r'[\u3400-\u4dbf\u4e00-\u9fff]')
KEEP = re.compile(r'[\u3400-\u4dbf\u4e00-\u9fff，。、；：？！（）【】·0-9A-Za-z]')


def normalize_text(t):
    t = _cc1.convert(t)
    t = _cc2.convert(t)
    # 先把 ASCII 标点归一为全角，再过滤噪声（否则 ASCII 标点会被 KEEP 直接删除）
    t = t.replace(',', '，').replace('.', '。').replace(';', '；').replace(':', '：').replace('?', '？')
    for k, v in OCR_FIX.items():
        if k in t:
            t = t.replace(k, v)
    t = ''.join(ch for ch in t if KEEP.match(ch) or ch in '\n')
    return t


def stroke_key(h):
    return [STROKES.get(c, 999) for c in h] + [0] * (8 - len(h))


def load_pages(content_from):
    out = []
    for fp in sorted(glob.glob(os.path.join(TxtD, 'page_*.txt'))):
        n = int(re.search(r'(\d+)', os.path.basename(fp)).group(1))
        if n >= content_from:
            out.append((n, normalize_text(open(fp, encoding='utf-8').read())))
    return out


def split_sections(body):
    """按原著凡例拆 病源/病状/治法 三节。"""
    secs = {'病源': '', '病状': '', '治法': ''}
    marks = [('病源', body.find('病源')), ('病状', body.find('病状')), ('治法', body.find('治法'))]
    marks = [(k, i) for k, i in marks if i >= 0]
    marks.sort(key=lambda x: x[1])
    if not marks:
        secs['病源'] = body
        return secs
    for idx, (k, i) in enumerate(marks):
        j = marks[idx + 1][1] if idx + 1 < len(marks) else len(body)
        secs[k] = body[i + 2:j]
    # 病源之前的前导并入病源
    if marks[0][1] > 0:
        secs['病源'] = body[:marks[0][1]] + secs['病源']
    return secs


def extract_entries(pages):
    entries, head, body, src = [], None, [], set()
    for pg, t in pages:
        for seg in re.split(r'(【[^】]{1,14}】)', t):
            m = re.fullmatch(r'【([^】]{1,14})】', seg or '')
            if m:
                if head:
                    entries.append({'head': head, 'body': ''.join(body), 'src': sorted(src)})
                head, body, src = m.group(1), [], {pg}
            elif head is not None:
                body.append(seg or ''); src.add(pg)
    if head:
        entries.append({'head': head, 'body': ''.join(body), 'src': sorted(src)})
    for e in entries:
        e['body'] = re.sub(r'\s+', '', e['body'])
    return [e for e in entries if e['head'] and len(e['body']) >= 2]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--content-from', type=int, default=56)
    ap.add_argument('--out', default=os.path.join(ROOT, 'data', 'bingyuan_terms.json'))
    a = ap.parse_args()

    pages = load_pages(a.content_from)
    ents = extract_entries(pages)
    ents.sort(key=lambda e: (stroke_key(e['head']), e['head']))
    terms = []
    for i, e in enumerate(ents, 1):
        secs = split_sections(e['body'])
        terms.append({
            'no': f'{i:04d}', 'head': e['head'],
            'stroke_first': STROKES.get(e['head'][0], None),
            'stroke_key': stroke_key(e['head']),
            'body': e['body'], 'sections': secs, 'src_pages': e['src'],
            'icd11': None,               # 由 s7b_icd_map.py 回填
        })
    json.dump(terms, open(a.out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f'规范化词条 {len(terms)} → {a.out}')
    for t in terms[:5]:
        print(f"  {t['no']} {t['head']}(首字{t['stroke_first']}画) 病源:{t['sections']['病源'][:24]}...")


if __name__ == '__main__':
    main()
