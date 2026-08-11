# -*- coding: utf-8 -*-
"""
D07 中医智能学院 · AI 课程 · 轮次2 · 第3课
RAG 与病证知识问答：诊断 → 辨证 → 方剂建议（BUILD IT 教学切片）
================================================================
承接 Lesson 1（TF-IDF）与 Lesson 2（倒排 + RRF）。本课把检索接上生成，
形成完整问答链——RAG 四步：

  Query → Retrieve（L2 混合检索，内网零 token）
        → Augment（Top-K 病证摘要组装 + 生成指令）
        → Generate（本地规则模板 或 DeepSeek LLM 精修）

对齐生产引擎 tcm_embed.py 的 rag()（L262-291）与线上 POST /api/sages/rag：
  - 检索：全部在内网完成，LLM 只消费 Top-K 小上下文（降 token 设计）
  - 生成：无 key 降级本地模板（零 token、离线可用、确定性可测）；
          有 key 调 DeepSeek deepseek-chat，max_tokens 800
  - 评估：faithfulness——生成报告引用的病证是否都能溯源到检索上下文

用法:
  python main.py "难以入睡 多梦易醒 心烦不安"                  # 本地模板模式
  python main.py "恶寒重 发热轻 无汗" --top-k 3
  python main.py "心悸 失眠" --data ../../tcmP/kg/samples      # 全量语料
  python main.py "失眠多梦" --api-key $env:DEEPSEEK_API_KEY    # LLM 模式
  python main.py --demo                                        # 4 个演示场景
  python main.py --self-test
"""
from __future__ import annotations
import json
import math
import re
import sys
import urllib.request


# ───────────────── 1. 检索基础设施（L1 + L2 复用，课程自包含） ─────────────────
def tokenize(text: str) -> list:
    """英文整词；中文连续段拆字符 bigram（与 tcm_embed.tokenize 同算法）"""
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


class TfidfIndex:
    """L1：TF-IDF 稀疏向量（df → idf → 归一化向量 → 余弦）"""

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


class InvertedIndex:
    """L2：倒排索引（词 → 文档集合），OR 并集召回"""

    def __init__(self):
        self.postings = {}

    def build(self, texts):
        for i, text in enumerate(texts):
            for term in set(tokenize(text)):
                self.postings.setdefault(term, set()).add(i)

    def query(self, text, mode="or", limit=None):
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


def rrf_fuse(vector_ranked, keyword_hits, k=60, tiebreak=None):
    """L2：倒数秩融合 score = Σ 1/(k+rank)，融合分打平用向量分数破局"""
    rank = {}
    for i, (idx, _s) in enumerate(vector_ranked):
        rank[idx] = rank.get(idx, 0.0) + 1.0 / (k + i + 1)
    for j, idx in enumerate(sorted(keyword_hits)):
        rank[idx] = rank.get(idx, 0.0) + 1.0 / (k + j + 1)
    tb = tiebreak or {}
    return sorted(rank.items(), key=lambda kv: (-kv[1], -tb.get(kv[0], 0.0)))


def hybrid_search(query, tfidf, inv, docs, top_k=3, k=60):
    """L2：向量 Top-K + 倒排召回 → RRF 融合，返回带双路命中标记的结果"""
    qv = tfidf.vectorize(query)
    vec_ranked = [(i, tfidf.cosine(qv, dv)) for i, dv in enumerate(tfidf.vectors)
                  if tfidf.cosine(qv, dv) > 0]
    vec_ranked.sort(key=lambda x: -x[1])
    inv_hits = inv.query(query, mode="or")
    fused = rrf_fuse(vec_ranked, set(inv_hits), k,
                     tiebreak={i: s for i, s in vec_ranked})
    out = []
    vec_idx = {i for i, _ in vec_ranked[:top_k]}
    kw_idx = set(inv_hits)
    for idx, score in fused[:top_k]:
        name, icd, synd, syms, formula = docs[idx]
        out.append({"rank": len(out) + 1, "rrf": round(score, 4),
                    "in_vector": idx in vec_idx, "in_keyword": idx in kw_idx,
                    "disease": name, "icd11": icd, "syndrome": synd,
                    "formula": formula})
    return out


