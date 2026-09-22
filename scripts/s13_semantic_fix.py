# -*- coding: utf-8 -*-
"""
S13 语义向量二次矫正 v2（保守版，安全）
原理：把片段映射到**字符 n-gram 向量空间**，只在"真替换"且频率显著时才纠错。
安全约束（吸取 v1 教训）：
  · 词目**不自动合并**（一字之差常是不同病名，如 上焦寒≠上焦热）——仅产出复核清单
  · 正文纠错须同时满足：等长 · 编辑距离1 · **非同字集**（排除轮转伪纠错，如 治法外治↔法外治法）
    · 字符二元组 Jaccard ≥ cos · 频率比 ≥ ratio · 候选绝对频 ≥ min_anchor_freq
输入：data/bingyuan_terms_icd.json   输出：data/bingyuan_terms_v2.json + dist/semantic_fix_log.json
"""
import os, json, argparse
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, 'dist'); os.makedirs(DIST, exist_ok=True)
TxtD = os.path.join(ROOT, 'data', 'bingyuan_txt')

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def edit_distance_le1(a, b):
    return len(a) == len(b) and sum(1 for x, y in zip(a, b) if x != y) == 1


def skipkeys(g):
    return {g[:i] + g[i + 1:] for i in range(len(g))}


def bigrams(s):
    return {s[i:i + 2] for i in range(len(s) - 1)} or {s}


def jaccard(a, b):
    return len(a & b) / len(a | b) if a and b else 0.0


def ngram_counts(text, ns=(3, 4, 5, 6)):
    c = Counter()
    for n in ns:
        for i in range(len(text) - n + 1):
            c[text[i:i + n]] += 1
    return c


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--terms', default=os.path.join(ROOT, 'data', 'bingyuan_terms_icd.json'))
    ap.add_argument('--out', default=os.path.join(ROOT, 'data', 'bingyuan_terms_v2.json'))
    ap.add_argument('--min-anchor-freq', type=int, default=8)
    ap.add_argument('--rare-char-max', type=int, default=30,
                    help='源字语料频次上限：超过则视为真词，不纠')
    a = ap.parse_args()

    terms = json.load(open(a.terms, encoding='utf-8'))
    for t in terms:
        t['body'] = t.get('body') or ''.join(t.get('sections', {}).values())
    corpus = [json.loads(l)['text'] for l in open(os.path.join(TxtD, 'corpus.jsonl'), encoding='utf-8')]
    full = ''.join(corpus)
    freq = ngram_counts(full)
    print(f'词条 {len(terms)} | 语料 {len(full)} 字 | n-gram {len(freq)}')

    log = {'headword_review': [], 'body_fix': []}

    # ── ① 词目复核清单（仅诊断，不自动合并）──
    uniq = sorted({t['head'] for t in terms})
    X = TfidfVectorizer(analyzer='char', ngram_range=(1, 2), min_df=1).fit_transform(uniq)
    sim = cosine_similarity(X)
    for i in range(len(uniq)):
        for j in range(i + 1, len(uniq)):
            if sim[i, j] >= 0.6 and len(uniq[i]) == len(uniq[j]) and edit_distance_le1(uniq[i], uniq[j]):
                log['headword_review'].append({'a': uniq[i], 'b': uniq[j],
                                               'cos': round(float(sim[i, j]), 3),
                                               'freq_a': full.count(uniq[i]), 'freq_b': full.count(uniq[j])})
    print('词目复核对:', len(log['headword_review']), '(不自动改)')

    # ── ② 正文纠错：仅当「纠后成为通用中文词、纠前不是」才自动应用（高精度）──
    # 教训：纯语料频率会强化系统性 OCR 错误(源辞典→源静典反向)；通用字二元组亦不稳(病源辞→病源山)。
    #       故加**词典成员资格**硬门限：cand 必须是 jieba 词且频次达标，g 不是词。
    import jieba
    jieba.initialize()
    JFREQ = {w: f for w, f in jieba.dt.FREQ.items() if f >= 100}
    charfreq = Counter(full)
    RARE_CHAR_MAX = a.rare_char_max
    anchors = defaultdict(set)
    for g, f in freq.items():
        if f >= a.min_anchor_freq:
            for k in skipkeys(g):
                anchors[k].add(g)
    fixes, review = {}, []
    for g, f in freq.items():
        L = len(g)
        if L < 2 or L > 4 or f > 50 or g in JFREQ:      # 源已是词典词 → 不纠
            continue
        gs = sorted(g)
        best = None
        for k in skipkeys(g):
            for cand in anchors.get(k, ()):
                if cand == g or len(cand) != L or cand not in JFREQ:
                    continue
                if sorted(cand) == gs or not edit_distance_le1(g, cand):
                    continue
                i = next(x for x in range(L) if g[x] != cand[x])
                if charfreq.get(g[i], 0) > RARE_CHAR_MAX:
                    continue
                if best is None or JFREQ[cand] > JFREQ[best]:
                    best = cand
        if best:
            fixes[g] = best
        elif f >= a.min_anchor_freq:
            review.append({'gram': g, 'corpus_freq': f})
    print('正文片段纠错(词典门限后):', len(fixes), '条 | 复核候选:', len(review))

    def fix_text(s):
        s2 = s
        for g, c in sorted(fixes.items(), key=lambda kv: -len(kv[0])):
            if g in s2:
                if len(log['body_fix']) < 400:
                    log['body_fix'].append({'from': g, 'to': c, 'freq_from': freq[g], 'freq_to': freq[c]})
                s2 = s2.replace(g, c)
        return s2

    changed_body = 0
    for t in terms:
        nb = fix_text(t['body'])
        if nb != t['body']:
            t['orig_body'] = t['body']; t['body'] = nb; changed_body += 1
        if isinstance(t.get('sections'), dict):
            for k in ('病源', '病状', '治法'):
                if k in t['sections']:
                    t['sections'][k] = fix_text(t['sections'][k])

    log['body_review'] = review[:400]
    json.dump(terms, open(a.out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    json.dump({'body_ngram_fixes': len(fixes), 'terms_body_changed': changed_body,
               'headword_review_pairs': len(log['headword_review']),
               'body_review_candidates': len(review),
               'anchor_min_freq': a.min_anchor_freq,
               'rare_char_max': a.rare_char_max, 'log': log},
              open(os.path.join(DIST, 'semantic_fix_log.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    print(f'正文改动 {changed_body} 条 → {a.out}')
    print('正文纠错样例:', [(x['from'], x['to']) for x in log['body_fix'][:8]])


if __name__ == '__main__':
    main()
