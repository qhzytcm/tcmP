# -*- coding: utf-8 -*-
"""
S22 通过 FTS5 校正完善（V5）
① harvest：以内网 ICD-11 API 检索中文标题（探针=1831 词目 + 常用医学术语），缓存可续跑
② align  ：FTS5(CJK 二元组) 索引 中文标题 + 平台 KB 术语 → 词目对齐 + 单字差校正 + ICD-11 标注完善
用法： python s22_fts5_v5.py harvest [--limit N]
       python s22_fts5_v5.py align
输出： data/icd_cn_titles.json · data/bingyuan_terms_v7.json · dist/fts5_v5_report.json
"""
import os, re, sys, json, sqlite3, time, argparse
from collections import Counter
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
DIST = os.path.join(ROOT, 'dist'); os.makedirs(DIST, exist_ok=True)
CACHE = os.path.join(ROOT, 'data', 'icd_cn_titles.json')
PROBES = os.path.join(ROOT, 'data', 'icd_probe_cache.json')

PROBE_EXTRA = list('寒热虚实表里阴阳气血痰瘀湿燥火风暑毒虫痛疹疮痈疽疳痢疟疸淋浊带崩漏汗咳喘呕吐泻痢便秘惊痫癫痫痹痿癃淋痈疔疖癣疥麻痘痧霍乱瘴瘟肿胀痞积症瘕疝痔瘘脱肛惊悸怔忡健忘失眠多梦眩晕耳鸣目赤鼻渊喉痹牙痛口疮') + \
    ['感冒', '咳嗽', '哮喘', '胃痛', '腹泻', '黄疸', '水肿', '中风', '消渴', '痹症', '虚劳', '血证',
     '心悸', '胸痹', '头痛', '眩晕', '厥证', '郁证', '癫狂', '痫病', '痴呆', '肺痨', '肺痈', '肺胀',
     '附骨疽', '肠痈', '乳痈', '蛇串疮', '湿疹', '风疹', '痤疮', '斑秃', '耳鸣', '鼻炎', '咽炎',
     '湿热', '风寒', '风热', '肝郁', '脾虚', '肾虚', '血瘀', '气滞', '阴虚', '阳虚']


def bgs(s):
    s = re.sub(r'[\s（）()、，。；：·\-—/]', '', s or '')
    return [s[i:i + 2] for i in range(len(s) - 1)] if len(s) > 1 else ([s] if s else [])


def overlap(a, b):
    ba, bb = Counter(bgs(a)), Counter(bgs(b))
    return sum(min(ba[k], bb[k]) for k in ba) / max(1, sum(ba.values()))


def harvest(limit=0):
    from icd11_client import ICD11Client
    cli = ICD11Client()
    titles = json.load(open(CACHE, encoding='utf-8')) if os.path.exists(CACHE) else {}
    done = json.load(open(PROBES, encoding='utf-8')) if os.path.exists(PROBES) else []
    dset = set(done)
    heads = [t['head'] for t in json.load(open(os.path.join(ROOT, 'data', 'bingyuan_terms_v6.json'), encoding='utf-8'))]
    probes = [p for p in (heads + PROBE_EXTRA) if p not in dset]
    if limit:
        probes = probes[:limit]
    print(f'待检索探针 {len(probes)} | 已缓存标题 {len(titles)}')
    t0 = time.time()
    for i, q in enumerate(probes):
        try:
            for r in cli.search_cn(q, limit=50):
                tc = (r.get('title_cn') or '').strip()
                if tc:
                    titles[tc] = r.get('foundation_id', '')
        except Exception:
            pass
        dset.add(q)
        if (i + 1) % 100 == 0:
            json.dump(titles, open(CACHE, 'w', encoding='utf-8'), ensure_ascii=False)
            json.dump(sorted(dset), open(PROBES, 'w', encoding='utf-8'), ensure_ascii=False)
            print(f'  ..{i+1}/{len(probes)} 标题累计 {len(titles)} 用时{int(time.time()-t0)}s')
    json.dump(titles, open(CACHE, 'w', encoding='utf-8'), ensure_ascii=False)
    json.dump(sorted(dset), open(PROBES, 'w', encoding='utf-8'), ensure_ascii=False)
    print(f'采集完成：探针 {len(dset)} | 中文标题 {len(titles)} 用时{int(time.time()-t0)}s')


