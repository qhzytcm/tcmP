# -*- coding: utf-8 -*-
"""
D07 中医智能学院 · AI 课程 · 轮次2 · 第2课
倒排索引与 RRF 融合（BUILD IT 教学切片）
========================================
承接 Lesson 1（手写 TF-IDF）。本课解决两个问题：

  1. 速度：全库扫描 O(N) → 倒排索引 O(命中词条数)
     检索 60,000+ 病证单元时，不可能每查一次就跟所有文档算余弦。

  2. 互补：向量检索(语义排序, precision) × 关键词召回(词面精确, recall)
     两路排序怎么合并成一路？—— RRF（Reciprocal Rank Fusion，倒数秩融合），
     只看名次不看分数：score(idx) = Σ 1/(k + rank_i)，k=60 为经验常数。

算法对齐生产引擎 tcmP/scripts/tcm_embed.py：
    FTS5Index.search → 本课 InvertedIndex.query（OR 语义）
    _rrf_fuse        → 本课 rrf_fuse（同公式 1/(k+rank+1)）
    TCMSearchEngine.diagnose = 向量 Top-K + FTS5 召回 → RRF 融合

用法:
  python main.py --demo                       # 4 个内置演示场景
  python main.py "难以入睡 多梦易醒" --top-k 3 # 混合检索
  python main.py --self-test                  # 内置断言自检
  python main.py "心悸" --data ../../tcmP/kg/samples   # 全量真实语料
"""
from __future__ import annotations
import math
import re
import sys
import time


# ───────────────── 1. 分词（与 Lesson 1 / tcm_embed 同算法） ─────────────────
def tokenize(text: str) -> list:
    """英文整词；中文连续段拆字符 bigram"""
    text = (text or "").lower()
    toks = []
    for w in re.findall(r"[a-z0-9]{2,}", text):
        toks.append(w)
    for seg in re.findall(r"[\u4e00-\u9fff]+", text):
        if len(seg) == 1:
            toks.append(seg)
        else:
            toks += [seg[i:i + 2] for i in range(len(seg) - 1)]
    return toks


# ───────────────── 2. TF-IDF 向量（Lesson 1 复用，只保留检索所需） ─────────────────
class TfidfIndex:
    def __init__(self):
        self.df, self.idf, self.vectors, self.n_docs = {}, {}, [], 0

    def fit(self, docs):
        self.n_docs = len(docs)
        doc_tokens = [set(tokenize(d)) for d in docs]
        for toks in doc_tokens:
            for t in toks:
                self.df[t] = self.df.get(t, 0) + 1
        self.idf = {t: math.log((self.n_docs + 1) / (f + 1)) + 1
                    for t, f in self.df.items()}
        self.vectors = [self._vector_of(toks) for toks in doc_tokens]

    def _vector_of(self, toks):
        tf = {}
        for t in toks:
            tf[t] = tf.get(t, 0) + 1
        norm = math.sqrt(sum((v * self.idf[t]) ** 2 for t, v in tf.items())) or 1
        return {t: v * self.idf[t] / norm for t, v in tf.items()}

    def vectorize(self, text):
        tf = {}
        for t in tokenize(text):
            tf[t] = tf.get(t, 0) + 1
        norm = math.sqrt(sum((v * self.idf.get(t, 1)) ** 2
                             for t, v in tf.items())) or 1
        return {t: v * self.idf.get(t, 1) / norm for t, v in tf.items()}

    def cosine(self, a, b):
        if not a or not b:
            return 0.0
        small, large = (a, b) if len(a) < len(b) else (b, a)
        return sum(small[t] * large[t] for t in small if t in large)


