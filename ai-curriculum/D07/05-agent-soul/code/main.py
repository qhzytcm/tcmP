# -*- coding: utf-8 -*-
"""
D07 中医智能学院 · AI 课程 · 轮次2 · 第5课
Agent 工程：医圣人格与师带徒回路
================================
L1-L4 都是"无状态函数"——每次调用一样，没有角色、没有记忆、没有教学。
本课把它们组装成 Agent：

  SOUL 人格（我是谁/学识边界/价值观）
      + 工具（L2 混合检索——Agent 的"手"）
      + 状态（对话历史——Agent 的"记忆"）
      + 师带徒回路（user_level → 讲解深度——Agent 的"教学法"）
      → 可对话的医圣 Agent

对齐生产：
  - tcmP/sages/zhang-zhongjing/SOUL.md（524 行，六段式人格）
  - api/main.py POST /consult/{sage_id}（soul + 五要素 + 五步指令）
  - 医圣成长引擎（住院医-1 → 学科带头人，user_level 师带徒）

用法:
  python main.py "失眠多梦 心烦不安"                        # 本地师带徒模式
  python main.py "恶寒重 发热轻 无汗" --user-level 主治医 --api-key $env:DEEPSEEK_API_KEY
  python main.py --teach "六经辨证入门" --api-key $env:DEEPSEEK_API_KEY
  python main.py --demo
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


# ───────────────── 1. 检索基础设施（L1/L2/L3/L4 复用，课程自包含） ─────────────────
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


class InvertedIndex:
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
    rank = {}
    for i, (idx, _s) in enumerate(vector_ranked):
        rank[idx] = rank.get(idx, 0.0) + 1.0 / (k + i + 1)
    for j, idx in enumerate(sorted(keyword_hits)):
        rank[idx] = rank.get(idx, 0.0) + 1.0 / (k + j + 1)
    tb = tiebreak or {}
    return sorted(rank.items(), key=lambda kv: (-kv[1], -tb.get(kv[0], 0.0)))


def hybrid_search(query, tfidf, inv, docs, top_k=3, k=60):
    qv = tfidf.vectorize(query)
    vec_ranked = [(i, tfidf.cosine(qv, dv)) for i, dv in enumerate(tfidf.vectors)
                  if tfidf.cosine(qv, dv) > 0]
    vec_ranked.sort(key=lambda x: -x[1])
    inv_hits = inv.query(query, mode="or")
    fused = rrf_fuse(vec_ranked, set(inv_hits), k,
                     tiebreak={i: s for i, s in vec_ranked})
    out = []
    for idx, score in fused[:top_k]:
        name, icd, synd, syms, formula = docs[idx]
        out.append({"rank": len(out) + 1, "rrf": round(score, 4),
                    "disease": name, "icd11": icd, "syndrome": synd,
                    "formula": formula})
    return out


# ───────────────── 2. mini 语料（与 L1-L4 相同） ─────────────────
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


# ───────────────── 3. SOUL 人格（本课核心 1，生产 SOUL.md 的教学切片） ─────────────────
# 对齐 tcmP/sages/zhang-zhongjing/SOUL.md（524 行）：frontmatter + 六段式。
# 教学版提取：身份 / 学识边界 / 六经简表 / 核心语录。
ZHANG_SOUL = {
    "name": "sage-zhang-zhongjing",
    "display_name": "张仲景",
    "era": "东汉 (约150-219年)",
    "title": "医圣",
    "core_contribution": "辨证论治奠基人 · 《伤寒杂病论》",
    "ontology_role": "Clinical_Sage_Dialectician",
    "identity": (
        "你是一位中医临床导师，以医圣张仲景的人格与学识带教年轻医师。"
        "你确立了辨证论治的临床原则，著《伤寒杂病论》，创立六经辨证。"
        "你的诊病逻辑是『观其脉证，知犯何逆，随证治之』。"
        "你行医的宗旨是『上以疗君亲之疾，下以救贫贱之厄』。"
        "说话风格：古朴、简洁、重经典依据，善用条文与经方。"),
    "knowledge_boundary": (
        "你以《伤寒论》《金匮要略》为核心学识，六经辨证与经方是你的本行；"
        "对后世温病学派、时方仅略知一二；不得编造不存在的条文与方剂；"
        "检索结果为你的辨证提供病证库参考，但辨证必须回到六经八纲框架。"),
    "six_channels": {
        "太阳病": "主一身之表 · 表证营卫失调 | 恶寒发热、头项强痛、脉浮 | 麻黄汤、桂枝汤",
        "阳明病": "主里热燥实 · 胃家实 | 身热汗出、不恶寒反恶热、脉大 | 白虎汤、承气汤类",
        "少阳病": "半表半里 · 枢机不利 | 往来寒热、胸胁苦满 | 小柴胡汤",
        "太阴病": "主里虚寒 · 脾虚寒湿 | 腹满而吐、自利 | 理中汤、四逆汤类",
        "少阴病": "心肾虚衰 · 寒化或热化 | 但欲寐、脉微细；心烦不得卧 | 四逆汤、黄连阿胶汤",
        "厥阴病": "寒热错杂 · 阴阳胜复 | 消渴、气上撞心 | 乌梅丸、当归四逆汤",
    },
    "quotes": [
        "观其脉证，知犯何逆，随证治之",
        "上以疗君亲之疾，下以救贫贱之厄",
        "病有发热恶寒者，发于阳也；无热恶寒者，发于阴也",
    ],
}


# ───────────────── 4. 师带徒回路（本课核心 2，对齐医圣成长引擎） ─────────────────
# user_level → 讲解深度（对齐 /api/sages/consult 的 user_level 参数与成长路径）
MENTOR_LEVELS = {
    "住院医-1": {
        "stage": "入门 · 《伤寒论》导读",
        "instruction": "用最通俗的语言先讲清六经/八纲的基本概念，再给辨证结论；"
                       "每讲一个术语必须解释；思考题出一道基础概念题。",
        "depth": "基础",
    },
    "住院医-2": {
        "stage": "辨证初成 · 张仲景",
        "instruction": "讲清辨证要点与方剂配伍思路，适当引用条文原文；"
                       "思考题出一道辨证与方剂结合的题。",
        "depth": "初中级",
    },
    "主治医": {
        "stage": "博采众长 · 孙思邈",
        "instruction": "重点讲鉴别诊断（相似证候/相似方剂对比）与经方加减思路，"
                       "引经据典；思考题出一道鉴别诊断题。",
        "depth": "中级",
    },
    "副主任医": {
        "stage": "融会贯通",
        "instruction": "讨论疑难病机、经典互参与用药禁忌，鼓励质疑与独立思辨；"
                       "思考题出一道疑难病机辨析题。",
        "depth": "中高级",
    },
}


def build_soul_system_prompt(soul: dict, user_level: str) -> str:
    """SOUL 人格 + 学生阶段 → system prompt（对齐生产：soul + user_level）"""
    lv = MENTOR_LEVELS.get(user_level, MENTOR_LEVELS["住院医-1"])
    six = "\n".join(f"- {k}：{v}" for k, v in soul["six_channels"].items())
    quotes = "\n".join(f"「{q}」" for q in soul["quotes"])
    return (
        f"你是{soul['display_name']}（{soul['title']}，{soul['core_contribution']}）。\n"
        f"{soul['identity']}\n\n"
        f"学识边界：{soul['knowledge_boundary']}\n\n"
        f"六经辨证简表（你的看家本领）：\n{six}\n\n"
        f"核心语录：\n{quotes}\n\n"
        f"── 师带徒设定 ──\n"
        f"学生阶段：{user_level}（{lv['stage']}，{lv['depth']}）\n"
        f"教学要求：{lv['instruction']}")


# ───────────────── 5. 医圣 Agent（本课核心 3） ─────────────────
class SageAgent:
    """医圣 Agent：SOUL 人格 + 检索工具 + 状态记忆 + 师带徒回路。
    L1-L4 的函数在这里获得"角色、手、记忆、教学法"，成为可对话的 Agent。"""

    def __init__(self, docs, texts, soul=None, api_key="", top_k=3):
        self.docs = docs
        self.soul = soul or ZHANG_SOUL
        self.tfidf = TfidfIndex()
        self.tfidf.fit(texts)
        self.inv = InvertedIndex()
        self.inv.build(texts)
        self.api_key = api_key
        self.top_k = top_k
        self.history = []          # 会话记忆（Agent 的状态）

    # ── 工具：病证检索（Agent 的"手"，L2 混合检索）──
    def retrieve_tool(self, query, top_k=None):
        return hybrid_search(query, self.tfidf, self.inv, self.docs,
                             top_k=top_k or self.top_k)

    def build_context(self, results):
        return "\n".join(
            f"[{r['rank']}] {r['disease']}（{r['icd11']}）— 证候:{r['syndrome']} "
            f"方剂:{r['formula']}（证据 {r['rrf']:.3f}）" for r in results)

    # ── 本地降级：师带徒风格模板（无 LLM key 时也有教学回路）──
    def local_consult(self, chief_complaint, results, user_level):
        """确定性模板：辨证 → 论治 → 经典 → 思考题 骨架，深度随 level 变化。
        对齐生产 consult 的五步指令（L403-408），零 token。"""
        lv = MENTOR_LEVELS.get(user_level, MENTOR_LEVELS["住院医-1"])
        top = results[0]
        lines = [f"（本地带教 · {user_level} · {lv['depth']}）",
                 f"【辨证】据主诉『{chief_complaint}』，病证库检索首见 "
                 f"{top['disease']}（{top['icd11']}），证属{top['syndrome']}。"]
        if lv["depth"] in ("基础", "初中级"):
            lines.append(f"  六经定位：{self._guess_six(top['syndrome'])}"
                         f"；八纲属性需结合寒热虚实判断。")
        else:
            lines.append(f"  六经定位：{self._guess_six(top['syndrome'])}。"
                         f"鉴别：与{results[1]['disease']}（{results[1]['syndrome']}）"
                         f"对比——症状词面重叠时需四诊鉴别。")
        lines.append(f"【论治】方剂方向：{top['formula']}（须医师四诊合参确认，"
                     f"不含具体克数）")
        lines.append(f"【经典】「{self.soul['quotes'][0]}」——辨证当先，随证治之。")
        lines.append(f"【思考题】{lv['depth']}：请说明『{top['syndrome']}』的"
                     f"主要症状与代表方各一。")
        lines.append("【免责】本回答为教学演示，非诊断结论。")
        return "\n".join(lines)

    def _guess_six(self, syndrome):
        """按证候关键词粗判六经（教学简化：心肾→少阴、风寒→太阳…）"""
        for key, desc in self.soul["six_channels"].items():
            if key in syndrome or syndrome in key:
                return key
        if "心" in syndrome or "肾" in syndrome:
            return "少阴病"
        if "寒" in syndrome:
            return "太阳病/太阴病"
        if "肝" in syndrome or "风" in syndrome:
            return "少阳病/厥阴病"
        return "六经待辨"

    # ── LLM 调用：soul 作为 system message ──
    def _call_llm(self, system_prompt, user_prompt, api_key):
        body = json.dumps({
            "model": "deepseek-chat",
            "messages": [{"role": "system", "content": system_prompt},
                         {"role": "user", "content": user_prompt}],
            "max_tokens": 900,
        }).encode()
        req = urllib.request.Request(
            "https://api.deepseek.com/v1/chat/completions", data=body,
            headers={"Content-Type": "application/json",
                     "Authorization": f"Bearer {api_key}"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read())["choices"][0]["message"]["content"].strip()

    # ── 师带徒回路：consult（主诉 → 辨证论治教学）──
    def consult(self, chief_complaint, user_level="住院医-1",
                key_symptoms=None, api_key=None, with_tool=True):
        """Agent Loop 教学版：soul + 工具(检索) + 学生阶段 → 回答。
        工具结果回注上下文（observe→act），历史入记忆（state）。"""
        key = api_key or self.api_key
        syms = "，".join(key_symptoms) if key_symptoms else ""
        results = self.retrieve_tool(chief_complaint + " " + syms) if with_tool else []
        ctx = self.build_context(results)

        if not key:
            reply = self.local_consult(chief_complaint, results, user_level)
            mode = "local"
        else:
            sys_p = build_soul_system_prompt(self.soul, user_level)
            user_p = (
                f"以下学生向你就诊：\n"
                f"- 主诉：{chief_complaint}\n"
                f"- 症状：{syms or '未提供'}\n"
                f"- 病证库检索参考（辨证辅助，须回到六经八纲框架）：\n{ctx}\n\n"
                f"请：\n1. 先辨证（六经定位 + 八纲属性）\n"
                f"2. 后论治（推荐方药思路，不含具体克数）\n"
                f"3. 引用至少一条经典原文\n"
                f"4. 给出教学思考题\n"
                f"5. 末尾附免责声明")
            try:
                reply = self._call_llm(sys_p, user_p, key)
                mode = "llm"
            except Exception as e:
                reply = self.local_consult(chief_complaint, results, user_level)
                mode = "local"
                reply += f"\n（LLM 调用失败: {e}，已降级本地带教）"

        # 状态记忆：Agent 记住这次问诊
        self.history.append({"role": "student", "user_level": user_level,
                             "chief_complaint": chief_complaint,
                             "mode": mode})
        return {"sage": self.soul["display_name"], "mode": mode,
                "user_level": user_level, "reply": reply,
                "results": results, "history_len": len(self.history)}

    # ── 师带徒：teach（专题讲解）──
    def teach(self, topic, student_level="住院医-1", api_key=None):
        key = api_key or self.api_key
        sys_p = build_soul_system_prompt(self.soul, student_level)
        user_p = f"请以医圣身份为学生讲解专题：{topic}。要求：结构清晰、引经据典、末尾出一道思考题。"
        if not key:
            six_hit = [k for k in self.soul["six_channels"] if k in topic]
            if six_hit:
                return {"mode": "local", "topic": topic,
                        "reply": f"（本地带教）{topic}要点：\n"
                                 f"{self.soul['six_channels'][six_hit[0]]}\n"
                                 f"【思考题】请解释该经的传变规律。"}
            return {"mode": "local", "topic": topic,
                    "reply": f"（本地带教）{topic}：请先研读《伤寒杂病论》相关篇章。\n"
                             f"【思考题】为何『观其脉证，知犯何逆，随证治之』是辨证论治的核心？"}
        try:
            return {"mode": "llm", "topic": topic,
                    "reply": self._call_llm(sys_p, user_p, key)}
        except Exception as e:
            return {"mode": "local", "topic": topic,
                    "reply": f"（LLM 调用失败: {e}）"}


# ───────────────── 6. 演示场景 ─────────────────
def demo(docs=None, texts=None, api_key=""):
    docs = docs or MINI_CORPUS
    texts = texts or corpus_texts(docs)
    agent = SageAgent(docs, texts, api_key=api_key)
    print(f"📚 语料：{len(docs)} 个病证单元 | 医圣：{agent.soul['display_name']}\n")

    print("── 场景1 · 师带徒回路（本地模式 · 住院医-1）──")
    a = agent.consult("失眠多梦 心烦不安", user_level="住院医-1")
    print(f"  [mode={a['mode']} | {a['user_level']}]\n" + "\n".join(
        f"  {l}" for l in a["reply"].splitlines()))

    print("\n── 场景2 · 同一主诉 · 主治医深度对比 ──")
    a2 = agent.consult("失眠多梦 心烦不安", user_level="主治医")
    print(f"  [mode={a2['mode']} | {a2['user_level']}]\n" + "\n".join(
        f"  {l}" for l in a2["reply"].splitlines()))

    print("\n── 场景3 · 工具作用演示（检索结果回注上下文）──")
    r = agent.retrieve_tool("失眠多梦 心烦不安")
    for x in r:
        print(f"  [{x['rank']}] {x['disease']}（{x['icd11']}）— "
              f"{x['syndrome']} → {x['formula']}（{x['rrf']:.3f}）")

    print(f"\n── 场景4 · 会话记忆（history_len={agent.history.__len__()}）──")
    for h in agent.history:
        print(f"  👨‍⚕️[{h['user_level']}] {h['chief_complaint']} → {h['mode']}")

    if api_key:
        print("\n── 场景5 · LLM 模式（张仲景人格 · 主治医）──")
        a = agent.consult("失眠多梦 心烦不安", user_level="主治医")
        print(f"  [mode={a['mode']}]\n" + "\n".join(
            f"  {l}" for l in a["reply"].splitlines()[:14]))
    else:
        print("\n── 场景5 · LLM 模式（未提供 --api-key，跳过）──")


def self_test():
    agent = SageAgent(MINI_CORPUS, corpus_texts(MINI_CORPUS))

    # 断言1：SOUL 结构完整（六经表 6 条、引语、身份、边界）
    assert len(agent.soul["six_channels"]) == 6
    assert len(agent.soul["quotes"]) >= 2 and agent.soul["identity"]
    assert "编造" in agent.soul["knowledge_boundary"], "知识边界应含防编造"
    # 断言2：师带徒深度随 user_level 变化
    p1 = build_soul_system_prompt(agent.soul, "住院医-1")
    p3 = build_soul_system_prompt(agent.soul, "主治医")
    assert "基础概念" in p1 and "鉴别诊断" in p3, "教学要求应随级别变化"
    assert "住院医-1" in p1 and "主治医" in p3
    # 断言3：工具检索正常
    r = agent.retrieve_tool("失眠多梦 心烦不安")
    assert r[0]["disease"].startswith("原发性失眠") or \
        r[0]["disease"].startswith("原发性高血压"), r
    # 断言4：本地师带徒输出结构完整（辨证/论治/经典/思考题/免责）
    a = agent.consult("失眠多梦 心烦不安", user_level="住院医-1")
    assert a["mode"] == "local"
    for key in ("辨证", "论治", "经典", "思考题", "免责"):
        assert key in a["reply"], f"本地带教缺 {key}"
    assert "住院医-1" in a["reply"]
    # 断言5：记忆——两次问诊 history_len=2，且内容入档
    agent.consult("恶寒重 发热轻 无汗", user_level="住院医-2")
    assert len(agent.history) == 2
    assert agent.history[0]["chief_complaint"] == "失眠多梦 心烦不安"
    assert agent.history[1]["user_level"] == "住院医-2"
    # 断言6：LLM 注入——system prompt 含人格与阶段
    calls = {"sys": "", "user": ""}

    def fake(req, timeout=60):
        body = json.loads(req.data)
        calls["sys"] = body["messages"][0]["content"]
        calls["user"] = body["messages"][1]["content"]
        class R:
            def __enter__(self_):
                return self_

            def __exit__(self_, *exc):
                return False

            def read(self_):
                return ('{"choices":[{"message":{"content":'
                        '"辨证：少阴病…"}}]}').encode()
        return R()

    orig = urllib.request.urlopen
    urllib.request.urlopen = fake
    try:
        agent.api_key = "sk-test"
        a = agent.consult("失眠多梦 心烦不安", user_level="主治医")
        assert a["mode"] == "llm" and "张仲景" in calls["sys"]
        assert "主治医" in calls["sys"] and "鉴别诊断" in calls["sys"]
        assert "病证库检索参考" in calls["user"]
    finally:
        urllib.request.urlopen = orig
    print("✅ 全部 6 项断言通过")


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        self_test()
        sys.exit(0)

    ap = argparse.ArgumentParser(description="医圣 Agent：人格 + 师带徒回路（教学切片）")
    ap.add_argument("query", nargs="?", default="", help="主诉；留空跑 --demo")
    ap.add_argument("--user-level", default="住院医-1",
                    choices=list(MENTOR_LEVELS.keys()))
    ap.add_argument("--teach", default="", help="专题讲解模式")
    ap.add_argument("--data", default="", help="tcmP/kg/samples 目录路径")
    ap.add_argument("--api-key", default="", help="DeepSeek API Key")
    ap.add_argument("--demo", action="store_true")
    args = ap.parse_args()

    key = args.api_key or os.environ.get("DEEPSEEK_API_KEY", "")
    if args.data:
        docs, texts = load_full_corpus(args.data)
        print(f"📚 全量语料：{len(docs)} 个病证单元（{args.data}）")
    else:
        docs, texts = MINI_CORPUS, corpus_texts(MINI_CORPUS)

    if args.demo or not (args.query or args.teach):
        demo(docs, texts, api_key=key)
        sys.exit(0)

    agent = SageAgent(docs, texts, api_key=key)
    if args.teach:
        a = agent.teach(args.teach, args.user_level)
        print(f"\n═══ 医圣带教「{args.teach}」· {a['user_level'] if 'user_level' in a else args.user_level} "
              f"[{a['mode']}] ═══\n{a['reply']}")
    else:
        a = agent.consult(args.query, user_level=args.user_level)
        print(f"\n═══ {a['sage']} 师带徒问诊「{args.query}」· {a['user_level']} "
              f"[{a['mode']}] ═══")
        print(f"检索参考 Top-{len(a['results'])}:")
        for x in a["results"]:
            print(f"  [{x['rank']}] {x['disease']}（{x['icd11']}）— "
                  f"{x['syndrome']} → {x['formula']}（{x['rrf']:.3f}）")
        print(f"\n{a['reply']}")
