# -*- coding: utf-8 -*-
"""
S30 合并「V7 中医病因辨证校正」→ v11，并做验收
判据：
  ① 长度比 ∈ [0.60, 1.25]（校正+少量补充，允许微增）
  ② 术语保留 ≥ 0.75（源文中医术语须大部分留存）
  ③ 三要素标记保真（病源/病状/治法）
  ④ **药名越界护栏**：输出不得出现源文所无的"药名+剂量"
输出 data/bingyuan_terms_v11.json + dist/v7_correct_report.json
"""
import os, re, glob, json
from collections import Counter
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, 'dist'); os.makedirs(DIST, exist_ok=True)
V7OUT = os.path.join(ROOT, 'data', 'v7_out')
PUNCT = '，。；、：？！“”‘’（）《》〈〉·—…,.!?;:()[]"\'　 \n\t'
RX = re.compile('[' + re.escape(PUNCT) + ']')
strip_p = lambda s: RX.sub('', s or '')
MARKS = {'病源': r'(?:病源|病因|病由)', '病状': r'(?:病状|症状|证候|临床表现)', '治法': r'(?:治法|治疗|疗法|方药)'}
DOSE = '一两三四五六七八九十钱分斤勺厘'
RX_HERB = re.compile(r'([\u4e00-\u9fff]{2})(?=[' + DOSE + r'])')
BLACK = {'病状', '参见', '者宜', '每服', '各二', '法宜', '源由', '汗条', '辞典', '一两', '煎至', '一五',
         '病源', '治法', '宜用', '以经', '各五', '各一', '各三', '各四', '各六', '外治', '内服', '或用'}
HERB = set()
LEX = set()


def build_lex():
    global HERB, LEX
    try:
        d = json.load(open(os.path.join(ROOT, 'data', 'tcm_ref_lexicon.json'), encoding='utf-8'))
        LEX = set(d.get('core', [])) | set(d.get('extracted_top', [])[:400])
    except Exception:
        LEX = set()


def build_herb(base):
    global HERB
    c = Counter(m.group(1) for t in base for m in RX_HERB.finditer(t.get('body') or ''))
    HERB = {w for w, n in c.items() if n >= 8 and w not in BLACK}


def fab_new(src, out):
    return {m.group(1) for m in RX_HERB.finditer(out) if m.group(1) in HERB and m.group(1) not in src}


def valid(src, out):
    so, si = strip_p(out), strip_p(src)
    if not so:
        return False, 'empty'
    r = len(so) / max(1, len(si))
    if not (0.60 <= r <= 1.25):
        return False, f'len比{r:.2f}'
    ent = {w for w in re.findall(r'[\u4e00-\u9fff]{2,5}', si) if w in LEX}
    keep = (sum(1 for e in ent if e in so) / len(ent)) if ent else 1.0
    if keep < 0.75:
        return False, f'术语保留{keep:.2f}({len(ent)})'
    for k, pat in MARKS.items():
        if re.search(pat, si) and not re.search(pat, so):
            return False, f'丢{k}标记'
    fab = fab_new(src, out)
    if fab:
        return False, '新增药名' + '/'.join(sorted(fab)[:3])
    return True, f'len比{r:.2f} 术语{keep:.2f}'


def main():
    base = json.load(open(os.path.join(ROOT, 'data', 'bingyuan_terms_v10.json'), encoding='utf-8'))
    build_lex(); build_herb(base)
    print('术语词表:', len(LEX), '| 药名护栏:', len(HERB))
    outs = {}
    for fp in sorted(glob.glob(os.path.join(V7OUT, '*.json'))):
        try:
            for e in json.load(open(fp, encoding='utf-8')):
                if e.get('no') and e.get('body'):
                    outs[e['no']] = e['body']
        except Exception as ex:
            print('  跳过', os.path.basename(fp), type(ex).__name__)
    st = Counter(); rej = []; ratios = []; keeps = []
    for t in base:
        src = t.get('body') or ''
        if t['no'] in outs:
            ok, why = valid(src, outs[t['no']])
            if ok:
                t['body'] = outs[t['no']]; t['ver'] = 'v7tcm'; st['corrected'] += 1
                ratios.append(float(why.split('len比')[1].split()[0]))
                if '术语' in why:
                    keeps.append(float(why.split('术语')[1]))
            else:
                t['ver'] = 'keep_v10'; st['fallback'] += 1
                rej.append({'no': t['no'], 'why': why, 'out': outs[t['no']][:60]})
        else:
            t['ver'] = 'keep_v10'; st['fallback'] += 1
            rej.append({'no': t['no'], 'why': 'missing', 'out': ''})
    json.dump(base, open(os.path.join(ROOT, 'data', 'bingyuan_terms_v11.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    rep = {'by_source': dict(st), 'rejected': len(rej), 'rejected_sample': rej[:15],
           'len_ratio_min': min(ratios) if ratios else None,
           'len_ratio_avg': round(sum(ratios) / len(ratios), 3) if ratios else None,
           'term_keep_min': min(keeps) if keeps else None,
           'term_keep_avg': round(sum(keeps) / len(keeps), 3) if keeps else None}
    json.dump(rep, open(os.path.join(DIST, 'v7_correct_report.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('来源:', dict(st), '| 退回:', len(rej))
    print('长度比 min/avg:', rep['len_ratio_min'], rep['len_ratio_avg'], '| 术语保留 min/avg:', rep['term_keep_min'], rep['term_keep_avg'])
    for x in rej[:6]:
        print('  !', x['no'], x['why'])


if __name__ == '__main__':
    main()
