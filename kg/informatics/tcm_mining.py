# -*- coding: utf-8 -*-
"""
中医信息学 · 信息挖掘引擎（零依赖）
=====================================================================
读取 build_informatics.py 产出的 tcm-informatics.json，提供只读查询 + 现算挖掘：
  · 频次分布 / 关联规则 / 证候聚类 / ICD-11 覆盖 / 数据质量
  · 检索：字符 bigram TF-IDF + 余弦（纯 stdlib）+ RRF 融合（对标 FTS5 融合思路）
CLI：
  python tcm_mining.py summary | standards | assets | operators
  python tcm_mining.py dist <key>        # key ∈ symptom/syndrome/disease/formula/zangfu/six_channel/category/evidence/mapping
  python tcm_mining.py rules <kind>      # symptom_to_syndrome / syndrome_to_formula / zangfu_to_formula
  python tcm_mining.py clusters | coverage | quality
  python tcm_mining.py retrieve "失眠 多梦"
"""
from __future__ import annotations

import json
import math
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
CATALOG = HERE / "tcm-informatics.json"
DSU_DIR = HERE.parent / "samples"


def load_catalog(path=None):
    return json.loads((Path(path) if path else CATALOG).read_text(encoding="utf-8"))


def load_units(dsu_dir=None):
    out = []
    for f in sorted((Path(dsu_dir) if dsu_dir else DSU_DIR).glob("dsu-samples-*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        out.extend(d.get("units", d) if isinstance(d, dict) else d)
    return out


def doc_text(u: dict) -> str:
    d, s, c = u.get("disease_side", {}), u.get("syndrome_side", {}), u.get("clinical", {})
    return (f"疾病：{d.get('disease_name','')}；ICD-11：{d.get('icd11_code','')}；{d.get('category','')}。"
            f"症状：{'，'.join(s.get('key_symptoms', []) or [])}。"
            f"证候：{s.get('syndrome_name','')}（{s.get('pattern_type','')}）；脏腑：{s.get('zangfu','')}；六经：{s.get('six_channels','')}。"
            f"主方：{c.get('recommended_formula','')}。")


def bigrams(text: str):
    t = (text or "").lower()
    toks = []
    for seg in __import__("re").findall(r"[\u4e00-\u9fff]+", t):
        toks += [seg] if len(seg) == 1 else [seg[i:i + 2] for i in range(len(seg) - 1)]
    for w in __import__("re").findall(r"[a-z0-9]{2,}", t):
        toks.append(w)
    return toks


class TfidfIndex:
    """字符 bigram TF-IDF + 余弦（零依赖，内网零 token 检索的最小实现）。"""

    def __init__(self, docs):
        self.ids = [d["id"] for d in docs]
        self.tokens = [bigrams(d["text"]) for d in docs]
        self.df = Counter()
        for tk in self.tokens:
            self.df.update(set(tk))
        self.n = len(docs)
        self.vecs = [self._vec(tk) for tk in self.tokens]

    def _idf(self, term):
        return math.log((1 + self.n) / (1 + self.df.get(term, 0))) + 1.0

    def _vec(self, toks):
        tf = Counter(toks)
        v = {t: (c / len(toks)) * self._idf(t) for t, c in tf.items()} if toks else {}
        norm = math.sqrt(sum(x * x for x in v.values())) or 1.0
        return {t: x / norm for t, x in v.items()}

    def retrieve(self, query, k=5):
        q = self._vec(bigrams(query))
        scored = []
        for i, v in enumerate(self.vecs):
            dot = sum(w * v.get(t, 0.0) for t, w in q.items())
            if dot > 0:
                scored.append((round(dot, 4), self.ids[i]))
        scored.sort(key=lambda x: (-x[0], x[1]))
        return scored[:k]


def rrf(rank_lists, k=60):
    """倒数排序融合（Reciprocal Rank Fusion）——对标向量 ∪ FTS5 的融合。"""
    score = {}
    for rl in rank_lists:
        for i, doc in enumerate(rl):
            score[doc] = score.get(doc, 0.0) + 1.0 / (k + i + 1)
    return sorted(score.items(), key=lambda x: (-x[1], x[0]))


def main(argv):
    cat = load_catalog()
    cmd = argv[0] if argv else "summary"
    if cmd == "summary":
        print(json.dumps(cat["stats"], ensure_ascii=False, indent=2))
    elif cmd == "standards":
        for s in cat["standards"]:
            print(f"  {s['code']:14s} {s['name']}  [{s['org']}/{s['kind']}]  平台={s['platform']}  ({s['verify']})")
    elif cmd == "assets":
        for a in cat["assets"]:
            print(f"  {a['id']} {a['name']:16s} {a['size']:>7} {a['unit']:4s} {a['path']}")
    elif cmd == "operators":
        for o in cat["operators"]:
            print(f"  {o['id']} {o['name']:16s} {o['algo']:38s} {o['use']}")
    elif cmd == "dist" and len(argv) > 1:
        for name, n in cat["distributions"].get(argv[1], []):
            print(f"  {name}  {n}")
    elif cmd == "rules" and len(argv) > 1:
        for r in cat["rules"].get(argv[1], []):
            print(f"  {r['left']} -> {r['right']}  sup={r['support']} conf={r['confidence']} lift={r['lift']} n={r['n']}")
    elif cmd == "clusters":
        for c in cat["clusters"]:
            print(f"  [{c['size']}] " + "、".join(c["members"]))
    elif cmd == "coverage":
        print(json.dumps(cat["icd_coverage"], ensure_ascii=False, indent=2))
    elif cmd == "quality":
        print(json.dumps(cat["data_quality"], ensure_ascii=False, indent=2))
    elif cmd == "retrieve" and len(argv) > 1:
        idx = TfidfIndex([dict(id=u["id"], text=doc_text(u)) for u in load_units()])
        fts = [[i for _, i in sorted([(len(set(bigrams(argv[1])) & set(bigrams(doc_text(u)))), u["id"])
                                      for u in load_units()], key=lambda x: (-x[0], x[1]))[:5]]]
        vec = [i for _, i in idx.retrieve(argv[1], 5)]
        print("  向量 Top5:", vec)
        print("  FTS5  Top5:", fts[0])
        print("  RRF 融合 :", [d for d, _ in rrf([vec, fts[0]])][:5])
    else:
        print(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])