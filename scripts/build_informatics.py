# -*- coding: utf-8 -*-
"""
中医信息学（TCM Informatics）构建器 —— S 信息标准 × A 数据资产 × M 信息挖掘算子
以 tcmP 平台为背景支架，把平台资源织成可复现的知识结构（含数据挖掘结果）。
产出：kg/informatics/tcm-informatics.json + schema.json（确定性，无 hash() 随机）
用法：python scripts/build_informatics.py [--dsu kg/samples] [--out kg/informatics]
"""
from __future__ import annotations
import argparse
import json
import itertools
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DEFAULT_DSU = REPO / "kg" / "samples"
DEFAULT_SUBJECTS = REPO / "data" / "tcmP-subjects.json"
DEFAULT_OUT = REPO / "kg" / "informatics"

EVIDENCE_ENUM = {"A级-多中心RCT", "B级-单中心RCT", "C级-队列研究",
                 "D级-病例对照", "E级-专家共识", "F级-经典理论"}
MAPPING_ENUM = {"直接对应", "间接对应", "阶段对应", "综合征对应", "机制对应"}
SIX_ENUM = {"太阳病", "阳明病", "少阳病", "太阴病", "少阴病", "厥阴病", "不适用"}

STANDARDS = [
    dict(code="ICD-11 TM1", name="ICD-11 传统医学病证模块一", org="WHO", kind="分类",
         platform="icd11_mms.db + /icd/* 三端点", verify="已落地"),
    dict(code="ICD-11 MMS", name="ICD-11 死亡与发病统计（线性化）", org="WHO", kind="分类",
         platform="本地库 31,838 实体（release 2026-01）", verify="已落地"),
    dict(code="GB/T 15657", name="中医病证分类与代码", org="国家中医药管理局", kind="分类代码",
         platform="与 ICD-11 桥接的国内口径", verify="待核"),
    dict(code="ISO/TC 215", name="健康信息学（含中医药信息标准化）", org="ISO", kind="术语/互操作",
         platform="中医术语国际标准化对接", verify="待核"),
    dict(code="DSU-Schema v1", name="病证单元六段式 Schema（自建平台标准）", org="tcmP",
         kind="数据模型", platform="kg/schema/schema.json（病/证/桥/临床/教学/元）", verify="已落地"),
]
ASSETS = [
    dict(id="A1", name="病证单元语料（DSU）", size=103, unit="单元",
         path="kg/samples/dsu-samples-*.json", note="病侧×证侧×桥接×临床×教学"),
    dict(id="A2", name="ICD-11 本地编码库", size=31838, unit="实体",
         path="data/icd11_mms.db", note="Foundation ID → MMS 标准编码"),
    dict(id="A3", name="教材学科目录", size=120, unit="学科",
         path="data/tcmP-subjects.json", note="8 域 × 15/域"),
    dict(id="A4", name="教育技能目录", size=84, unit="技能",
         path="agent-tcmedu-skills/catalog.json", note="可挂接到学科枝"),
]
OPERATORS = [
    dict(id="M1", name="频次与分布分析", algo="Counter / 直方图", use="症状·证候·脏腑·六经·证据·分类分布"),
    dict(id="M2", name="关联规则挖掘", algo="co-occurrence + support/confidence/lift",
         use="症状→证候、证候→方剂、脏腑→方剂"),
    dict(id="M3", name="证候聚类", algo="症状集合重叠系数 Overlap + 单链聚类", use="相似证候归并、证候族"),
    dict(id="M4", name="编码覆盖率与冲突检测", algo="集合差 / 覆盖率", use="ICD-11 标注率、未编码清单"),
    dict(id="M5", name="数据质量门禁", algo="枚举一致性校验", use="证据等级/六经/桥接越界、缺失项"),
    dict(id="M6", name="检索与排序", algo="TF-IDF 字符 n-gram + SQLite FTS5 + RRF 融合", use="内网零 token 检索"),
    dict(id="M7", name="上下文工程装配", algo="Top-K + 出处锚定 + 证据等级排序", use="LLM 小上下文（↓95% token）"),
]


