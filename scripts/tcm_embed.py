# -*- coding: utf-8 -*-
"""
tcm_embed.py — 病证单元 Embedding 引擎（论著 RAG 范式落地）
================================================================
参考论著: "Decoding the mind: A RAG-LLM on ICD-11 for decision support
in psychology" (ESWA 2025) — Document构建 → embedding → 余弦相似度
Top-K检索 → 上下文/决策输出。LLMind 用 LangChain+ChromaDB+Gemma2，
本引擎对标其管线并在 tcmP 病证单元(DSU)上落地：

  Document = 病侧(病名/ICD11编码/症状) + 证侧(证候/六经/方药) 单文本
  向量化   = TF-IDF 字符n-gram（零依赖） | 可选 BGE 语义向量
  检索     = 余弦相似度 Top-K + SQLite FTS5 全文召回（RRF 融合）
  流程     = diagnose(症状→病) / bianzheng(症状→证) / rag(检索+LLM报告)

降 token 设计：全部检索/排序/融合在内网完成，LLM 仅消费 Top-K 小上下文。

用法:
  from tcm_embed import TCMSearchEngine
  eng = TCMSearchEngine()            # 自动加载 kg/samples
  eng.diagnose(["恶寒重","发热轻","无汗","头身疼痛"])
  eng.bianzheng(["口苦","咽干","胁肋胀痛"])
  eng.rag(["失眠多梦","口苦咽干"])   # 需 deepseek_key
"""
from __future__ import annotations
import json, math, os, re, sqlite3, sys
from pathlib import Path
from typing import List, Optional

KG_DIR = Path(__file__).parent.parent / "kg" / "samples"
DB_PATH = Path(__file__).parent.parent / "data" / "icd11_mms.db"


# ───────────────────────── 文本工具 ─────────────────────────
def tokenize(text: str) -> List[str]:
    """中文按字符 bigram + 英文单词混合的轻量分词"""
    text = (text or "").lower()
    toks = []
    # 英文单词
    for w in re.findall(r"[a-z0-9]{2,}", text):
        toks.append(w)
    # 中文连续段 → 字符 bigram
    for seg in re.findall(r"[\u4e00-\u9fff]+", text):
        if len(seg) == 1:
            toks.append(seg)
        else:
            toks += [seg[i:i + 2] for i in range(len(seg) - 1)]
    return toks


# ───────────────────────── Document 构建 ─────────────────────────
def build_document(dsu: dict) -> dict:
    """病证单元 → 单文本 Document（对标论著 prompt 字段）"""
    ds = dsu["disease_side"]
    ss = dsu.get("syndrome_side", {})
    cl = dsu.get("clinical", {})

    disease = ds.get("disease_name", "")
    icd = ds.get("icd11_code") or ds.get("icd_code") or ""
    dsym = "，".join(ds.get("key_symptoms", []) or [])
    dcat = ds.get("category", "")
    syndrome = ss.get("syndrome_name", "")
    pat = ss.get("pattern_type", "")
    zf = ss.get("zangfu", "")
    six = ss.get("six_channels", "")
    ssym = "，".join(ss.get("key_symptoms", []) or [])
    formula = cl.get("recommended_formula", "")

    text = (f"疾病：{disease}；ICD-11编码：{icd}；{dcat}。"
            f"西医症状：{dsym}。"
            f"中医证候：{syndrome}（{pat}），脏腑：{zf}，六经：{six}。"
            f"证候症状：{ssym}。推荐方剂：{formula}。")
    return {
        "dsu_id": dsu.get("id", ""),
        "disease_name": disease,
        "icd11_code": icd,
        "syndrome_name": syndrome,
        "pattern_type": pat,
        "zangfu": zf,
        "six_channels": six,
        "formula": formula,
        "text": text,
        "_tokens": None,
    }


# ───────────────────────── 向量化（TF-IDF） ─────────────────────────
class TfidfIndex:
    """字符 n-gram TF-IDF 稀疏向量（纯 Python，零依赖）"""

    def __init__(self):
        self.df = {}          # term -> 文档频率
        self.idf = {}         # term -> idf
        self.vectors = []     # [{term: weight}, ...]
        self.n_docs = 0

    def fit(self, docs_text: List[str]):
        self.n_docs = len(docs_text)
        doc_tokens = [set(tokenize(t)) for t in docs_text]
        for toks in doc_tokens:
            for t in toks:
                self.df[t] = self.df.get(t, 0) + 1
        self.idf = {t: math.log((self.n_docs + 1) / (f + 1)) + 1
                    for t, f in self.df.items()}
        self.vectors = []
        for toks in doc_tokens:
            tf = {}
            for t in toks:
                tf[t] = tf.get(t, 0) + 1
            norm = math.sqrt(sum((v * self.idf[t]) ** 2 for t, v in tf.items())) or 1
            self.vectors.append({t: v * self.idf[t] / norm for t, v in tf.items()})

    def vectorize(self, text: str) -> dict:
        tf = {}
        for t in tokenize(text):
            tf[t] = tf.get(t, 0) + 1
        norm = math.sqrt(sum((v * self.idf.get(t, 1)) ** 2 for t, v in tf.items())) or 1
        return {t: v * self.idf.get(t, 1) / norm for t, v in tf.items()}

    def cosine(self, a: dict, b: dict) -> float:
        if not a or not b:
            return 0.0
        small, large = (a, b) if len(a) < len(b) else (b, a)
        dot = sum(small[t] * large[t] for t in small if t in large)
        return dot  # 已归一化


