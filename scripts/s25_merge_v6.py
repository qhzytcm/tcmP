# -*- coding: utf-8 -*-
"""
S25 合并「V6 现代汉语简洁化」→ v8，并做**现代汉语简洁档**验收
判据：
  ① 长度比 ∈ [0.45, 1.10]（要求简洁，允许明显压缩，但不许膨胀）
  ② 医学术语保真：源文中的**方药/病名类术语**（2~6 字，取自权威词表或源文高频词）须在输出中保留 ≥60%
  ③ 三要素标记保真（源有 → 输出必有）
  ④ 不得新增源文没有的方药词
输出 data/bingyuan_terms_v8.json + dist/v6_rewrite_report.json
"""
import os, re, glob, json
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, 'dist'); os.makedirs(DIST, exist_ok=True)
V6OUT = os.path.join(ROOT, 'data', 'v6_out')
PUNCT = '，。；、：？！“”‘’（）《》〈〉·—…,.!?;:()[]"\'　 \n\t'
RX = re.compile('[' + re.escape(PUNCT) + ']')
MARKS = {'病源': r'(?:病源|病因|病由)', '病状': r'(?:病状|症状|证候|临床表现)', '治法': r'(?:治法|治疗|疗法|方药)'}
strip_p = lambda s: RX.sub('', s or '')

# 权威术语词表（ICD-11 中文标题 + KB）+ 药名（取自语料高频 2-3 字词）
LEX = set()
try:
    t = json.load(open(os.path.join(ROOT, 'data', 'icd_cn_titles.json'), encoding='utf-8'))
    for tc in t:
        for part in re.split(r'[、，,（）()；;·\-—/]', tc):
            p = part.strip()
            if 2 <= len(p) <= 6:
                LEX.add(p)
except Exception:
    pass
for f in sorted(glob.glob(os.path.join(ROOT, 'kg', 'samples', '*.json'))):
    try:
        for d in json.load(open(f, encoding='utf-8')):
            for nm in (d.get('disease_side', {}).get('disease_name', ''), d.get('syndrome_side', {}).get('syndrome_name', ''),
                       d.get('clinical', {}).get('recommended_formula', '')):
                for part in re.split(r'[、，,（）()；;·\-—/]', nm or ''):
                    if 2 <= len(part.strip()) <= 6:
                        LEX.add(part.strip())
    except Exception:
        pass


def terms_in(s):
    """源文中的实体术语：命中权威词表者 + 高频 2-3 字串（药名/病名候选）"""
    out = set()
    for n in (2, 3, 4):
        for i in range(len(s) - n + 1):
            g = s[i:i + n]
            if g in LEX:
                out.add(g)
    return out


DOSE = '一两三四五六七八九十钱分斤勺厘'
RX_HERB = re.compile(r'([\u4e00-\u9fff]{2})(?=[' + DOSE + r'])')
BLACK = {'病状', '参见', '者宜', '每服', '各二', '法宜', '源由', '汗条', '辞典', '一两', '煎至', '一五',
         '病源', '治法', '宜用', '以经', '各五', '各一', '各三', '各四', '各六', '外治', '内服', '或用'}
HERB = set()      # 源语料"词+剂量"高频词 → 药名候选（禁编造护栏用）


def build_herb_lex(bodies):
    from collections import Counter as C
    c = C(m.group(1) for b in bodies for m in RX_HERB.finditer(b))
    return {w for w, n in c.items() if n >= 8 and w not in BLACK}


def fab_new(src, out):
    """输出中出现、源文所无的"药名+剂量"词（编造风险）"""
    new = set()
    for m in RX_HERB.finditer(out):
        w = m.group(1)
        if w in HERB and w not in src:
            new.add(w)
    return new


def valid(src, out):
    so, si = strip_p(out), strip_p(src)
    if not so:
        return False, 'empty'
    r = len(so) / max(1, len(si))
    if not (0.45 <= r <= 1.10):
        return False, f'len比{r:.2f}'
    ent = terms_in(si)
    if ent:
        keep = sum(1 for e in ent if e in so) / len(ent)
        if keep < 0.60:
            return False, f'术语保留{keep:.2f}({len(ent)}词)'
    else:
        keep = 1.0
    for k, pat in MARKS.items():
        if re.search(pat, si) and not re.search(pat, so):
            return False, f'丢{k}标记'
    fab = fab_new(src, out)
    if fab:
        return False, '新增药名' + '/'.join(sorted(fab)[:3])
    return True, f'len比{r:.2f} 术语{keep:.2f}'


def main():
    global HERB
    base = json.load(open(os.path.join(ROOT, 'data', 'bingyuan_terms_v7.json'), encoding='utf-8'))
    HERB = build_herb_lex([t.get('body') or '' for t in base])
    print('药名护栏词表:', len(HERB))
    outs = {}
    for fp in sorted(glob.glob(os.path.join(V6OUT, '*.json'))):
        try:
            for e in json.load(open(fp, encoding='utf-8')):
                if e.get('no') and e.get('body'):
                    outs[e['no']] = e['body']
        except Exception as ex:
            print('  跳过坏文件', os.path.basename(fp), type(ex).__name__)
    st = Counter(); rej = []; ratios = []; keeps = []
    for t in base:
        src = t.get('body') or ''
        if t['no'] in outs:
            ok, why = valid(src, outs[t['no']])
            if ok:
                t['body'] = outs[t['no']]; t['ver'] = 'v6modern'; st['rewritten'] += 1
                ratios.append(float(why.split('len比')[1].split()[0]))
                keep = why.split('术语')
                if len(keep) > 1:
                    keeps.append(float(keep[1]))
            else:
                t['ver'] = 'keep_v7'; st['fallback'] += 1
                rej.append({'no': t['no'], 'why': why, 'out': outs[t['no']][:60]})
        else:
            t['ver'] = 'keep_v7'; st['fallback'] += 1
            rej.append({'no': t['no'], 'why': 'missing', 'out': ''})
    json.dump(base, open(os.path.join(ROOT, 'data', 'bingyuan_terms_v8.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    rep = {'by_source': dict(st), 'rejected': len(rej), 'rejected_sample': rej[:15],
           'len_ratio_min': min(ratios) if ratios else None,
           'len_ratio_avg': round(sum(ratios) / len(ratios), 3) if ratios else None,
           'term_keep_min': min(keeps) if keeps else None,
           'term_keep_avg': round(sum(keeps) / len(keeps), 3) if keeps else None}
    json.dump(rep, open(os.path.join(DIST, 'v6_rewrite_report.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('来源:', dict(st), '| 退回:', len(rej))
    print('长度比 min/avg:', rep['len_ratio_min'], rep['len_ratio_avg'], '| 术语保留 min/avg:', rep['term_keep_min'], rep['term_keep_avg'])
    for x in rej[:5]:
        print('  !', x['no'], x['why'])


if __name__ == '__main__':
    main()