def align():
    titles = json.load(open(CACHE, encoding='utf-8')) if os.path.exists(CACHE) else {}
    con = sqlite3.connect(':memory:')
    con.execute("CREATE VIRTUAL TABLE t USING fts5(bg, code, title)")
    for tc, fid in titles.items():
        con.execute("INSERT INTO t VALUES (?,?,?)", (' '.join(bgs(tc)), str(fid), tc))
    kb = 0
    try:
        for f in sorted(os.listdir(os.path.join(ROOT, 'kg', 'samples'))):
            for d in json.load(open(os.path.join(ROOT, 'kg', 'samples', f), encoding='utf-8')):
                for nm in [d.get('disease_side', {}).get('disease_name', ''),
                           d.get('syndrome_side', {}).get('syndrome_name', ''),
                           d.get('clinical', {}).get('recommended_formula', '')]:
                    if nm:
                        con.execute("INSERT INTO t VALUES (?,?,?)", (' '.join(bgs(nm)), '', nm)); kb += 1
    except Exception:
        pass
    con.commit()
    # foundation_id → 正式 ICD-11 编码（本地 MMS 库 entities.id → code）
    codemap = {}
    try:
        d = sqlite3.connect(os.path.join(ROOT, 'data', 'icd11_mms.db'))
        codemap = {str(i): c for i, c in d.execute("SELECT id, code FROM entities WHERE code IS NOT NULL AND code<>''")}
        d.close()
    except Exception as e:
        print('  codemap 跳过:', type(e).__name__)
    print(f'FTS5 索引：中文标题 {len(titles)} + KB 术语 {kb} | 编码映射 {len(codemap)}')

    terms = json.load(open(os.path.join(ROOT, 'data', 'bingyuan_terms_v6.json'), encoding='utf-8'))
    st = Counter(); samples = []
    for t in terms:
        head = t['head']
        q = ' OR '.join(f'"{g}"' for g in list(dict.fromkeys(bgs(head)))[:12]) or f'"{head}"'
        try:
            rows = con.execute("SELECT code, title FROM t WHERE t MATCH ? ORDER BY rank LIMIT 8", (q,)).fetchall()
        except sqlite3.OperationalError:
            rows = []
        best = None
        for code, title in rows:
            ov = overlap(head, title)
            if best is None or ov > best[0]:
                best = (ov, code, title)
        t['fts5'] = None
        strict = best and (len(head) >= 3 or len(best[2]) <= 4)
        if strict and best[0] >= 0.6:
            ov, code, title = best
            t['fts5'] = {'fid': code, 'code': codemap.get(str(code), ''), 'title': title, 'overlap': round(ov, 3)}
            st['对齐'] += 1
            if len(head) == len(title) and sum(1 for x, y in zip(head, title) if x != y) == 1:
                t['head'] = title; st['词目归一'] += 1
            if len(samples) < 10:
                samples.append((t['no'], head, title, code, round(ov, 3)))
        else:
            st['未对齐'] += 1
    json.dump(terms, open(os.path.join(ROOT, 'data', 'bingyuan_terms_v7.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    rep = {'lexicon': len(titles) + kb, 'aligned': st['对齐'], 'headword_norm': st['词目归一'],
           'unaligned': st['未对齐'], 'samples': samples}
    json.dump(rep, open(os.path.join(DIST, 'fts5_v5_report.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('对齐:', st['对齐'], '| 词目归一:', st['词目归一'], '| 未对齐:', st['未对齐'])
    for s in samples:
        print('  ', s)


def build_lexicon(titles):
    """权威术语词表：ICD-11 中文标题切分 + KB 术语"""
    L = set()
    for tc in titles:
        for part in re.split(r'[、，,（）()；;·\-—/]', tc):
            p = part.strip()
            if 2 <= len(p) <= 6:
                L.add(p)
        if 2 <= len(tc) <= 6:
            L.add(tc)
    try:
        for f in sorted(os.listdir(os.path.join(ROOT, 'kg', 'samples'))):
            for d in json.load(open(os.path.join(ROOT, 'kg', 'samples', f), encoding='utf-8')):
                for nm in [d.get('disease_side', {}).get('disease_name', ''),
                           d.get('syndrome_side', {}).get('syndrome_name', ''),
                           d.get('clinical', {}).get('recommended_formula', '')]:
                    for part in re.split(r'[、，,（）()；;·\-—/]', nm or ''):
                        if 2 <= len(part.strip()) <= 6:
                            L.add(part.strip())
    except Exception:
        pass
    return L


def annotate():
    """通过 tcmP 平台 FTS5 引擎检索权威病证单元 → 为词条附「参考标注」（不改写正文）。
    查询串 = 词目 + 病状段文本；命中按与检索结果的字面重合度过滤。"""
    import urllib.request, urllib.parse
    terms = json.load(open(os.path.join(ROOT, 'data', 'bingyuan_terms_v7.json'), encoding='utf-8'))

    def sect(b):
        m = re.search(r'病[状默送肤选迭达跋然][：:]?(.*?)(?:[治洛活浩照浴跆沼陪邵路阁]法|$)', b or '')
        return (m.group(1) if m else '')[:60]

    def q(text):
        url = 'http://127.0.0.1:8300/semantic-search?q=' + urllib.parse.quote(text[:60])
        try:
            return json.loads(urllib.request.urlopen(url, timeout=20).read().decode('utf-8')).get('results') or []
        except Exception:
            return []

    st = Counter(); samples = []
    for t in terms:
        t['ref'] = None
        query = t['head'] + ' ' + sect(t['body'])
        res = q(query)
        if not res:
            st['无结果'] += 1; continue
        top = res[0]
        nm = (top.get('disease', '') or '') + (top.get('syndrome', '') or '')
        ov = overlap(t['body'][:120], nm)
        if ov >= 0.34:
            t['ref'] = {'dsu_id': top.get('dsu_id'), 'disease': top.get('disease'),
                        'syndrome': top.get('syndrome'), 'icd11': top.get('icd11_code'),
                        'overlap': round(ov, 3)}
            st['标注'] += 1
            if len(samples) < 10:
                samples.append((t['no'], t['head'], top.get('disease'), top.get('icd11_code'), top.get('syndrome'), round(ov, 3)))
        else:
            st['弱相关'] += 1
    json.dump(terms, open(os.path.join(ROOT, 'data', 'bingyuan_terms_v7.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    print('FTS5 检索标注:', dict(st))
    for s in samples:
        print('  ', s)
    rep = json.load(open(os.path.join(DIST, 'fts5_v5_report.json'), encoding='utf-8')) if os.path.exists(os.path.join(DIST, 'fts5_v5_report.json')) else {}
    rep['ref_annotated'] = st['标注']; rep['ref_samples'] = samples
    json.dump(rep, open(os.path.join(DIST, 'fts5_v5_report.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('mode', choices=['harvest', 'align', 'annotate'])
    ap.add_argument('--limit', type=int, default=0)
    a = ap.parse_args()
    {'harvest': lambda: harvest(a.limit), 'align': align, 'annotate': annotate}[a.mode]()


def fix(apply=False):
    """（已弃用·保留供研究）术语级单字差校正：实测误纠率高，不纳入 V5 流水线。"""
    import jieba
    from collections import defaultdict
    jieba.initialize()
    JF = {w for w, f in jieba.dt.FREQ.items() if f >= 100}
    titles = json.load(open(CACHE, encoding='utf-8')) if os.path.exists(CACHE) else {}
    L = build_lexicon(titles)
    print(f'权威术语词表: {len(L)} 条')
    terms = json.load(open(os.path.join(ROOT, 'data', 'bingyuan_terms_v7.json'), encoding='utf-8'))

    # 掩码键索引：每个词每个位置打一个 *，检出单字差候选
    mask = defaultdict(list)
    support = Counter()
    for w in L:
        for i in range(len(w)):
            mask[w[:i] + '\x00' + w[i + 1:]].append(w)
        for n in range(2, min(6, len(w)) + 1):
            for i in range(len(w) - n + 1):
                support[w[i:i + n]] += 1

    # 一遍收集候选 n-gram 频次（仅纯汉字）
    CJK = re.compile(r'^[\u4e00-\u9fff]+$')
    NGRAM = (4, 3)
    cnt = Counter()
    chs = Counter()
    for t in terms:
        b = t.get('body') or ''
        for ch in b:
            if '\u4e00' <= ch <= '\u9fff':
                chs[ch] += 1
        for n in NGRAM:
            for i in range(len(b) - n + 1):
                g = b[i:i + n]
                if CJK.match(g) and g not in L and g not in JF:
                    cnt[g] += 1
    TOP = [c for c, _ in chs.most_common(700)]

    def is_frag(g):
        """g 是通用词/词表词的片段 → 拒绝（防把 '津液不' 纠成 '津液证'）"""
        for c in TOP:
            if (c + g) in JF or (g + c) in JF:
                return True
        return False

    fixes = {}
    for g, c0 in cnt.items():
        if cnt[g] < 2 or is_frag(g):
            continue
        cands = set()
        for i in range(len(g)):
            for c in mask.get(g[:i] + '\x00' + g[i + 1:], ()):
                if sorted(c) != sorted(g):
                    cands.add(c)
        if cands:
            best = max(cands, key=lambda x: support.get(x, 0))
            if support.get(best, 0) >= 3:
                fixes[g] = best

    print(f'候选纠错对 {len(fixes)} 种 | 覆盖语料 n-gram {sum(cnt[g] for g in fixes)} 次')
    for k in sorted(fixes, key=lambda x: -cnt[x])[:25]:
        print(f'   {k} → {fixes[k]}  (x{cnt[k]})')
    if apply:
        chg = 0
        for t in terms:
            b = t.get('body') or ''
            nb = b
            for g, c in fixes.items():
                if g in nb:
                    nb = nb.replace(g, c)
            if nb != b:
                t['body'] = nb; chg += 1
        json.dump(terms, open(os.path.join(ROOT, 'data', 'bingyuan_terms_v7.json'), 'w', encoding='utf-8'),
                  ensure_ascii=False, indent=1)
        print(f'已写回 v7，改动条目 {chg}')
        json.dump({'pairs': len(fixes), 'entries_changed': chg,
                   'samples': {k: fixes[k] for k in list(fixes)[:40]}},
                  open(os.path.join(DIST, 'fts5_termfix_report.json'), 'w', encoding='utf-8'),
                  ensure_ascii=False, indent=1)
