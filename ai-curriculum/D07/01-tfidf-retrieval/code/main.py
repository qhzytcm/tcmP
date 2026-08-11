# -*- coding: utf-8 -*-
"""
D07 中医智能学院 · AI 课程 · 轮次2 · 第1课
病证检索与文本表示：手写 TF-IDF（BUILD IT 教学切片）
====================================================
本文件用纯标准库实现 TF-IDF + 余弦相似度检索，
算法与生产引擎 tcmP/scripts/tcm_embed.py 完全同源：

    分词   = 中文字符 bigram + 英文单词（tcm_embed.tokenize 同算法）
    IDF    = log((N+1)/(df+1)) + 1
    向量   = TF-IDF 加权后 L2 归一化
    相似度 = 余弦（归一化后等价于点积）

用法:
  python main.py "难以入睡 多梦易醒 心烦不安"     # 内置 mini 语料检索
  python main.py "恶寒重 发热轻 无汗" --top-k 2
  python main.py --self-test                     # 内置断言自检
  python main.py "失眠多梦" --data ../../tcmP/kg/samples   # 全量真实语料
"""
from __future__ import annotations
import math
import re
import sys


# ───────────────── 1. 分词：中文 bigram + 英文单词 ─────────────────
def tokenize(text: str) -> list:
    """轻量分词：英文单词整词；中文连续段拆字符 bigram。
    与 tcm_embed.tokenize 同算法——先想清楚"检索的最小单位是什么"，
    再决定如何切。bigram 是零依赖中文分词的最简可工作选择。"""
    text = (text or "").lower()
    toks = []
    for w in re.findall(r"[a-z0-9]{2,}", text):        # 英文/数字整词
        toks.append(w)
    for seg in re.findall(r"[\u4e00-\u9fff]+", text):  # 中文连续段
        if len(seg) == 1:
            toks.append(seg)
        else:
            toks += [seg[i:i + 2] for i in range(len(seg) - 1)]
    return toks


# ───────────────── 2. TF-IDF 索引（核心） ─────────────────
class TfidfIndex:
    """稀疏 TF-IDF 向量索引，纯 Python 零依赖。
    三步：统计文档频率 df → 计算逆文档频率 idf → 生成归一化向量。"""

    def __init__(self):
        self.df = {}        # 词 -> 出现在多少篇文档中
        self.idf = {}       # 词 -> 逆文档频率
        self.vectors = []   # 每篇文档的归一化 TF-IDF 向量 {词: 权重}
        self.n_docs = 0

    def fit(self, docs):
        """docs: 文档文本列表"""
        self.n_docs = len(docs)
        doc_tokens = [set(tokenize(d)) for d in docs]
        # 步骤 A：文档频率 df —— 词在多少篇文档中出现（去重后）
        for toks in doc_tokens:
            for t in toks:
                self.df[t] = self.df.get(t, 0) + 1
        # 步骤 B：逆文档频率 idf —— 越稀有越关键；+1 平滑防除零
        #   log((N+1)/(df+1)) + 1：df=1 时 ≈ log(N)+1，df=N 时 = 1
        self.idf = {t: math.log((self.n_docs + 1) / (f + 1)) + 1
                    for t, f in self.df.items()}
        # 步骤 C：每篇文档生成 L2 归一化 TF-IDF 向量
        self.vectors = [self._vector_of(toks) for toks in doc_tokens]

    def _vector_of(self, toks):
        """词集合 -> 归一化 TF-IDF 向量 {词: tf * idf / ||·||}"""
        tf = {}
        for t in toks:
            tf[t] = tf.get(t, 0) + 1
        norm = math.sqrt(sum((v * self.idf[t]) ** 2 for t, v in tf.items())) or 1
        return {t: v * self.idf[t] / norm for t, v in tf.items()}

    def vectorize(self, text):
        """查询文本向量化；未见过的词以 idf=1 兜底（不惩罚新词）"""
        tf = {}
        for t in tokenize(text):
            tf[t] = tf.get(t, 0) + 1
        norm = math.sqrt(sum((v * self.idf.get(t, 1)) ** 2
                             for t, v in tf.items())) or 1
        return {t: v * self.idf.get(t, 1) / norm for t, v in tf.items()}

    def cosine(self, a, b):
        """余弦相似度。两向量均已归一化，故等价于点积。
        遍历较短的字典以省时——稀疏向量的惯用技巧。"""
        if not a or not b:
            return 0.0
        small, large = (a, b) if len(a) < len(b) else (b, a)
        return sum(small[t] * large[t] for t in small if t in large)