# ───────────────── 3. 倒排索引（本课核心 1） ─────────────────
class InvertedIndex:
    """词 → 文档 ID 集合（posting list）。
    正向：文档 → 包含哪些词（建库时一次）；反向：词 → 哪些文档（查询时 O(词条数)）。
    工业实现即 SQLite FTS5 / Lucene / Elasticsearch 的倒排表。"""

    def __init__(self):
        self.postings = {}   # term -> set(doc_idx)

    def build(self, texts):
        """texts: 文档文本列表。每篇文档分词后去重，词指向文档 ID。"""
        for i, text in enumerate(texts):
            for term in set(tokenize(text)):
                self.postings.setdefault(term, set()).add(i)

    def query(self, text, mode="or", limit=None):
        """关键词查询。
        mode="or" ：并集——含任一查询词的文档全部召回（recall 优先）
        mode="and"：交集——含全部查询词的文档（precision 优先）
        返回按文档 ID 排序的列表。"""
        terms = [t for t in set(tokenize(text)) if t in self.postings]
        if not terms:
            return []
        if mode == "and":
            hits = set(self.postings[terms[0]])
            for t in terms[1:]:
                hits &= self.postings[t]
        else:
            hits = set()
            for t in terms:
                hits |= self.postings[t]
        out = sorted(hits)
        return out if limit is None else out[:limit]

    def posting_size(self, term):
        """某个词的倒排表长度（教学演示用：全扫 N vs 倒排查 len）"""
        return len(self.postings.get(term, ()))


# ───────────────── 4. RRF 融合（本课核心 2） ─────────────────
def rrf_fuse(vector_ranked, keyword_hits, k=60, tiebreak=None):
    """倒数秩融合：多路排序 → 一路。
    vector_ranked: [(doc_idx, vec_score), ...] 已按相似度降序
    keyword_hits : 倒排召回文档索引（集合或列表，名次按固定次序）
    tiebreak     : {doc_idx: vec_score}——融合分打平时用向量分数破局
                   （对齐生产引擎 _rrf_fuse 的 (-rrf, -vec) 排序）
    公式: score(d) = Σ_rank 1/(k + rank)   （k=60 经验常数，抑制首位霸权）
    返回 [(doc_idx, rrf_score), ...] 降序。"""
    rank = {}
    for i, (idx, _score) in enumerate(vector_ranked):
        rank[idx] = rank.get(idx, 0.0) + 1.0 / (k + i + 1)
    for j, idx in enumerate(sorted(keyword_hits)):
        rank[idx] = rank.get(idx, 0.0) + 1.0 / (k + j + 1)
    tb = tiebreak or {}
    return sorted(rank.items(),
                  key=lambda kv: (-kv[1], -tb.get(kv[0], 0.0)))


# ───────────────── 5. 混合检索：向量 + 倒排 → RRF ─────────────────
def hybrid_search(query, tfidf, inv, docs, top_k=3, k=60):
    """生产引擎 diagnose() 的教学版：向量 Top-3k 候选 + 倒排召回 → RRF"""
    qv = tfidf.vectorize(query)
    vec_ranked = []
    for i, dv in enumerate(tfidf.vectors):
        s = tfidf.cosine(qv, dv)
        if s > 0:
            vec_ranked.append((i, s))
    vec_ranked.sort(key=lambda x: -x[1])
    inv_hits = inv.query(query, mode="or")
    fused = rrf_fuse(vec_ranked, set(inv_hits), k,
                     tiebreak={i: s for i, s in vec_ranked})
    out = []
    vec_idx = {i for i, _ in vec_ranked[:top_k]}
    for idx, score in fused[:top_k]:
        name, icd, synd, syms, formula = docs[idx]
        out.append({"rank": len(out) + 1, "rrf": round(score, 4),
                    "in_vector": idx in vec_idx, "in_keyword": idx in set(inv_hits),
                    "disease": name, "icd11": icd, "syndrome": synd,
                    "formula": formula})
    return out, vec_ranked, inv_hits


# ───────────────── 6. mini 语料（与 Lesson 1 相同，保证课程连续性） ─────────────────
MINI_CORPUS = [
    ("普通感冒（上呼吸道感染）", "CA00", "风寒束表证",
     "恶寒重 发热轻 无汗 头身疼痛 鼻塞流清涕", "麻黄汤"),
    ("原发性失眠（慢性失眠障碍）", "7A00", "心肾不交证",
     "难以入睡 多梦易醒 心烦不安 五心烦热 心悸健忘 头晕耳鸣 腰膝酸软",
     "黄连阿胶汤合交泰丸"),
    ("偏头痛（无先兆偏头痛）", "8A80", "肝阳上亢证(头部)",
     "偏侧搏动性头痛 胀痛或跳痛 头晕目眩 烦躁易怒 面红目赤 口干口苦",
     "天麻钩藤饮加减"),
    ("原发性高血压", "BA00", "肝阳上亢证",
     "头晕头痛且胀 面红目赤 心烦易怒 耳鸣如潮 失眠多梦 口干口苦",
     "天麻钩藤饮"),
    ("支气管哮喘", "CA23.32", "寒哮证（冷哮）",
     "呼吸急促喉中哮鸣有声 咳痰清稀色白泡沫状 遇寒触发或加重 胸闷如窒 喘不得卧",
     "射干麻黄汤"),
]