def load_units(dsu_dir: Path):
    units = []
    for f in sorted(dsu_dir.glob("dsu-samples-*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        units.extend(d.get("units", d) if isinstance(d, dict) else d)
    return units


def distributions(units):
    sym, syn, dis, form, zf, six, cat, ev, mapt = (Counter() for _ in range(9))
    for u in units:
        d, s, b, c = (u.get("disease_side", {}), u.get("syndrome_side", {}),
                      u.get("bridge", {}), u.get("clinical", {}))
        syn[s.get("syndrome_name", "")] += 1
        dis[d.get("disease_name", "")] += 1
        form[c.get("recommended_formula", "")] += 1
        zf[s.get("zangfu", "")] += 1
        six[s.get("six_channels", "")] += 1
        cat[d.get("category", "")] += 1
        ev[b.get("evidence_level", "")] += 1
        mapt[b.get("mapping_type", "")] += 1
        for x in s.get("key_symptoms", []) or []:
            sym[x] += 1
    return dict(symptom=sym, syndrome=syn, disease=dis, formula=form,
                zangfu=zf, six_channel=six, category=cat, evidence=ev, mapping=mapt)


def mine_rules(units, left_of, right_of, min_support=1, top=15):
    n = len(units)
    lc, rc, pair = Counter(), Counter(), Counter()
    for u in units:
        L, R = set(left_of(u)), set(right_of(u))
        for x in L:
            lc[x] += 1
        for y in R:
            rc[y] += 1
        for x in L:
            for y in R:
                pair[(x, y)] += 1
    rules = []
    for (x, y), k in pair.items():
        if k < min_support:
            continue
        conf = k / lc[x]
        lift = conf / (rc[y] / n)
        rules.append(dict(left=x, right=y, support=round(k / n, 4),
                          confidence=round(conf, 4), lift=round(lift, 4), n=k))
    rules.sort(key=lambda r: (-r["lift"], -r["support"], r["left"]))
    return rules[:top]


def mine_clusters(units, threshold=0.5, top=12):
    syms = {}
    for u in units:
        s = u.get("syndrome_side", {})
        syn = s.get("syndrome_name", "")
        if not syn:
            continue
        syms.setdefault(syn, set()).update(s.get("key_symptoms", []) or [])
    names = sorted(syms)
    parent = {k: k for k in names}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def uni(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[max(ra, rb)] = min(ra, rb)

    edges = []
    for a, b in itertools.combinations(names, 2):
        sa, sb = syms[a], syms[b]
        if not sa or not sb:
            continue
        j = len(sa & sb) / min(len(sa), len(sb))  # 重叠系数：适配稀疏症状集
        if j >= threshold:
            uni(a, b)
            edges.append((round(j, 3), a, b))
    groups = defaultdict(list)
    for k in names:
        groups[find(k)].append(k)
    clusters = [dict(size=len(v), members=sorted(v)) for v in groups.values() if len(v) > 1]
    clusters.sort(key=lambda c: (-c["size"], c["members"][0]))
    edges.sort(key=lambda e: (-e[0], e[1]))
    return clusters[:top], edges[:20]


def icd_coverage(units):
    mapped, unmapped = [], []
    for u in units:
        d = u.get("disease_side", {})
        rec = dict(id=u["id"], disease=d.get("disease_name", ""),
                   icd11=d.get("icd11_code", ""), icd=d.get("icd_code", ""))
        (mapped if d.get("icd11_code") else unmapped).append(rec)
    return dict(total=len(units), mapped=len(mapped), unmapped=len(unmapped),
                rate=round(len(mapped) / len(units), 4) if units else 0.0,
                unmapped_sample=unmapped[:10])


def data_quality(units):
    issues = []
    for u in units:
        d, s, b = u.get("disease_side", {}), u.get("syndrome_side", {}), u.get("bridge", {})
        ev, mt, six = b.get("evidence_level", ""), b.get("mapping_type", ""), s.get("six_channels", "")
        if ev and ev not in EVIDENCE_ENUM:
            issues.append(dict(id=u["id"], field="evidence_level", value=ev,
                               rule="∉ A–F 级", fix="枚举越界（疑似 I级→E级）"))
        if mt and mt not in MAPPING_ENUM:
            issues.append(dict(id=u["id"], field="mapping_type", value=mt, rule="∉ 5 类", fix="枚举越界"))
        if six and six not in SIX_ENUM:
            issues.append(dict(id=u["id"], field="six_channels", value=six,
                               rule="∉ 七值（含合病/过渡变体）", fix="按主证归并或扩展枚举"))
        if not s.get("syndrome_name"):
            issues.append(dict(id=u["id"], field="syndrome_name", value="", rule="必填", fix="补证名"))
        if not d.get("icd11_code"):
            issues.append(dict(id=u["id"], field="icd11_code", value="", rule="覆盖率<100%",
                               fix="补 ICD-11 编码（内网 API 或本地 db）"))
    return issues, dict(Counter(i["field"] for i in issues))


def build(dsu_dir: Path, subjects_json: Path):
    units = load_units(dsu_dir)
    dist = distributions(units)
    nonempty = lambda u, *ks: [u.get(ks[0], {}).get(ks[1], "")] if u.get(ks[0], {}).get(ks[1]) else []
    rules = dict(
        symptom_to_syndrome=mine_rules(
            units, lambda u: u.get("syndrome_side", {}).get("key_symptoms", []) or [],
            lambda u: nonempty(u, "syndrome_side", "syndrome_name")),
        syndrome_to_formula=mine_rules(
            units, lambda u: nonempty(u, "syndrome_side", "syndrome_name"),
            lambda u: nonempty(u, "clinical", "recommended_formula")),
        zangfu_to_formula=mine_rules(
            units, lambda u: nonempty(u, "syndrome_side", "zangfu"),
            lambda u: nonempty(u, "clinical", "recommended_formula")),
    )
    clusters, edges = mine_clusters(units)
    cov = icd_coverage(units)
    issues, by_field = data_quality(units)
    assets = [dict(a) for a in ASSETS]
    try:
        subj = json.loads(subjects_json.read_text(encoding="utf-8"))
        for a in assets:
            if a["id"] == "A3":
                a["size"] = subj.get("subjectCount", a["size"])
    except Exception:
        pass
    top = lambda c, k=12: [[x, n] for x, n in c.most_common(k) if x]
    stats = dict(
        units=len(units),
        distinct=dict(syndrome=len([x for x in dist["syndrome"] if x]),
                      disease=len([x for x in dist["disease"] if x]),
                      formula=len([x for x in dist["formula"] if x]),
                      symptom=len([x for x in dist["symptom"] if x])),
        icd11=cov, data_quality_issues=len(issues),
        clusters=len(clusters), rules=sum(len(v) for v in rules.values()),
    )
    catalog = dict(
        meta=dict(name="中医信息学", en="TCM Informatics", version="1.0.0",
                  model="S 信息标准 × A 数据资产 × M 信息挖掘算子",
                  sources=["kg/samples/dsu-samples-*.json", "data/icd11_mms.db",
                           "data/tcmP-subjects.json", "kg/schema/schema.json"],
                  note="挖掘结果由本构建器从真实语料现算，确定性（无 hash() 随机）",
                  generated_by="scripts/build_informatics.py"),
        standards=STANDARDS, assets=assets, operators=OPERATORS,
        distributions={k: top(v) for k, v in dist.items()},
        rules=rules, clusters=clusters, cluster_edges=edges,
        icd_coverage=cov, data_quality=dict(by_field=by_field, issues=issues[:40]),
        stats=stats,
    )
    return catalog, stats


SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "中医信息学 v1 · 三层信息结构",
    "version": "1.0.0",
    "description": "S 信息标准层 × A 数据资产层 × M 信息挖掘算子层。",
    "type": "object",
    "required": ["meta", "standards", "assets", "operators", "distributions", "rules", "stats"],
    "properties": {
        "meta": {"type": "object"}, "stats": {"type": "object"},
        "standards": {"type": "array"}, "assets": {"type": "array"},
        "operators": {"type": "array"}, "distributions": {"type": "object"},
        "rules": {"type": "object"}, "clusters": {"type": "array"},
        "cluster_edges": {"type": "array"}, "icd_coverage": {"type": "object"},
        "data_quality": {"type": "object"},
    },
}


def validate(cat):
    errs = []
    if cat["stats"]["units"] <= 0:
        errs.append("无语料")
    cov = cat["icd_coverage"]
    if cov["mapped"] + cov["unmapped"] != cov["total"]:
        errs.append("ICD 覆盖率自洽失败")
    for k, rs in cat["rules"].items():
        for r in rs:
            if not r["left"] or not r["right"]:
                errs.append(f"{k} 规则端点为空")
            if not (0 <= r["support"] <= 1 and r["confidence"] <= 1.0001 and r["lift"] >= 0):
                errs.append(f"规则取值越界: {r}")
    for c in cat["clusters"]:
        if c["size"] < 2:
            errs.append("聚类成员不足")
    return errs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dsu", default=str(DEFAULT_DSU))
    ap.add_argument("--subjects", default=str(DEFAULT_SUBJECTS))
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    print("=" * 62)
    print(" 中医信息学 · 构建开始（S×A×M 三层）")
    print("=" * 62)
    cat, stats = build(Path(args.dsu), Path(args.subjects))
    errs = validate(cat)
    if errs:
        print("[校验] 失败：")
        for e in errs[:20]:
            print("   x", e)
        raise SystemExit(1)
    (out / "tcm-informatics.json").write_text(
        json.dumps(cat, ensure_ascii=False, indent=1), encoding="utf-8")
    (out / "schema.json").write_text(json.dumps(SCHEMA, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[源] DSU {stats['units']} · 标准 {len(cat['standards'])} · 资产 {len(cat['assets'])} · 算子 {len(cat['operators'])}")
    print("[校验] 通过 OK")
    print(f"[产出] {out / 'tcm-informatics.json'}")
    print("-- 挖掘概览 --")
    print(f"  证候 {stats['distinct']['syndrome']} · 病 {stats['distinct']['disease']} · 主方 {stats['distinct']['formula']} · 症状 {stats['distinct']['symptom']}")
    print(f"  ICD-11 覆盖 {stats['icd11']['mapped']}/{stats['icd11']['total']} ({stats['icd11']['rate']:.1%})")
    print(f"  关联规则 {stats['rules']} · 证候聚类 {stats['clusters']} · 数据质量 {stats['data_quality_issues']}")
    print(f"  六经 top3 {cat['distributions']['six_channel'][:3]}")
    print(f"  证据 top3 {cat['distributions']['evidence'][:3]}")


if __name__ == "__main__":
    main()