# ───────────────────────── FTS5 全文索引 ─────────────────────────
class FTS5Index:
    """SQLite FTS5 全文索引：症状/病名关键词快速召回"""

    def __init__(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.execute(
            "CREATE VIRTUAL TABLE dsu_fts USING fts5(dsu_id, disease, syndrome, symptoms, formula, text)")
        self.n = 0

    def add(self, doc: dict):
        self.conn.execute(
            "INSERT INTO dsu_fts VALUES (?,?,?,?,?,?)",
            (doc["dsu_id"], doc["disease_name"], doc["syndrome_name"],
             doc.get("_symptoms_text", ""), doc["formula"], doc["text"]))
        self.n += 1

    def search(self, query: str, limit: int = 20) -> List[str]:
        """返回命中的 dsu_id 列表（按 FTS5 相关性）"""
        q = " OR ".join(f'"{t}"' for t in tokenize(query)[:12])
        if not q:
            return []
        try:
            rows = self.conn.execute(
                f"SELECT dsu_id FROM dsu_fts WHERE dsu_fts MATCH ? ORDER BY rank LIMIT ?",
                (q, limit)).fetchall()
            return [r[0] for r in rows]
        except sqlite3.OperationalError:
            return []

    def close(self):
        self.conn.close()


# ───────────────────────── 搜索引擎 ─────────────────────────
class TCMSearchEngine:
    def __init__(self, kg_dir: Optional[Path] = None, top_k: int = 5,
                 debug: bool = False):
        self.kg_dir = Path(kg_dir) if kg_dir else KG_DIR
        self.top_k = top_k
        self.debug = debug
        self.docs: List[dict] = []
        self.by_id = {}
        self._load()
        self.tfidf = TfidfIndex()
        self.tfidf.fit([d["text"] for d in self.docs])
        self.fts = FTS5Index()
        for d in self.docs:
            d["_symptoms_text"] = (d.get("text", ""))
            self.fts.add(d)
        self._bge = None  # 语义向量（BGE）预留

    def _load(self):
        files = sorted(self.kg_dir.glob("dsu-samples-*.json"))
        for f in files:
            for dsu in json.loads(f.read_text(encoding="utf-8")):
                doc = build_document(dsu)
                self.docs.append(doc)
                self.by_id[doc["dsu_id"]] = doc
        if self.debug:
            print(f"  📚 DSU 加载: {len(self.docs)} 个病证单元")

    # ── 检索核心 ──
    def _vector_rank(self, query: str) -> List[dict]:
        qv = self.tfidf.vectorize(query)
        scored = []
        for i, dv in enumerate(self.tfidf.vectors):
            s = self.tfidf.cosine(qv, dv)
            if s > 0:
                scored.append({"idx": i, "score": round(s, 4)})
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[: self.top_k * 3]

    def _rrf_fuse(self, vector_hits: List[dict], fts_ids: List[str],
                  k: int = 60) -> List[dict]:
        """RRF 融合：向量相似度 + FTS5 关键词召回"""
        rank = {}
        for i, h in enumerate(vector_hits):
            dsu_id = self.docs[h["idx"]]["dsu_id"]
            rank.setdefault(dsu_id, {"rrf": 0.0, "vec": h["score"], "fts": 0})
            rank[dsu_id]["rrf"] += 1.0 / (k + i + 1)
        for j, dsu_id in enumerate(fts_ids):
            rank.setdefault(dsu_id, {"rrf": 0.0, "vec": 0.0, "fts": 1})
            rank[dsu_id]["rrf"] += 1.0 / (k + j + 1)
        ranked = sorted(rank.items(),
                        key=lambda kv: (-kv[1]["rrf"], -kv[1]["vec"]))
        return [{"dsu_id": d, **kv} for d, kv in ranked[: self.top_k]]

    def _enrich(self, dsu_id: str) -> dict:
        d = self.by_id[dsu_id]
        return {
            "dsu_id": dsu_id,
            "disease": d["disease_name"],
            "icd11_code": d["icd11_code"],
            "syndrome": d["syndrome_name"],
            "pattern_type": d["pattern_type"],
            "zangfu": d["zangfu"],
            "six_channels": d["six_channels"],
            "formula": d["formula"],
        }

    # ── 流程 1：疾病诊断（症状 → 病）──
    def diagnose(self, symptoms: List[str], top_k: Optional[int] = None) -> dict:
        k = top_k or self.top_k
        self.top_k = k
        query = "，".join(symptoms)
        vec = self._vector_rank(query)
        fts = self.fts.search(query)
        fused = self._rrf_fuse(vec, fts)
        results = []
        for h in fused:
            r = self._enrich(h["dsu_id"])
            r["score"] = h["vec"]
            r["evidence"] = f"向量 {h['vec']:.3f} + FTS {h['fts']}"
            results.append(r)
        return {"mode": "diagnose", "symptoms": symptoms,
                "results": results, "top_k": k}

    # ── 流程 2：证候辨证（症状 → 证，支撑病证单元）──
    def bianzheng(self, symptoms: List[str], top_k: Optional[int] = None) -> dict:
        k = top_k or self.top_k
        self.top_k = k
        query = "，".join(symptoms)
        vec = self._vector_rank(query)
        fts = self.fts.search(query)
        fused = self._rrf_fuse(vec, fts)
        results = []
        for h in fused:
            r = self._enrich(h["dsu_id"])
            r["score"] = h["vec"]
            results.append(r)
        return {"mode": "bianzheng", "symptoms": symptoms,
                "results": results, "top_k": k}

    # ── 流程 3：RAG 报告（检索 Top-K + LLM 生成，可选降 token）──
    def rag(self, symptoms: List[str], deepseek_key: str = "",
            top_k: Optional[int] = None) -> dict:
        k = top_k or self.top_k
        diag = self.diagnose(symptoms, k)
        ctx = "\n\n".join(
            f"[{i+1}] {r['disease']}（{r['icd11_code']}）— 证候:{r['syndrome']} "
            f"方剂:{r['formula']}" for i, r in enumerate(diag["results"]))
        if not deepseek_key.startswith("sk-"):
            diag["rag_report"] = ("[本地模式] 未配置 DeepSeek Key，已返回内网检索结果"
                                  "（零 token 消耗）")
            return diag
        # LLM 精修（仅消费 Top-K 小上下文）
        import urllib.request as u2
        prompt = (f"患者症状：{'，'.join(symptoms)}\n\n"
                  f"病证库 Top-{k} 检索结果：\n{ctx}\n\n"
                  f"请综合给出：1.最可能疾病+ICD-11编码 2.中医证候 3.推荐方剂 4.鉴别要点")
        body = json.dumps({"model": "deepseek-chat",
                           "messages": [{"role": "user", "content": prompt}],
                           "max_tokens": 800}).encode()
        req = u2.Request("https://api.deepseek.com/v1/chat/completions", data=body,
                         headers={"Content-Type": "application/json",
                                  "Authorization": f"Bearer {deepseek_key}"})
        try:
            with u2.urlopen(req, timeout=60) as resp:
                d = json.loads(resp.read())
            diag["rag_report"] = d["choices"][0]["message"]["content"]
            diag["token_estimate"] = len(prompt) // 2
        except Exception as e:
            diag["rag_report"] = f"[LLM调用失败: {e}]"
        return diag


# ───────────────────────── CLI ─────────────────────────
def main():
    import argparse
    ap = argparse.ArgumentParser(description="tcmP 病证单元 Embedding 引擎")
    ap.add_argument("symptoms", nargs="+", help="症状（空格分隔）")
    ap.add_argument("--mode", choices=["diagnose", "bianzheng", "rag"],
                    default="diagnose", help="流程：诊断/辨证/RAG")
    ap.add_argument("--top-k", type=int, default=5)
    ap.add_argument("--debug", action="store_true")
    args = ap.parse_args()

    eng = TCMSearchEngine(debug=args.debug, top_k=args.top_k)
    if args.mode == "diagnose":
        r = eng.diagnose(args.symptoms)
        print(f"═══ 疾病诊断「{'，'.join(args.symptoms)}」═══")
        for i, x in enumerate(r["results"], 1):
            print(f"  {i}. {x['disease']} [{x['icd11_code']}] — {x['evidence']}")
    elif args.mode == "bianzheng":
        r = eng.bianzheng(args.symptoms)
        print(f"═══ 证候辨证「{'，'.join(args.symptoms)}」═══")
        for i, x in enumerate(r["results"], 1):
            print(f"  {i}. {x['syndrome']}（{x['zangfu']} / {x['six_channels']}）→ {x['formula']}")
    else:
        r = eng.rag(args.symptoms, os.environ.get("DEEPSEEK_API_KEY", ""))
        print(f"═══ RAG 诊断「{'，'.join(args.symptoms)}」═══")
        for i, x in enumerate(r["results"], 1):
            print(f"  {i}. {x['disease']} [{x['icd11_code']}] — {x['syndrome']} → {x['formula']}")
        print("\n--- RAG 报告 ---")
        print(r.get("rag_report", ""))


if __name__ == "__main__":
    main()