def corpus_texts(docs):
    return [f"疾病：{d[0]}；症状：{d[3]}；证候：{d[2]}；方剂：{d[4]}"
            for d in docs]


def load_full_corpus(kg_dir):
    """读取真实 tcmP/kg/samples/dsu-samples-*.json 全量病证单元"""
    import json
    from pathlib import Path
    docs, texts = [], []
    for f in sorted(Path(kg_dir).glob("dsu-samples-*.json")):
        for dsu in json.loads(f.read_text(encoding="utf-8")):
            ds = dsu["disease_side"]
            ss = dsu.get("syndrome_side", {})
            cl = dsu.get("clinical", {})
            syms = " ".join((ds.get("key_symptoms", []) or [])
                            + (ss.get("key_symptoms", []) or []))
            doc = (ds.get("disease_name", ""), ds.get("icd11_code", ""),
                   ss.get("syndrome_name", ""), syms,
                   cl.get("recommended_formula", ""))
            docs.append(doc)
            texts.append(f"疾病：{doc[0]}；症状：{syms}；证候：{doc[2]}；方剂：{doc[4]}")
    return docs, texts


# ───────────────── 7. 演示场景 ─────────────────
def demo(docs=None, texts=None):
    docs = docs or MINI_CORPUS
    texts = texts or corpus_texts(docs)
    n = len(docs)
    tfidf = TfidfIndex()
    tfidf.fit(texts)
    inv = InvertedIndex()
    inv.build(texts)

    print(f"📚 语料：{n} 个病证单元\n")

    # 场景1：速度——全扫 vs 倒排
    print("── 场景1 · 速度：全库扫描 vs 倒排索引 ──")
    query = "难以入睡"
    terms = [t for t in set(tokenize(query)) if t in inv.postings]
    scan_work = n
    inv_work = sum(inv.posting_size(t) for t in terms) + len(terms)
    t0 = time.perf_counter()
    for _ in range(200):
        _ = [tfidf.cosine(tfidf.vectorize(query), dv) for dv in tfidf.vectors]
    t_vec = (time.perf_counter() - t0) / 200
    t0 = time.perf_counter()
    for _ in range(2000):
        _ = inv.query(query, mode="or")
    t_inv = (time.perf_counter() - t0) / 2000
    print(f"  查询词: {terms}")
    print(f"  计算量: 全扫 {scan_work} 次余弦 vs 倒排查 {inv_work} 个条目")
    print(f"  实测耗时: 向量全扫 {t_vec*1e6:.0f}µs/次 vs 倒排 {t_inv*1e6:.0f}µs/次"
          f"（{t_vec/t_inv:.0f}x）\n")

    # 场景2：精确词——倒排的舞台
    print("── 场景2 · 精确词「麻黄汤」：两路召回对比 ──")
    inv_hits = inv.query("麻黄汤", mode="or")
    qv = tfidf.vectorize("麻黄汤")
    vec_top = sorted(((i, tfidf.cosine(qv, dv)) for i, dv in enumerate(tfidf.vectors)),
                     key=lambda x: -x[1])[:2]
    print(f"  倒排召回: {[(docs[i][0]) for i in inv_hits]}")
    print(f"  向量Top2: {[(docs[i][0], round(s, 4)) for i, s in vec_top]}\n")

    # 场景3：语义词——向量 vs 倒排 vs RRF 融合
    print("── 场景3 · 语义查询「难以入睡 多梦易醒 心烦不安」：三路对比 ──")
    qv = tfidf.vectorize("难以入睡 多梦易醒 心烦不安")
    vec_ranked = sorted(((i, tfidf.cosine(qv, dv)) for i, dv in enumerate(tfidf.vectors)
                         if tfidf.cosine(qv, dv) > 0), key=lambda x: -x[1])
    inv_hits = inv.query("难以入睡 多梦易醒 心烦不安", mode="or")
    fused = rrf_fuse(vec_ranked, set(inv_hits))
    print(f"  纯向量Top3: {[(docs[i][0], round(s, 4)) for i, s in vec_ranked[:3]]}")
    print(f"  倒排召回: {[docs[i][0] for i in inv_hits]}")
    print(f"  RRF融合Top3: {[(docs[i][0], round(s, 4)) for i, s in fused[:3]]}\n")

    # 场景4：AND vs OR——精确与召回的对立
    print("── 场景4 · 「恶寒 无汗」：AND 交集 vs OR 并集 ──")
    and_hits = inv.query("恶寒 无汗", mode="and")
    or_hits = inv.query("恶寒 无汗", mode="or")
    print(f"  AND: {[docs[i][0] for i in and_hits]}")
    print(f"  OR : {[docs[i][0] for i in or_hits]}")


