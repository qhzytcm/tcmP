# -*- coding: utf-8 -*-
"""
D07 中医智能学院 · AI 课程 · 轮次2 · 第4课
LLM 工程：结构化输出（JSON Schema 校验生成报告）
================================================
承接 Lesson 3（RAG 问答链）。L3 的 LLM 报告是自由文本——机器无法直接
消费。本课解决结构化输出三件套：

  ① 让生成器输出 JSON（本地模板直接产 JSON / LLM 指令要求 JSON）
  ② JSON Schema 校验（手写迷你校验器，理解校验原理）
  ③ 校验失败重试（错误喂回 prompt）+ 最终降级本地模板

对齐生产：
  - tcmP/kg/schema/schema.json —— 病证单位 DSU 的 JSON Schema（draft-07，
    $ref / required / enum / pattern 全用上）
  - api/main.py 的 Pydantic BaseModel —— FastAPI 请求校验（结构化输入）
  - DeepSeek response_format=json_object —— LLM 结构化输出

用法:
  python main.py "难以入睡 多梦易醒 心烦不安"                 # 本地结构化生成
  python main.py "失眠多梦" --api-key $env:DEEPSEEK_API_KEY   # LLM 结构化+校验+重试
  python main.py --validate <json文件>                        # 校验任意 JSON 文件
  python main.py --demo                                       # 4 个演示场景
  python main.py --self-test
"""
from __future__ import annotations
import argparse
import json
import math
import os
import re
import sys
import urllib.request


# ───────────────── 1. 检索基础设施（L1/L2/L3 复用，课程自包含） ─────────────────
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
    """L1：TF-IDF 稀疏向量"""

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
    """L2：倒排索引（词 → 文档集合）"""

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
    """L2：倒数秩融合 score = Σ 1/(k+rank)"""
    rank = {}
    for i, (idx, _s) in enumerate(vector_ranked):
        rank[idx] = rank.get(idx, 0.0) + 1.0 / (k + i + 1)
    for j, idx in enumerate(sorted(keyword_hits)):
        rank[idx] = rank.get(idx, 0.0) + 1.0 / (k + j + 1)
    tb = tiebreak or {}
    return sorted(rank.items(), key=lambda kv: (-kv[1], -tb.get(kv[0], 0.0)))


def hybrid_search(query, tfidf, inv, docs, top_k=3, k=60):
    """L2：向量 + 倒排 → RRF 融合"""
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


# ───────────────── 2. mini 语料（与 L1-L3 相同） ─────────────────
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


# ───────────────── 3. JSON Schema 定义（本课核心 1） ─────────────────
# 病证问答报告 schema——对齐平台数据结构（DSU 的简化版 + 鉴别字段）
RAG_REPORT_SCHEMA = {
    "type": "object",
    "required": ["disease", "icd11_code", "syndrome", "formula",
                 "confidence", "differential", "evidence_gap"],
    "properties": {
        "disease": {"type": "string", "minLength": 2,
                    "description": "最可能疾病名（必须来自检索结果）"},
        "icd11_code": {"type": "string", "pattern": r"^[0-9A-Z][0-9A-Z.]*$",
                       "description": "ICD-11 编码（注意：精神/神经类以数字开头，如 7A00、8A80）"},
        "syndrome": {"type": "string", "minLength": 2, "description": "中医证候"},
        "formula": {"type": "string", "minLength": 1, "description": "推荐方剂"},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1,
                       "description": "检索证据置信度 0-1"},
        "differential": {"type": "array", "minItems": 1,
                         "items": {"type": "string", "minLength": 4},
                         "description": "鉴别要点列表"},
        "evidence_gap": {"type": "boolean",
                         "description": "证据不足时置 true"},
    },
}