# ───────────────── 3. mini 语料：真实 DSU 摘录 ─────────────────
# 来源：tcmP/kg/samples/dsu-samples-00{1,2,3,4}.json（病名/证候/症状/方剂均为原文）
# 每项 = (病名, ICD-11, 证候, 关键症状[空格分隔], 推荐方剂)
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
    """把语料拼成单文本 Document（对标 tcm_embed.build_document 的简化版）"""
    return [f"疾病：{d[0]}；症状：{d[3]}；证候：{d[2]}；方剂：{d[4]}"
            for d in docs]


# ───────────────── 4. 检索 ─────────────────
def search(query, idx, docs, top_k=3):
    """查询 -> 排序后的 Top-K 结果列表"""
    qv = idx.vectorize(query)
    scored = []
    for i, dv in enumerate(idx.vectors):
        s = idx.cosine(qv, dv)
        if s > 0:
            scored.append((s, i))
    scored.sort(key=lambda x: x[0], reverse=True)
    out = []
    for s, i in scored[:top_k]:
        name, icd, synd, syms, formula = docs[i]
        out.append({"rank": len(out) + 1, "score": round(s, 4),
                    "disease": name, "icd11": icd, "syndrome": synd,
                    "symptoms": syms, "formula": formula})
    return out


# ───────────────── 5. 全量语料加载（可选扩展） ─────────────────
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


# ───────────────── 6. 内置自检 ─────────────────
def self_test():
    idx = TfidfIndex()
    idx.fit(corpus_texts(MINI_CORPUS))

    # 断言 1：bigram 分词正确
    assert tokenize("恶寒重发热轻") == ["恶寒", "寒重", "重发", "发热", "热轻"], \
        f"bigram 分词错误: {tokenize('恶寒重发热轻')}"
    # 断言 2：罕见词 idf 高于常见词（判别力越强权重越高）
    idf_common = max(idx.idf[t] for t in idx.idf
                     if idx.df[t] >= len(MINI_CORPUS) - 1)
    idf_rare = min(idx.idf[t] for t in idx.idf if idx.df[t] == 1)
    assert idf_rare > idf_common, f"idf 排序错误: 罕见{idf_rare} vs 常见{idf_common}"
    # 断言 3：查询"难以入睡 多梦易醒 心烦不安" → Top1 原发性失眠
    r = search("难以入睡 多梦易醒 心烦不安", idx, MINI_CORPUS, 1)
    assert r[0]["disease"].startswith("原发性失眠"), f"失眠检索失败: {r}"
    # 断言 4：查询"恶寒重 发热轻 无汗" → Top1 普通感冒
    r = search("恶寒重 发热轻 无汗", idx, MINI_CORPUS, 1)
    assert r[0]["disease"].startswith("普通感冒"), f"感冒检索失败: {r}"
    # 断言 5：余弦自相似 = 1（归一化向量与自身点积），且对称
    qv = idx.vectorize("心烦不安")
    assert abs(idx.cosine(qv, qv) - 1.0) < 1e-9, "自相似应=1"
    assert idx.cosine(qv, idx.vectors[1]) == idx.cosine(idx.vectors[1], qv), \
        "余弦应满足对称性"
    print("✅ 全部 5 项断言通过")


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        self_test()
        sys.exit(0)

    import argparse
    ap = argparse.ArgumentParser(description="手写 TF-IDF 病证检索（教学切片）")
    ap.add_argument("query", nargs="?", default="难以入睡 多梦易醒 心烦不安",
                    help="症状查询（空格分隔）")
    ap.add_argument("--top-k", type=int, default=3)
    ap.add_argument("--data", default="",
                    help="tcmP/kg/samples 目录路径；留空用内置 mini 语料")
    args = ap.parse_args()

    if args.data:
        docs, texts = load_full_corpus(args.data)
        print(f"📚 全量语料：{len(docs)} 个病证单元（{args.data}）")
    else:
        docs, texts = MINI_CORPUS, corpus_texts(MINI_CORPUS)
        print(f"📚 内置 mini 语料：{len(docs)} 个病证单元")

    idx = TfidfIndex()
    idx.fit(texts)
    print(f"\n═══ 手写 TF-IDF 检索「{args.query}」═══")
    for r in search(args.query, idx, docs, args.top_k):
        print(f"  {r['rank']}. [{r['score']:.4f}] {r['disease']} "
              f"({r['icd11']}) — {r['syndrome']} → {r['formula']}")