def self_test():
    tfidf = TfidfIndex()
    tfidf.fit(corpus_texts(MINI_CORPUS))
    inv = InvertedIndex()
    inv.build(corpus_texts(MINI_CORPUS))

    # 断言1：倒排表结构——词指向包含它的文档
    assert 0 in inv.postings["恶寒"] and 1 not in inv.postings["恶寒"], \
        "「恶寒」应只命中普通感冒(0)"
    assert 1 in inv.postings["失眠"] and 3 in inv.postings["失眠"], \
        "「失眠」应命中失眠(病名)与高血压(症状)"
    # 断言2：OR 并集 vs AND 交集
    or_hits = inv.query("恶寒 失眠", mode="or")
    and_hits = inv.query("恶寒 失眠", mode="and")
    assert 0 in or_hits and 1 in or_hits and 3 in or_hits, "OR 应召回全部"
    assert and_hits == [], "AND（恶寒+失眠）应无交集"
    # 断言3：RRF 融合公式——两路都命中的排最前
    fused = rrf_fuse([(1, 0.4), (3, 0.2)], {0, 1})
    assert fused[0][0] == 1 and fused[0][1] > fused[1][1], f"融合排序错误: {fused}"
    # 断言4：融合分 = 1/(k+r1) + 1/(k+r2) 精确值
    f = rrf_fuse([(0, 0.5)], {0}, k=60)
    assert abs(f[0][1] - (1 / 61 + 1 / 61)) < 1e-9, f"RRF 公式错误: {f}"
    # 断言5：混合检索——失眠查询融合后 Top1 失眠，且双路命中标记正确
    out, _, inv_hits = hybrid_search("难以入睡 多梦易醒 心烦不安", tfidf, inv,
                                     MINI_CORPUS, top_k=3)
    assert out[0]["disease"].startswith("原发性失眠"), f"混合检索失败: {out}"
    assert out[0]["in_vector"] and out[0]["in_keyword"], \
        "失眠应双路命中（向量+关键词）"
    print("✅ 全部 5 项断言通过")


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        self_test()
        sys.exit(0)

    import argparse
    ap = argparse.ArgumentParser(description="手写倒排索引 + RRF 融合（教学切片）")
    ap.add_argument("query", nargs="?", default="",
                    help="症状查询（空格分隔）；留空跑 --demo")
    ap.add_argument("--top-k", type=int, default=3)
    ap.add_argument("--data", default="",
                    help="tcmP/kg/samples 目录路径；留空用内置 mini 语料")
    ap.add_argument("--demo", action="store_true")
    args = ap.parse_args()

    if args.data:
        docs, texts = load_full_corpus(args.data)
        print(f"📚 全量语料：{len(docs)} 个病证单元（{args.data}）")
    else:
        docs, texts = MINI_CORPUS, corpus_texts(MINI_CORPUS)

    if args.demo or not args.query:
        demo(docs, texts)
        sys.exit(0)

    tfidf = TfidfIndex()
    tfidf.fit(texts)
    inv = InvertedIndex()
    inv.build(texts)
    out, _, _ = hybrid_search(args.query, tfidf, inv, docs, args.top_k)
    print(f"\n═══ 混合检索（向量 + 倒排 → RRF）「{args.query}」═══")
    for r in out:
        tag = ("向量+关键词" if r["in_vector"] and r["in_keyword"]
               else "仅向量" if r["in_vector"] else "仅关键词")
        print(f"  {r['rank']}. [RRF {r['rrf']:.4f} | {tag}] {r['disease']} "
              f"({r['icd11']}) — {r['syndrome']} → {r['formula']}")