# DSU 骨架 schema——从生产 tcmP/kg/schema/schema.json 裁剪的教学子集
# （生产版用 $ref 组织完整四段结构，本子集聚焦 id pattern + 必填骨架）
DSU_SKELETON_SCHEMA = {
    "type": "object",
    "required": ["id", "disease_side", "syndrome_side", "bridge", "clinical"],
    "properties": {
        "id": {"type": "string", "pattern": r"^DSU-\d{5}$"},
        "disease_side": {"type": "object",
                         "required": ["disease_name"],
                         "properties": {
                             "disease_name": {"type": "string", "minLength": 2},
                             "icd11_code": {"type": "string"}}},
        "syndrome_side": {"type": "object",
                          "required": ["syndrome_name"],
                          "properties": {
                              "syndrome_name": {"type": "string", "minLength": 2}}},
        "bridge": {"type": "object", "required": ["evidence_level"],
                   "properties": {
                       "evidence_level": {"type": "string",
                                          "enum": ["A级-多中心RCT",
                                                   "B级-单中心RCT",
                                                   "C级-病例对照",
                                                   "D级-专家共识"]}}},
        "clinical": {"type": "object", "required": ["recommended_formula"],
                     "properties": {
                         "recommended_formula": {"type": "string", "minLength": 1}}},
    },
}


# ───────────────── 4. 迷你校验器（本课核心 2，纯标准库） ─────────────────
class MiniValidator:
    """JSON Schema 迷你校验器（教学版）。
    支持关键字：type / required / properties / items / enum / pattern /
    minLength / minItems / minimum / maximum。
    与生产 FastAPI/Pydantic 同源的校验语义，但不支持 $ref 组合。
    返回错误信息列表，空列表 = 通过。"""

    def validate(self, data, schema):
        errors = []
        self._check(data, schema, "$", errors)
        return errors

    def _check(self, data, schema, path, errors):
        t = schema.get("type")
        if t == "object":
            if not isinstance(data, dict):
                errors.append(f"{path}: 应为 object，实为 {type(data).__name__}")
                return
            for req in schema.get("required", []):
                if req not in data:
                    errors.append(f"{path}: 缺少必填字段 {req}")
            for key, sub in schema.get("properties", {}).items():
                if key in data:
                    self._check(data[key], sub, f"{path}.{key}", errors)
        elif t == "array":
            if not isinstance(data, list):
                errors.append(f"{path}: 应为 array，实为 {type(data).__name__}")
                return
            if "minItems" in schema and len(data) < schema["minItems"]:
                errors.append(f"{path}: 长度 {len(data)} < minItems "
                              f"{schema['minItems']}")
            for i, item in enumerate(data):
                self._check(item, schema.get("items", {}), f"{path}[{i}]", errors)
        elif t == "string":
            if not isinstance(data, str):
                errors.append(f"{path}: 应为 string，实为 {type(data).__name__}")
                return
            if "minLength" in schema and len(data) < schema["minLength"]:
                errors.append(f"{path}: 长度 {len(data)} < minLength "
                              f"{schema['minLength']}")
            if "pattern" in schema and not re.search(schema["pattern"], data):
                errors.append(f"{path}: 不匹配 pattern {schema['pattern']}")
            if "enum" in schema and data not in schema["enum"]:
                errors.append(f"{path}: 不在枚举内 {schema['enum']}")
        elif t == "number":
            if isinstance(data, bool) or not isinstance(data, (int, float)):
                errors.append(f"{path}: 应为 number，实为 {type(data).__name__}")
                return
            if "minimum" in schema and data < schema["minimum"]:
                errors.append(f"{path}: {data} < minimum {schema['minimum']}")
            if "maximum" in schema and data > schema["maximum"]:
                errors.append(f"{path}: {data} > maximum {schema['maximum']}")
        elif t == "integer":
            if isinstance(data, bool) or not isinstance(data, int):
                errors.append(f"{path}: 应为 integer，实为 {type(data).__name__}")
        elif t == "boolean":
            if not isinstance(data, bool):
                errors.append(f"{path}: 应为 boolean，实为 {type(data).__name__}")


# ───────────────── 5. 结构化生成（本课核心 3） ─────────────────
def local_json(results):
    """本地规则生成：Top-K → schema 合规 JSON（确定性、零 token）。
    confidence 取 Top1 RRF 分数 ×10 归一到 0-1；differential 取 Top1 vs Top2
    对比；evidence_gap = Top1 分数过低。"""
    top = results[0]
    conf = min(1.0, round(top["rrf"] * 10, 2))
    diff = []
    if len(results) >= 2:
        alt = results[1]
        diff.append(f"与{alt['disease'].split('（')[0]}（{alt['syndrome']}）"
                    f"对比：证据 {top['rrf']:.3f} vs {alt['rrf']:.3f}，"
                    f"词面重叠时需四诊鉴别")
    if not diff:
        diff.append("无相近候选，需结合舌脉四诊确认")
    return {
        "disease": top["disease"].split("（")[0],
        "icd11_code": top["icd11"],
        "syndrome": top["syndrome"],
        "formula": top["formula"],
        "confidence": conf,
        "differential": diff,
        "evidence_gap": top["rrf"] < 0.05,
    }