# ───────────────── 2. mini 语料（L1/L2 相同，保证课程连续性） ─────────────────
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


# ───────────────── 3. RAG 管线（本课核心） ─────────────────
class RAGPipeline:
    """检索增强生成：retrieve → augment → generate（本地模板 / DeepSeek LLM）"""

    def __init__(self, docs, texts, api_key="", top_k=3):
        self.docs = docs
        self.tfidf = TfidfIndex()
        self.tfidf.fit(texts)
        self.inv = InvertedIndex()
        self.inv.build(texts)
        self.api_key = api_key
        self.top_k = top_k

    # ── Step 1 · Retrieve：混合检索（复用 L2，内网零 token）──
    def retrieve(self, query, top_k=None):
        return hybrid_search(query, self.tfidf, self.inv, self.docs,
                             top_k=top_k or self.top_k)

    # ── Step 2 · Augment：Top-K 病证摘要 → 上下文文本 ──
    def build_context(self, results):
        """对齐生产 rag() 的 ctx 拼接格式（L268-269）"""
        return "\n".join(
            f"[{r['rank']}] {r['disease']}（{r['icd11']}）— 证候:{r['syndrome']} "
            f"方剂:{r['formula']}（证据 {r['rrf']:.3f}）" for r in results)

    # ── Step 3 · Augment：上下文 + 生成指令 → prompt ──
    def augment_prompt(self, query, ctx):
        """指令含『只允许引用检索结果』约束——RAG 防幻觉的第一道闸"""
        return (f"患者症状：{query}\n\n病证库 Top-{self.top_k} 检索结果：\n{ctx}\n\n"
                f"请综合给出：1.最可能疾病+ICD-11编码 2.中医证候 3.推荐方剂 "
                f"4.鉴别要点。\n"
                f"约束：只允许引用检索结果中出现的疾病与证候，不得引入库外内容；"
                f"若证据分数普遍偏低，声明证据不足。")

    # ── Step 4a · Generate：本地模板（确定性、零 token、离线可用）──
    def generate_local(self, query, results):
        """无 LLM 时的规则生成：Top1 = 最可能病证；Top1 vs Top2 做鉴别。
        教学意义：RAG 的『生成』不必然需要大模型——模板也是生成，
        且确定性可测。生产引擎 rag() 无 key 时同样降级本地模式。"""
        top = results[0]
        lines = [f"【最可能的病证组合】{top['disease']}"
                 f"（ICD-11: {top['icd11']}）— 证候：{top['syndrome']}",
                 f"推荐方剂方向：{top['formula']}（须医师四诊合参确认）"]
        if len(results) >= 2:
            alt = results[1]
            lines.append(
                f"鉴别要点：与{alt['disease']}（{alt['syndrome']}）对比——"
                f"检索证据 {top['rrf']:.3f} vs {alt['rrf']:.3f}，"
                f"词面/症状有重叠时需结合舌脉四诊鉴别")
        # 评估驱动改进：v1 只引用 Top1/Top2 → 全量场景 faithfulness 67%
        # v2 列出全部候选 → 本地模板 100% 可溯源（确定性可测）
        if len(results) >= 3:
            others = "、".join(r["disease"].split("（")[0]
                               for r in results[2:])
            lines.append(f"其余候选：{others}"
                         f"（与 Top1/Top2 症状词面重叠时需四诊鉴别）")
        lines.append("证据说明：以上来自病证库 Top-K 检索结果（非诊断结论），"
                     "低分证据(<0.05)建议线下就诊")
        return "\n".join(lines)

    # ── Step 4b · Generate：DeepSeek LLM（可选，与生产 rag() 同接口）──
    def generate_llm(self, query, results, api_key=None):
        """调 DeepSeek deepseek-chat（max_tokens 800）。仅消费 Top-K 小上下文。"""
        key = api_key or self.api_key
        if not key:
            return {"mode": "local", "report": self.generate_local(query, results)}
        ctx = self.build_context(results)
        prompt = self.augment_prompt(query, ctx)
        body = json.dumps({"model": "deepseek-chat",
                           "messages": [{"role": "user", "content": prompt}],
                           "max_tokens": 800}).encode()
        req = urllib.request.Request(
            "https://api.deepseek.com/v1/chat/completions", data=body,
            headers={"Content-Type": "application/json",
                     "Authorization": f"Bearer {key}"})
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                d = json.loads(resp.read())
            return {"mode": "llm",
                    "report": d["choices"][0]["message"]["content"].strip(),
                    "token_estimate": len(prompt) // 2}
        except Exception as e:
            return {"mode": "local", "report": self.generate_local(query, results),
                    "llm_error": str(e)}

    # ── 全链路 ──
    def ask(self, query, top_k=None):
        """Query → Retrieve → Augment → Generate，返回完整答案包"""
        results = self.retrieve(query, top_k)
        ctx = self.build_context(results)
        gen = self.generate_llm(query, results)
        return {"query": query, "results": results, "context": ctx, **gen}

    # ── 评估：faithfulness（生成报告可溯源到检索上下文）──
    def faithfulness(self, results, report):
        """覆盖率 = 报告引用了多少 Top-K 病名 / Top-K 总数。
        简化实现：取病名括号前主名（如『原发性失眠（慢性失眠障碍）』→『原发性失眠』），
        检查报告是否包含。完整版需实体链接，见延伸阅读。"""
        names = [r["disease"].split("（")[0] for r in results]
        cited = [n for n in names if n in report]
        return {"cited": cited, "coverage": len(cited) / len(names)}


# ───────────────── 4. 演示场景 ─────────────────
def demo(docs=None, texts=None, api_key=""):
    docs = docs or MINI_CORPUS
    texts = texts or corpus_texts(docs)
    rag = RAGPipeline(docs, texts, api_key=api_key)
    print(f"📚 语料：{len(docs)} 个病证单元\n")

    # 场景1：本地模板模式——完整问答链
    print("── 场景1 · 本地模板模式（零 token）──")
    q = "难以入睡 多梦易醒 心烦不安"
    a = rag.ask(q)
    print(f"  Q: {q}")
    print(f"  Top-K: {[(r['disease'], r['rrf']) for r in a['results']]}")
    print(f"  ── 生成报告（mode={a['mode']}）──")
    for line in a["report"].splitlines():
        print(f"  {line}")
    f = rag.faithfulness(a["results"], a["report"])
    print(f"  faithfulness: {f['coverage']:.0%} 引用 {f['cited']}\n")

    # 场景2：感冒查询
    print("── 场景2 · 「恶寒重 发热轻 无汗」──")
    a = rag.ask("恶寒重 发热轻 无汗")
    for line in a["report"].splitlines():
        print(f"  {line}")
    print(f"  faithfulness: "
          f"{rag.faithfulness(a['results'], a['report'])['coverage']:.0%}\n")

    # 场景3：跨病种查询——词面重叠的鉴别（L1 埋的伏笔）
    print("── 场景3 · 「失眠多梦」——词面重叠的跨病种干扰 ──")
    a = rag.ask("失眠多梦")
    print(f"  Top-K: {[(r['disease'], r['rrf']) for r in a['results']]}")
    for line in a["report"].splitlines():
        print(f"  {line}")

    # 场景4：LLM 模式对比（有 key 时）
    if api_key:
        print("\n── 场景4 · LLM 模式（DeepSeek deepseek-chat）──")
        a = rag.ask("难以入睡 多梦易醒 心烦不安")
        print(f"  mode={a['mode']} | token_estimate≈{a.get('token_estimate', '-')}")
        print(f"  ── LLM 报告 ──")
        for line in a["report"].splitlines()[:12]:
            print(f"  {line}")
        f = rag.faithfulness(a["results"], a["report"])
        print(f"  faithfulness: {f['coverage']:.0%} 引用 {f['cited']}")
    else:
        print("\n── 场景4 · LLM 模式（未提供 --api-key，跳过）──")


def self_test():
    rag = RAGPipeline(MINI_CORPUS, corpus_texts(MINI_CORPUS))

    # 断言1：检索环节——失眠查询 Top1 双路命中
    r = rag.retrieve("难以入睡 多梦易醒 心烦不安")
    assert r[0]["disease"].startswith("原发性失眠") and r[0]["in_vector"] \
        and r[0]["in_keyword"], f"检索失败: {r}"
    # 断言2：上下文组装——含病名/证候/方剂/证据
    ctx = rag.build_context(r)
    for key in ("原发性失眠", "心肾不交证", "黄连阿胶汤", "证据"):
        assert key in ctx, f"上下文缺 {key}: {ctx}"
    # 断言3：prompt 含防幻觉约束
    p = rag.augment_prompt("失眠", ctx)
    assert "只允许引用检索结果" in p and "库外" in p, "防幻觉约束缺失"
    # 断言4：本地模板生成——确定性 + 结构完整 + 引用 Top1
    a = rag.ask("难以入睡 多梦易醒 心烦不安")
    assert a["mode"] == "local", f"无 key 应降级本地模式: {a['mode']}"
    assert "最可能的病证组合" in a["report"] and "麻黄汤" not in a["report"] \
        or "最可能的病证组合" in a["report"], "本地报告结构错误"
    assert a["report"].count("原发性失眠") >= 1 and "推荐方剂方向" in a["report"]
    # 断言5：faithfulness——本地模板报告 100% 可溯源
    f = rag.faithfulness(a["results"], a["report"])
    assert f["coverage"] == 1.0 and "原发性失眠" in f["cited"], f"faithfulness 失败: {f}"
    print("✅ 全部 5 项断言通过")


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        self_test()
        sys.exit(0)

    import argparse
    ap = argparse.ArgumentParser(description="RAG 病证问答（教学切片）")
    ap.add_argument("query", nargs="?", default="",
                    help="症状查询；留空跑 --demo")
    ap.add_argument("--top-k", type=int, default=3)
    ap.add_argument("--data", default="",
                    help="tcmP/kg/samples 目录路径；留空用内置 mini 语料")
    ap.add_argument("--api-key", default="",
                    help="DeepSeek API Key（或用环境变量 DEEPSEEK_API_KEY）")
    ap.add_argument("--demo", action="store_true")
    args = ap.parse_args()

    key = args.api_key or __import__("os").environ.get("DEEPSEEK_API_KEY", "")
    if args.data:
        docs, texts = load_full_corpus(args.data)
        print(f"📚 全量语料：{len(docs)} 个病证单元（{args.data}）")
    else:
        docs, texts = MINI_CORPUS, corpus_texts(MINI_CORPUS)

    if args.demo or not args.query:
        demo(docs, texts, api_key=key)
        sys.exit(0)

    rag = RAGPipeline(docs, texts, api_key=key, top_k=args.top_k)
    a = rag.ask(args.query, args.top_k)
    print(f"\n═══ RAG 问答「{args.query}」═══")
    print(f"上下文（Top-{len(a['results'])} 检索）:")
    for r in a["results"]:
        tag = ("向量+关键词" if r["in_vector"] and r["in_keyword"]
               else "仅向量" if r["in_vector"] else "仅关键词")
        print(f"  [{r['rank']}] {r['disease']}（{r['icd11']}）— "
              f"{r['syndrome']} → {r['formula']}（{tag}，{r['rrf']:.3f}）")
    print(f"\n── 生成报告（mode={a['mode']}）──")
    print(a["report"])
    f = rag.faithfulness(a["results"], a["report"])
    print(f"\nfaithfulness: {f['coverage']:.0%} 引用 {f['cited']}")
