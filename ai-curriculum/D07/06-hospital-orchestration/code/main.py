# -*- coding: utf-8 -*-
"""
D07 中医智能学院 · AI 课程 · 轮次2 · 第6课
多智能体编排与六者协作
====================
L5 造了一个医圣 Agent。但医院是生态：医者开方、患者就诊、药者审方、
械者管设备、规者管质控、法者防纠纷。本课把六个 Agent 编成"医院"：

  角色分工（六者 SOUL）→ 路由（问题找谁）→ 流水线（就诊流）
  → 枢纽（医者协调药者/规者闭环）

对齐生产：
  - tcmP/agents/{healer,patient,pharmacist,device,regulator,legal}/SOUL.md
  - api/main.py /agents/{role}/chat + /patients/* + /pharmacists/* 等端点
  - 六者医圣成长平台（医者为核心枢纽，其余五方围绕医者）

用法:
  python main.py "失眠多梦 心烦不安"                       # 路由 → 相应角色
  python main.py "患者失眠，方用黄连阿胶汤" --demo          # 就诊流水线
  python main.py "附子15g 半夏10g" --role pharmacist        # 指定角色
  python main.py --demo                                     # 演示场景
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


# ───────────────── 1. 检索基础设施（L1-L5 复用，课程自包含） ─────────────────
def tokenize(text: str) -> list:
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


# ───────────────── 2. mini 语料（与 L1-L5 相同） ─────────────────
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


# ───────────────── 3. 六者 SOUL（本课核心 1，对齐 agents/ 六目录） ─────────────────
# 教学版精简：role / display / hospital_mapping / mission / tools / boundary
SIX_ROLES = {
    "healer": {
        "display": "医者", "hospital_mapping": "临床医师/带教老师",
        "mission": "病证推理 + 方剂推荐 + 师带徒教学",
        "tools": ["病证检索", "辨证论治", "师带徒"],
        "boundary": "不直接开具处方剂量；需四诊合参",
        "route_keywords": ["失眠", "头痛", "咳嗽", "发热", "辨证", "证候", "方剂思路"],
    },
    "patient": {
        "display": "患者", "hospital_mapping": "就诊患者/家属",
        "mission": "症状自查 + 导诊 + 康复指导",
        "tools": ["症状自查", "导诊分诊", "康复建议"],
        "boundary": "自查非诊断，重症建议急诊",
        "route_keywords": ["症状", "自查", "导诊", "挂号", "挂什么科", "挂科", "康复", "去哪看"],
    },
    "pharmacist": {
        "display": "药者", "hospital_mapping": "药剂师/药企/配送",
        "mission": "处方审核 + 用药安全 + 饮片溯源",
        "tools": ["处方审核", "配伍检查", "禁忌提示"],
        "boundary": "十八反十九畏绝不越过；剂量超限必警示",
        "route_keywords": ["处方", "药", "剂量", "配伍", "禁忌", "附子", "半夏", "煎服"],
    },
    "device": {
        "display": "械者", "hospital_mapping": "设备科/影像科",
        "mission": "设备维护 + 影像辅助 + 采购论证",
        "tools": ["设备状态", "维护建议", "采购评估"],
        "boundary": "设备故障应急按预案分级",
        "route_keywords": ["设备", "CT", "MRI", "维修", "采购", "球管", "仪器"],
    },
    "regulator": {
        "display": "规者", "hospital_mapping": "院办/质控/后勤",
        "mission": "质控管理 + 排班优化 + 应急调度",
        "tools": ["质控检查", "排班", "应急调度"],
        "boundary": "质控指标以院级标准为准",
        "route_keywords": ["质控", "排班", "应急", "检查", "运营", "调度"],
    },
    "legal": {
        "display": "法者", "hospital_mapping": "医事律师/法务",
        "mission": "纠纷防控 + 法规查询 + 文书辅助",
        "tools": ["纠纷风险评估", "法规查询", "文书生成"],
        "boundary": "提供风险提示，最终以正式法律意见为准",
        "route_keywords": ["纠纷", "医保", "赔偿", "法规", "知情同意", "投诉", "责任"],
    },
}


# ───────────────── 4. 角色 Agent + 路由 + 流水线（本课核心 2/3/4） ─────────────────
# 药味白名单（教学版识别范围；生产为药典级数据）
HERB_WHITELIST = ["附子", "乌头", "半夏", "瓜蒌", "贝母", "白蔹", "白及",
                  "甘草", "海藻", "甘遂", "大戟", "芫花", "麻黄", "桂枝",
                  "黄连", "黄芩", "阿胶", "酸枣仁", "天麻", "钩藤", "射干",
                  "细辛", "干姜", "五味子", "柴胡", "白芍", "人参", "黄芪",
                  "当归", "川芎", "熟地", "肉桂"]
FORMULA_WHITELIST = ["麻黄汤", "黄连阿胶汤合交泰丸", "黄连阿胶汤", "交泰丸",
                     "天麻钩藤饮", "射干麻黄汤", "桂枝汤", "小柴胡汤",
                     "四逆汤", "理中汤", "乌梅丸", "炙甘草汤"]


class RoleAgent:
    """通用角色 Agent：SOUL + 本地确定性处理 + 可选 LLM。
    教学版每个角色用规则模板完成本职工作（零 token），
    有 key 时走 SOUL system + LLM（对齐 /agents/{role}/chat）。"""

    def __init__(self, role, docs, texts, api_key="", top_k=3):
        assert role in SIX_ROLES, f"未知角色: {role}"
        self.role = role
        self.soul = SIX_ROLES[role]
        self.docs_list = docs or MINI_CORPUS
        self.tfidf = TfidfIndex()
        self.tfidf.fit(texts)
        self.inv = InvertedIndex()
        self.inv.build(texts)
        self.api_key = api_key
        self.top_k = top_k

    def retrieve(self, query):
        return hybrid_search(query, self.tfidf, self.inv, self.docs_list,
                             top_k=self.top_k)

    # ── 本地确定性处理（每个角色的"手艺活"）──
    def local_handle(self, task, results=None):
        soul = self.soul
        if self.role == "healer":
            top = (results or self.retrieve(task))[0]
            return (f"【辨证】据主诉『{task}』，病证库首见 {top['disease']}"
                    f"（{top['icd11']}），证属{top['syndrome']}。\n"
                    f"【论治】方剂方向：{top['formula']}（须四诊合参确认）。\n"
                    f"【协作】建议转药者审方 → 规者质控记录。")
        if self.role == "patient":
            top = (results or self.retrieve(task))[0]
            return (f"【自查】症状『{task}』与 {top['disease']} 相似病证吻合。\n"
                    f"【导诊】建议挂号：{top['icd11']} 对应科室方向"
                    f"（中医内科/相应专科）。\n"
                    f"【提示】自查非诊断；症状持续加重请及时就诊。")
        if self.role == "pharmacist":
            herbs = [h for h in HERB_WHITELIST if h in task]
            formulas = [f for f in FORMULA_WHITELIST if f in task]
            risk = []
            for h in herbs:
                if h in ("附子", "乌头"):
                    risk.append(f"{h}: 有毒之品，须先煎/久煎，剂量超 15g 警示")
                if h in ("半夏", "瓜蒌", "贝母", "白蔹", "白及"):
                    risk.append(f"{h}: 与乌头类相反（十八反），配伍须核查")
                if h in ("甘草",):
                    risk.append(f"{h}: 与海藻/甘遂/大戟/芫花相反，且久服伤脾")
            if not risk:
                risk.append("未检出十八反十九畏冲突；建议核对剂量与妊娠禁忌")
            head = f"【审方】药味：{'、'.join(herbs) if herbs else '（未识别药味）'}"
            if formulas:
                head += f"；含方剂：{'、'.join(formulas)}"
            return (head + "\n"
                    + "\n".join(f"【警示】{r}" for r in risk)
                    + "\n【结论】" + ("需医者复核后再调配" if any("相反" in r or "有毒" in r for r in risk)
                                    else "可调配，附用药说明"))
        if self.role == "device":
            return (f"【设备】{task}——状态检查：运行正常（教学演示数据）。\n"
                    f"【维护】建议按周期保养；异常时启动应急预案分级上报。\n"
                    f"【采购】如需采购论证，提供参数对比与预算评估。")
        if self.role == "regulator":
            return (f"【质控】{task}——检查项：处方合规 / 排班覆盖 / 应急演练。\n"
                    f"【记录】本次协作将写入质控日志（对话=进化信号）。\n"
                    f"【建议】处方闭环完整率目标 ≥95%。")
        if self.role == "legal":
            return (f"【风险评估】{task}——风险点：知情同意 / 诊疗记录完整 / "
                    f"沟通留痕。\n"
                    f"【建议】完善告知义务与文书归档，降低纠纷概率。\n"
                    f"【提示】如需正式意见请转法务线下。")
        return f"【{soul['display']}】收到：{task}"

    # ── 统一入口：本地 or LLM ──
    def handle(self, task, api_key=None):
        key = api_key or self.api_key
        if not key:
            return {"role": self.role, "display": self.soul["display"],
                    "mode": "local", "reply": self.local_handle(task)}
        sys_p = (f"你是医院{self.soul['display']}（{self.soul['hospital_mapping']}）。\n"
                 f"使命：{self.soul['mission']}\n工具：{', '.join(self.soul['tools'])}\n"
                 f"边界：{self.soul['boundary']}\n"
                 f"请以该角色身份专业、简洁地回答（本地病证库检索可辅助辨证/审方）。")
        body = json.dumps({"model": "deepseek-chat",
                           "messages": [{"role": "system", "content": sys_p},
                                        {"role": "user", "content": task}],
                           "max_tokens": 600}).encode()
        req = urllib.request.Request(
            "https://api.deepseek.com/v1/chat/completions", data=body,
            headers={"Content-Type": "application/json",
                     "Authorization": f"Bearer {key}"})
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                reply = json.loads(resp.read())["choices"][0]["message"]["content"].strip()
            return {"role": self.role, "display": self.soul["display"],
                    "mode": "llm", "reply": reply}
        except Exception as e:
            return {"role": self.role, "display": self.soul["display"],
                    "mode": "local", "reply": self.local_handle(task),
                    "llm_error": str(e)}


class HospitalRouter:
    """路由：问题 → 六者之一（关键词规则；默认医者）"""

    def __init__(self):
        self.keywords = {role: soul["route_keywords"]
                         for role, soul in SIX_ROLES.items()}

    def route(self, text):
        scores = {}
        for role, kws in self.keywords.items():
            n = sum(1 for kw in kws if kw in text)
            if n:
                scores[role] = n
        if not scores:
            return "healer"          # 默认：医者（核心枢纽）
        return max(scores, key=scores.get)


class Hospital:
    """六者医院：路由 + 角色 Agent + 协作流水线"""

    def __init__(self, docs, texts, api_key="", top_k=3):
        self.docs, self.texts = docs, texts
        self.api_key = api_key
        self.agents = {role: RoleAgent(role, docs, texts, api_key, top_k)
                       for role in SIX_ROLES}
        self.router = HospitalRouter()
        self.collab_log = []         # 协作日志（对话=进化信号）

    def ask(self, question, role=None):
        """入口：指定角色或自动路由"""
        target = role or self.router.route(question)
        a = self.agents[target].handle(question)
        self.collab_log.append({"from": "user", "to": target,
                                "task": question, "mode": a["mode"]})
        return a

    # ── 就诊流水线：患者 → 医者 → 药者 → 规者（核心教学场景）──
    def visit_pipeline(self, chief_complaint, formula_hint=""):
        """一次完整就诊流，每步产出交给下一步"""
        steps = []
        # 1. 患者：自查导诊
        p = self.agents["patient"].handle(chief_complaint)
        steps.append({"role": "patient", "task": chief_complaint,
                      "reply": p["reply"], "mode": p["mode"]})
        # 2. 医者：辨证论治（带检索）
        results = self.agents["healer"].retrieve(chief_complaint)
        top = results[0]
        h = self.agents["healer"].handle(
            f"{chief_complaint}（病证库参考：{top['disease']} {top['syndrome']}）")
        h["reply"] += f"\n【处方】{top['formula']}（方向）"
        steps.append({"role": "healer", "task": chief_complaint,
                      "reply": h["reply"], "mode": h["mode"]})
        # 3. 药者：审方（医者枢纽自动触发）
        rx = formula_hint or top["formula"]
        ph = self.agents["pharmacist"].handle(f"审方：{rx}")
        steps.append({"role": "pharmacist", "task": rx, "reply": ph["reply"],
                      "mode": ph["mode"]})
        # 4. 规者：质控记录
        rg = self.agents["regulator"].handle(
            f"就诊闭环质控：{chief_complaint} → {top['disease']} → {rx}")
        steps.append({"role": "regulator", "task": "质控记录", "reply": rg["reply"],
                      "mode": rg["mode"]})
        for s in steps:
            self.collab_log.append({"from": "prev", "to": s["role"],
                                    "task": s["task"], "mode": s["mode"]})
        return {"steps": steps, "top": top}


# ───────────────── 5. 演示场景 ─────────────────
def demo(docs=None, texts=None, api_key=""):
    docs = docs or MINI_CORPUS
    texts = texts or corpus_texts(docs)
    hospital = Hospital(docs, texts, api_key=api_key)
    print(f"📚 语料：{len(docs)} 个病证单元 | 六者医院已开诊\n")

    print("── 场景1 · 路由演示（问题找谁）──")
    for q in ("我失眠多梦怎么办", "这张处方有附子15g", "CT设备报错",
              "医保报销纠纷咨询", "内科质控检查", "不知道挂什么科"):
        r = hospital.router.route(q)
        print(f"  「{q}」→ {SIX_ROLES[r]['display']}（{r}）")

    print("\n── 场景2 · 就诊流水线（患者→医者→药者→规者）──")
    visit = hospital.visit_pipeline("失眠多梦 心烦不安")
    for s in visit["steps"]:
        print(f"\n  ▶ {SIX_ROLES[s['role']]['display']}（{s['role']} · {s['mode']}）")
        for line in s["reply"].splitlines():
            print(f"    {line}")
    print(f"\n  ▶ 辨证结论: {visit['top']['disease']} → {visit['top']['formula']}")

    print("\n── 场景3 · 药者审方（十八反警示）──")
    ph = hospital.agents["pharmacist"].handle("审方：附子15g 半夏10g 甘草6g")
    for line in ph["reply"].splitlines():
        print(f"  {line}")

    print("\n── 场景4 · 协作日志（对话=进化信号）──")
    for entry in hospital.collab_log[:8]:
        print(f"  {entry['from']} → {entry['to']}: {entry['task'][:20]}… [{entry['mode']}]")


def self_test():
    hospital = Hospital(MINI_CORPUS, corpus_texts(MINI_CORPUS))

    # 断言1：六者 SOUL 齐备（6 角色，各含 mission/tools/boundary）
    assert len(SIX_ROLES) == 6
    for role, soul in SIX_ROLES.items():
        assert soul["mission"] and soul["tools"] and soul["boundary"], role
    # 断言2：路由正确
    r = hospital.router
    assert r.route("这张处方有附子15g") == "pharmacist"
    assert r.route("CT设备故障报修") == "device"
    assert r.route("医保报销纠纷") == "legal"
    assert r.route("内科质控检查") == "regulator"
    assert r.route("随便聊聊") == "healer", "无关键词应默认医者"
    # 断言3：各角色本地处理
    p = hospital.agents["patient"].handle("失眠多梦")
    assert "自查" in p["reply"] and "导诊" in p["reply"]
    h = hospital.agents["healer"].handle("失眠多梦 心烦不安")
    assert "辨证" in h["reply"] and "论治" in h["reply"]
    ph = hospital.agents["pharmacist"].handle("审方：附子15g 半夏10g")
    assert "十八反" in ph["reply"] or "相反" in ph["reply"], ph["reply"]
    # 断言4：就诊流水线四步闭环
    visit = hospital.visit_pipeline("失眠多梦 心烦不安")
    roles = [s["role"] for s in visit["steps"]]
    assert roles == ["patient", "healer", "pharmacist", "regulator"], roles
    assert visit["top"]["disease"].startswith("原发性失眠")
    # 断言5：协作日志记录（流水线 4 步 = 4 条）
    assert len(hospital.collab_log) >= 4
    # 断言6：LLM 注入——医者有 key 时 mode=llm 且 system 含角色
    calls = {}
    def fake(req, timeout=60):
        body = json.loads(req.data)
        calls["sys"] = body["messages"][0]["content"]
        class R:
            def __enter__(self_):
                return self_

            def __exit__(self_, *exc):
                return False

            def read(self_):
                return ('{"choices":[{"message":{"content":"辨证：少阴病"}}]}').encode()
        return R()
    orig = urllib.request.urlopen
    urllib.request.urlopen = fake
    try:
        hospital.agents["healer"].api_key = "sk-test"
        a = hospital.agents["healer"].handle("失眠多梦")
        assert a["mode"] == "llm" and "医者" in calls["sys"]
        assert "师带徒" in calls["sys"] or "方剂" in calls["sys"]
    finally:
        urllib.request.urlopen = orig
    print("✅ 全部 6 项断言通过")


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        self_test()
        sys.exit(0)

    ap = argparse.ArgumentParser(description="六者医院：多智能体编排（教学切片）")
    ap.add_argument("question", nargs="?", default="", help="问题/主诉；留空跑 --demo")
    ap.add_argument("--role", default="", choices=list(SIX_ROLES.keys()),
                    help="指定角色（默认自动路由）")
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

    if args.demo or not args.question:
        demo(docs, texts, api_key=key)
        sys.exit(0)

    hospital = Hospital(docs, texts, api_key=key)
    a = hospital.ask(args.question, role=args.role or None)
    print(f"\n═══ {a['display']}（{a['role']} · {a['mode']}）═══")
    print(a["reply"])
    print(f"\n协作日志: {len(hospital.collab_log)} 条")