class StructuredRAG:
    """结构化 RAG：检索 → LLM(JSON) → 校验 → 重试 → 降级本地"""

    MAX_RETRY = 2

    def __init__(self, docs, texts, api_key="", top_k=3, schema=None):
        self.docs = docs
        self.tfidf = TfidfIndex()
        self.tfidf.fit(texts)
        self.inv = InvertedIndex()
        self.inv.build(texts)
        self.api_key = api_key
        self.top_k = top_k
        self.schema = schema or RAG_REPORT_SCHEMA
        self.validator = MiniValidator()

    def retrieve(self, query, top_k=None):
        return hybrid_search(query, self.tfidf, self.inv, self.docs,
                             top_k=top_k or self.top_k)

    def build_context(self, results):
        return "\n".join(
            f"[{r['rank']}] {r['disease']}（{r['icd11']}）— 证候:{r['syndrome']} "
            f"方剂:{r['formula']}（证据 {r['rrf']:.3f}）" for r in results)

    def build_prompt(self, query, ctx, feedback=""):
        """JSON 输出指令：字段说明 + 示例 + 可选的上轮校验错误反馈"""
        p = (f"患者症状：{query}\n\n病证库 Top-{self.top_k} 检索结果：\n{ctx}\n\n"
             f"请只输出一个 JSON 对象（不要任何其他文本），结构：\n"
             f'{{"disease": "最可能疾病名(必须来自检索结果)", '
             f'"icd11_code": "ICD-11编码", "syndrome": "中医证候", '
             f'"formula": "推荐方剂", "confidence": 0.0到1.0, '
             f'"differential": ["鉴别要点1","鉴别要点2"], '
             f'"evidence_gap": true或false}}\n'
             f"约束：只引用检索结果中的病证；Top1 证据分数低于 0.05 时 "
             f"evidence_gap 置 true。")
        if feedback:
            p += f"\n\n⚠️ 你上一轮输出未通过 JSON Schema 校验：\n{feedback}\n请修正后重新输出完整 JSON。"
        return p

    def _call_llm(self, prompt, api_key):
        body = json.dumps({
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 800,
            "response_format": {"type": "json_object"},   # 生产级：强制 JSON
        }).encode()
        req = urllib.request.Request(
            "https://api.deepseek.com/v1/chat/completions", data=body,
            headers={"Content-Type": "application/json",
                     "Authorization": f"Bearer {api_key}"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read())["choices"][0]["message"]["content"]

    def ask(self, query, top_k=None, api_key=None):
        """结构化问答：retrieve → LLM JSON → 校验 → 重试 → 降级本地"""
        key = api_key or self.api_key
        results = self.retrieve(query, top_k)
        ctx = self.build_context(results)
        if not key:
            data = local_json(results)
            return {"mode": "local", "data": data,
                    "valid": not self.validator.validate(data, self.schema),
                    "attempts": 0, "errors": [], "results": results}
        prompt = self.build_prompt(query, ctx)
        attempts, last_errors = 0, []
        for i in range(self.MAX_RETRY + 1):
            attempts = i + 1
            try:
                raw = self._call_llm(prompt, key)
                data = json.loads(raw)          # 解析失败 → 重试
            except (json.JSONDecodeError, ValueError) as e:
                last_errors = [f"JSON 解析失败: {e}"]
                prompt = self.build_prompt(query, ctx, "\n".join(last_errors))
                continue
            errors = self.validator.validate(data, self.schema)
            if not errors:
                return {"mode": "llm", "data": data, "valid": True,
                        "attempts": attempts, "errors": [],
                        "results": results, "token_estimate": len(prompt) // 2}
            last_errors = errors
            prompt = self.build_prompt(query, ctx, "\n".join(errors))
        # 重试用尽 → 降级本地模板（graceful degradation）
        data = local_json(results)
        return {"mode": "local", "data": data, "valid": True,
                "attempts": attempts, "errors": last_errors,
                "results": results, "degraded": True}

    def validate_json(self, data):
        return self.validator.validate(data, self.schema)


# ───────────────── 6. 演示场景 ─────────────────
def demo(docs=None, texts=None, api_key=""):
    docs = docs or MINI_CORPUS
    texts = texts or corpus_texts(docs)
    rag = StructuredRAG(docs, texts, api_key=api_key)
    print(f"📚 语料：{len(docs)} 个病证单元\n")

    # 场景1：本地结构化生成
    print("── 场景1 · 本地结构化生成（确定性 JSON）──")
    a = rag.ask("难以入睡 多梦易醒 心烦不安")
    print(json.dumps(a["data"], ensure_ascii=False, indent=2))
    print(f"  校验: {'✅ 通过' if a['valid'] else '❌ ' + str(a['errors'])}\n")

    # 场景2：真实 DSU 数据过 DSU 骨架 schema
    print("── 场景2 · 平台真实数据校验（DSU 骨架 schema）──")
    try:
        from pathlib import Path
        samples = list(Path(r"..\..\..\tcmP\kg\samples").glob("dsu-samples-*.json"))
        if not samples:
            samples = list(Path(r"C:\Users\DELL\tcmP\kg\samples").glob("dsu-samples-*.json"))
        dsu = json.loads(samples[0].read_text(encoding="utf-8"))[0]
        errs = rag.validator.validate(dsu, DSU_SKELETON_SCHEMA)
        print(f"  样本: {samples[0].name} → {dsu['id']} "
              f"({dsu['disease_side']['disease_name']})")
        print(f"  校验: {'✅ 通过骨架 schema' if not errs else '❌ ' + str(errs)}\n")
    except Exception as e:
        print(f"  ⚠️ 跳过（{e}）\n")

    # 场景3：校验器负面演示（故意构造坏数据）
    print("── 场景3 · 校验器负面演示（坏数据被拦截）──")
    bad = {"disease": "原", "icd11_code": "7a00", "syndrome": "心肾不交证",
           "formula": "", "confidence": 1.5, "differential": ["x"],
           "evidence_gap": "yes"}
    errs = rag.validator.validate(bad, RAG_REPORT_SCHEMA)
    for e in errs:
        print(f"  ❌ {e}")
    print(f"  共 {len(errs)} 项违规——机器可消费的保证\n")

    # 场景4：LLM 结构化输出（有 key 时）
    if api_key:
        print("── 场景4 · LLM 结构化输出 + 校验 + 重试 ──")
        a = rag.ask("难以入睡 多梦易醒 心烦不安")
        print(f"  mode={a['mode']} | attempts={a['attempts']} | "
              f"valid={a['valid']}")
        print(json.dumps(a["data"], ensure_ascii=False, indent=2))
    else:
        print("── 场景4 · LLM 模式（未提供 --api-key，跳过）──")


def self_test():
    rag = StructuredRAG(MINI_CORPUS, corpus_texts(MINI_CORPUS))
    v = rag.validator

    # 断言1：合法对象通过校验
    good = {"disease": "原发性失眠", "icd11_code": "7A00",
            "syndrome": "心肾不交证", "formula": "黄连阿胶汤",
            "confidence": 0.32, "differential": ["与高血压对比，需四诊鉴别"],
            "evidence_gap": False}
    assert v.validate(good, RAG_REPORT_SCHEMA) == [], v.validate(good, RAG_REPORT_SCHEMA)
    # 断言2：缺必填 / 错类型 / pattern 违规 / 越界分别被拒
    bad1 = {k: good[k] for k in good if k != "disease"}
    assert any("缺少必填字段 disease" in e
               for e in v.validate(bad1, RAG_REPORT_SCHEMA))
    bad2 = dict(good, icd11_code="7a00")   # pattern 违规
    assert any("pattern" in e for e in v.validate(bad2, RAG_REPORT_SCHEMA))
    bad3 = dict(good, confidence=1.5)      # maximum 越界
    assert any("maximum" in e for e in v.validate(bad3, RAG_REPORT_SCHEMA))
    bad4 = dict(good, evidence_gap="yes")  # 类型错误
    assert any("boolean" in e for e in v.validate(bad4, RAG_REPORT_SCHEMA))
    # 断言3：local_json 确定性 + schema 合规
    results = rag.retrieve("难以入睡 多梦易醒 心烦不安")
    d1, d2 = local_json(results), local_json(results)
    assert d1 == d2, "local_json 应确定性"
    assert v.validate(d1, RAG_REPORT_SCHEMA) == [], v.validate(d1, RAG_REPORT_SCHEMA)
    assert d1["disease"] == "原发性失眠" and d1["evidence_gap"] is True
    # mini 语料 RRF 分数为 1/60 量级（k=60），Top1≈0.033 < 0.05 →
    # evidence_gap 必须为 True（低分证据声明）——与 L3 LLM 的判断一致
    # 断言4：LLM 注入——坏 JSON 重试后成功
    calls = {"n": 0}

    def fake_bad_then_good(req, timeout=60):
        calls["n"] += 1
        if calls["n"] == 1:
            content = '{"disease": "原发性失眠", "icd11_code": "7A00"}'  # 缺字段
        else:
            content = json.dumps(good, ensure_ascii=False)
        class R:
            def __enter__(self_):
                return self_

            def __exit__(self_, *exc):
                return False

            def read(self_):
                return ('{"choices":[{"message":{"content":'
                        + json.dumps(content, ensure_ascii=False) + '}}]}').encode()
        return R()

    orig = urllib.request.urlopen
    urllib.request.urlopen = fake_bad_then_good
    try:
        rag.api_key = "sk-test"
        a = rag.ask("难以入睡 多梦易醒 心烦不安")
        assert a["mode"] == "llm" and a["attempts"] == 2 and a["valid"], a
    finally:
        urllib.request.urlopen = orig
    # 断言5：LLM 全坏 → 降级本地（graceful degradation）
    def fake_always_bad(req, timeout=60):
        class R:
            def __enter__(self_):
                return self_

            def __exit__(self_, *exc):
                return False

            def read(self_):
                return ('{"choices":[{"message":{"content":'
                        '"not json at all"}}]}').encode()
        return R()

    urllib.request.urlopen = fake_always_bad
    try:
        a = rag.ask("难以入睡 多梦易醒 心烦不安")
        assert a["mode"] == "local" and a.get("degraded") and a["valid"], a
    finally:
        urllib.request.urlopen = orig
    print("✅ 全部 5 项断言通过")


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        self_test()
        sys.exit(0)

    ap = argparse.ArgumentParser(description="结构化输出：JSON Schema 校验（教学切片）")
    ap.add_argument("query", nargs="?", default="", help="症状查询；留空跑 --demo")
    ap.add_argument("--top-k", type=int, default=3)
    ap.add_argument("--data", default="", help="tcmP/kg/samples 目录路径")
    ap.add_argument("--api-key", default="", help="DeepSeek API Key")
    ap.add_argument("--validate", default="", help="校验指定 JSON 文件（RAG_REPORT_SCHEMA）")
    ap.add_argument("--demo", action="store_true")
    args = ap.parse_args()

    if args.validate:
        data = json.loads(open(args.validate, encoding="utf-8").read())
        errs = MiniValidator().validate(data, RAG_REPORT_SCHEMA)
        print("✅ 校验通过" if not errs else "❌ 违规:\n" + "\n".join(errs))
        sys.exit(0 if not errs else 1)

    key = args.api_key or os.environ.get("DEEPSEEK_API_KEY", "")
    if args.data:
        docs, texts = load_full_corpus(args.data)
        print(f"📚 全量语料：{len(docs)} 个病证单元（{args.data}）")
    else:
        docs, texts = MINI_CORPUS, corpus_texts(MINI_CORPUS)

    if args.demo or not args.query:
        demo(docs, texts, api_key=key)
        sys.exit(0)

    rag = StructuredRAG(docs, texts, api_key=key, top_k=args.top_k)
    a = rag.ask(args.query, args.top_k)
    print(f"\n═══ 结构化问答「{args.query}」═══")
    print(f"mode={a['mode']} | attempts={a['attempts']} | valid={a['valid']}"
          + (f" | degraded={a['degraded']}" if a.get("degraded") else ""))
    print(json.dumps(a["data"], ensure_ascii=False, indent=2))
    if a.get("errors"):
        print(f"\n⚠️ 最终校验未通过的错误：\n" + "\n".join(a["errors"]))
