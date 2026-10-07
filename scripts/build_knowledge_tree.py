# -*- coding: utf-8 -*-
"""
中医知识树（TCM Knowledge Tree）构建器 · 树图一体
=====================================================================
以 tcmP 中医药网络教育平台为「背景支架」，把平台既有资源编织成一棵
「须—根—干—枝—叶」五级骨架 + 跨枝经脉图边 的知识结构（树 × 图 一体）。

设计要旨
--------
* 树（层次骨架）：须(哲学根基) → 根(核心公理) → 干(院系域) → 枝(学科) → 叶(知识点/病证单元)
* 图（跨枝经脉）：五行生克 · 十二经脉流注与表里 · 六经传变 · 学科前置 · 技能挂点 ·
                病证桥接 · ICD-11 映射 —— 让「叶」不再是孤立的，而是织入一张语义网络。
* 一体：叶＝图节点，枝干路径＝图的分层聚类，树是图的骨架，图是树的经脉。

数据源（全部为平台真实资源）
----------------------------
  · data/tcmP-subjects.json            8 域 / 120 学科（tcmP 主仓 domain-specs 的同步抽取）
  · domain-specs/DOMAIN_SPEC_D0*.md    章节目录（叶）+ 前置依赖（图边）
  · kg/samples/dsu-samples-*.json      103 病证单元(DSU) / 病证桥接 / ICD-11 标注
  · agent-tcmedu-skills/catalog.json   84 教育技能（挂点边）
  · 内嵌中医哲学根基                     须6 / 根4 / 五行 / 十二经脉 / 六经（不可从单科教材导出者）

产出
----
  kg/tree/tcm-knowledge-tree.json   nodes + edges + stats（树图一体，机器可读）
  kg/tree/schema.json               结构定义（供运行时与下游工具校验）

用法
----
  python scripts/build_knowledge_tree.py
  python scripts/build_knowledge_tree.py --domains <dir> --subjects-json <f> --out <dir>
"""
from __future__ import annotations
import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DEFAULT_DOMAINS = Path(r"C:/Users/DELL/textbook-project/domain-specs")
DEFAULT_SUBJECTS = REPO / "data" / "tcmP-subjects.json"
DEFAULT_DSU = REPO / "kg" / "samples"
DEFAULT_CATALOG = Path(r"F:/agent-tcmedu-skills/catalog.json")
DEFAULT_OUT = REPO / "kg" / "tree"

# ══════════════════════════════════════════════════════════════════════
# 一、内嵌哲学根基（须 / 根）—— 中医不可从单科教材导出的“共祖”知识
# ══════════════════════════════════════════════════════════════════════
XU = [  # 须（根须／养分层）
    ("X1", "象数阴阳", "阴阳对立、互根、消长、转化——中医认知的原初标尺"),
    ("X2", "五行生克", "木火土金水 生克乘侮——关系优先的拓扑网络"),
    ("X3", "精气神形", "精、气、神三宝与形神合一"),
    ("X4", "天人相应", "四时、五方、节气——人天耦合的边界条件"),
    ("X5", "藏象经络", "脏腑经络的生理图式根基"),
    ("X6", "恒动整体", "整体观念与恒动观——生命的动态稳态"),
]
GEN = [  # 根（核心公理层）
    ("G1", "整体观念", "人是一个有机整体，人与自然、社会相统一"),
    ("G2", "辨证论治", "辨证求因、审因论治——中医临床的操作系统"),
    ("G3", "恒动平衡", "阴平阳秘、以平为期——动态稳态与冲和"),
    ("G4", "治未病", "未病先防、既病防变、瘥后防复"),
]
NOURISH = [  # 须 → 根 的“滋养”边（语义人工认定）
    ("X1", "G1"), ("X1", "G2"), ("X2", "G1"), ("X2", "G3"),
    ("X3", "G3"), ("X4", "G1"), ("X4", "G4"), ("X5", "G2"), ("X6", "G3"), ("X6", "G4"),
]
WUXING = [("W-木", "木"), ("W-火", "火"), ("W-土", "土"), ("W-金", "金"), ("W-水", "水")]
SHENG = [("W-木", "W-火"), ("W-火", "W-土"), ("W-土", "W-金"), ("W-金", "W-水"), ("W-水", "W-木")]
KE = [("W-木", "W-土"), ("W-土", "W-水"), ("W-水", "W-火"), ("W-火", "W-金"), ("W-金", "W-木")]
MERIDIAN = ["手太阴肺经", "手阳明大肠经", "足阳明胃经", "足太阴脾经", "手少阴心经", "手太阳小肠经",
            "足太阳膀胱经", "足少阴肾经", "手厥阴心包经", "手少阳三焦经", "足少阳胆经", "足厥阴肝经"]
BIAOLI = [(0, 1), (2, 3), (4, 5), (6, 7), (8, 9), (10, 11)]
SIX = ["太阳病", "阳明病", "少阳病", "太阴病", "少阴病", "厥阴病"]

# 病证单元 → 学科枝 的关键词路由
DSU_ROUTE = [
    (("妇", "经", "带", "胎", "产", "乳", "崩漏", "痛经", "不孕", "绝经"), "D01-S16"),
    (("小儿", "儿", "疳", "惊风", "麻疹", "遗尿", "食积"), "D01-S17"),
    (("骨", "关节", "脊柱", "骨折", "筋", "颈", "腰", "膝", "脱位"), "D05-S01"),
    (("眼", "目", "视", "翳", "瞳", "青光", "白内障"), "D06-S01"),
    (("耳", "鼻", "喉", "咽", "口", "牙", "齿", "扁桃"), "D06-S02"),
    (("皮肤", "疮", "疹", "癣", "斑", "痘", "湿疹", "银屑"), "D01-S19"),
    (("男", "精", "阳痿", "遗精", "早泄", "前列腺"), "D01-S20"),
    (("肿瘤", "癌", "瘤"), "D01-S22"),
]
DSU_DEFAULT_SUBJECT = "D01-S13"


# ══════════════════════════════════════════════════════════════════════
# 二、解析器
# ══════════════════════════════════════════════════════════════════════
def load_subjects(subjects_json: Path):
    """加载 120 学科（canonical 抽取：8 域 × 学科）。"""
    data = json.loads(subjects_json.read_text(encoding="utf-8"))
    domains, subjects = [], []
    for d in data["domains"]:
        dom = dict(code=d["domain"], name=d["name"], prefix=d["prefix"])
        dom["subjects"] = []
        for s in d["subjects"]:
            sub = dict(code=s["code"], s=s["s"], name=s["name"], stage=s.get("stage", ""),
                       credits=s.get("credits", ""), textbook=s.get("textbook", ""),
                       domain=d["domain"])
            dom["subjects"].append(sub)
            subjects.append(sub)
        domains.append(dom)
    return domains, subjects


SEC_RE = re.compile(r"^#{3,4}\s+(.*\S)\s*$")
CODE_RE = re.compile(r"(D\d{2}-S\d{2})")
CH_ANY = re.compile(r"第[0-9一二三四五六七八九十百]+章[^\n|<]{0,40}")
TABLE_PRE_RE = re.compile(r"^\|\s*\*\*前置(?:课程|学科)?\*\*\s*\|\s*(.+?)\s*\|")
BULLET_PRE_RE = re.compile(r"^-\s*\*\*前置(?:要求|课程|学科)?\*\*\s*[：:]\s*(.+?)\s*$")
FQ_RE = re.compile(r"D\d{2}-S\d{2}")
LOCAL_S_RE = re.compile(r"(?<![A-Za-z0-9])S(\d{1,2})(?![\d])")
CHP_ROW = re.compile(r"^\|\s*(第[0-9一二三四五六七八九十百]+章)\s*\|\s*([^|]*?)\s*\|")


def _extract_chapters(blob: str):
    """从 章节目录 区块（编号列表 / 表格 / <br> 拼接 / 代码围栏）抽取章节条目。"""
    blob = blob.replace("<br>", "\n").replace("<br/>", "\n").replace("<br />", "\n")
    out = []
    for raw in blob.splitlines():
        ln = raw.strip()
        if not ln or ln in ("```",) or set(ln) <= {"-", "|", ":"}:
            continue
        if ln.startswith("|"):
            m = CHP_ROW.match(ln)
            if m:
                name = m.group(2)
                out.append(f"{m.group(1)} {name}".strip() if name else m.group(1))
                continue
            for t in CH_ANY.findall(" ".join(c.strip() for c in ln.strip("|").split("|"))):
                out.append(t)
            continue
        for t in re.findall(r"\*\*(第[^*]+章[^*]{0,40})\*\*", ln):
            out.append(t)
        m = re.match(r"^\d{1,2}[\.、]\s*(\S.{0,60})$", ln)
        if m:
            out.append(m.group(1))
            continue
        m = re.match(r"^(第[0-9一二三四五六七八九十百]+章[^\n|]{0,40})", ln)
        if m:
            out.append(m.group(1))
    seen, res = set(), []
    for x in out:
        x = re.split(r"[：:]", re.sub(r"\s+", " ", str(x)).strip(" 　*"))[0].strip()
        if 1 < len(x) <= 40 and x not in seen:
            seen.add(x)
            res.append(x)
    return res


def parse_markdown(domains_dir: Path, subjects):
    """解析章节叶 + 前置依赖边（跨 8 份异构规范文件的容错解析）。"""
    subj_by_code = {s["code"]: s for s in subjects}
    name2code = {}
    for s in subjects:
        name2code.setdefault(s["name"], s["code"])
    chapters, prereq = {}, []
    for f in sorted(domains_dir.glob("DOMAIN_SPEC_D*.md")):
        dm = re.search(r"DOMAIN_SPEC_(D\d+)", f.name)
        dom = dm.group(1) if dm else None
        lines = f.read_text(encoding="utf-8").splitlines()
        heads = []
        for i, l in enumerate(lines):
            if l.startswith("####") or l.startswith("###"):
                heads.append(i)
        last_code = None
        for k, idx in enumerate(heads):
            title = lines[idx].lstrip("#").strip()
            end = heads[k + 1] if k + 1 < len(heads) else len(lines)
            body = lines[idx + 1:end]
            cm = CODE_RE.search(title)
            cur = cm.group(1) if cm else name2code.get(title)
            is_toc_head = ("章节目录" in title) or (title.endswith("目录") and len(title) <= 8)
            if cur and cur in subj_by_code:
                last_code = cur
            elif is_toc_head and last_code:
                cur = last_code          # 目录标题与其上方的学科标题同属一科
            else:
                cur = None
            if not cur:
                continue
            for ln in body:
                pm = BULLET_PRE_RE.match(ln) or TABLE_PRE_RE.match(ln)
                if not pm:
                    continue
                txt = pm.group(1)
                for fq in FQ_RE.findall(txt):
                    if fq in subj_by_code and fq != cur:
                        prereq.append((cur, fq))
                if not FQ_RE.search(txt) and dom:
                    for sn in LOCAL_S_RE.findall(txt):
                        tgt = f"{dom}-S{int(sn):02d}"
                        if tgt in subj_by_code and tgt != cur:
                            prereq.append((cur, tgt))
            if is_toc_head:
                got = _extract_chapters("\n".join(body))
            else:
                ci = next((j for j, ln in enumerate(body) if "章节目录" in ln), -1)
                got = _extract_chapters("\n".join(body[ci:])) if ci >= 0 else []
            if got:
                chapters.setdefault(cur, []).extend(got)
    seen = set()
    prereq = [p for p in prereq if not (p in seen or seen.add(p))]
    return chapters, prereq


def parse_dsu(dsu_dir: Path):
    units = []
    for f in sorted(dsu_dir.glob("dsu-samples-*.json")):
        data = json.loads(f.read_text(encoding="utf-8"))
        arr = data.get("units", data) if isinstance(data, dict) else data
        units.extend(arr)
    return units


def parse_catalog(catalog_path: Path):
    if not catalog_path.exists():
        return []
    return json.loads(catalog_path.read_text(encoding="utf-8")).get("skills", [])


def _dom_num(code: str) -> int:
    return int(code[1:3])


def _obj_num(code: str) -> int:
    return int(code[5:])


# ══════════════════════════════════════════════════════════════════════
# 三、树图构建
# ══════════════════════════════════════════════════════════════════════
def build(domains, subjects, chapters, prereq, dsu, skills):
    nodes, edges = [], []
    subj_by_code = {s["code"]: s for s in subjects}

    def add(code, level, level_index, name, parent, kind, code5=None, **attrs):
        nodes.append(dict(id=code, code5=code5 or code, level=level, level_index=level_index,
                          name=name, parent=parent, kind=kind, attrs=attrs))
        if parent:
            edges.append(dict(source=parent, target=code, type="hierarchy"))

    # ── L0 须 ──
    for i, (xid, name, desc) in enumerate(XU, 1):
        add(xid, "hair", 0, name, None, "foundation", code5=f"{i}", desc=desc)
    # ── L1 根 ──
    for i, (gid, name, desc) in enumerate(GEN, 1):
        add(gid, "root", 1, name, None, "axiom", code5=f"0.{i}", desc=desc)
    for s, t in NOURISH:
        edges.append(dict(source=s, target=t, type="nourish"))
    # ── 概念节点：五行 / 十二经脉 / 六经 ──
    for i, (wid, wname) in enumerate(WUXING, 1):
        add(wid, "concept", 1, f"五行·{wname}", "X2", "concept", code5=f"2.{i}")
    for s, t in SHENG:
        edges.append(dict(source=s, target=t, type="wuxing_sheng"))
    for s, t in KE:
        edges.append(dict(source=s, target=t, type="wuxing_ke"))
    for i, mname in enumerate(MERIDIAN, 1):
        add(f"M-{i:02d}", "concept", 2, mname, "X5", "meridian", code5=f"5.{i}")
    for i in range(12):
        edges.append(dict(source=f"M-{i + 1:02d}", target=f"M-{(i + 1) % 12 + 1:02d}",
                          type="meridian_liuzhu"))
    for a, b in BIAOLI:
        edges.append(dict(source=f"M-{a + 1:02d}", target=f"M-{b + 1:02d}", type="meridian_biaoli"))
    for i, sname in enumerate(SIX, 1):
        add(f"SC-{i}", "concept", 2, sname, "G2", "six_channel", code5=f"1.{i}")
    for i in range(1, 6):
        edges.append(dict(source=f"SC-{i}", target=f"SC-{i + 1}", type="six_chuanbian"))

    # ── L2 干（8 域）──
    for d in domains:
        gid = d["code"]
        add(gid, "trunk", 2, d["name"], None, "domain", code5=f"0.0.{_dom_num(gid)}",
            prefix=d["prefix"], subjectCount=len(d["subjects"]))
        for r in GEN:
            edges.append(dict(source=r[0], target=gid, type="spine"))

    # ── L3 枝（120 学科）──
    for s in subjects:
        dom = s["domain"]
        add(s["code"], "branch", 3, s["name"], dom, "subject",
            code5=f"0.0.{_dom_num(dom)}.{_obj_num(s['code']):02d}",
            textbook=s["textbook"], stage=s["stage"], credits=s["credits"])
    for a, b in prereq:
        if a in subj_by_code and b in subj_by_code:
            edges.append(dict(source=b, target=a, type="prerequisite"))

    # ── L4 叶：章节知识点 ──
    kp = 0
    for scode, tocs in chapters.items():
        if scode not in subj_by_code:
            continue
        for j, title in enumerate(tocs, 1):
            add(f"{scode}-K{j:02d}", "leaf", 4, title, scode, "knowledge_point",
                code5=f"0.0.{_dom_num(scode)}.{_obj_num(scode):02d}.{j:02d}", index=j)
            kp += 1

    # ── 叶：技能挂点边 ──
    by_subjname = {}
    for s in subjects:
        by_subjname.setdefault(s["name"], s["code"])
    skill_bound = 0
    for sk in skills:
        tgt = next((by_subjname[x] for x in (sk.get("subjects") or []) if x in by_subjname), None)
        if tgt is None:
            for tc in sk.get("textbookCodes") or []:
                tgt = next((s["code"] for s in subjects if s["textbook"] == tc), None)
                if tgt:
                    break
        if tgt:
            sid = f"SKILL:{sk['name']}"
            add(sid, "concept", 3, sk.get("title") or sk["name"], None, "skill",
                code5=f"SKILL.{sk['name']}", category=sk.get("category"),
                description=sk.get("description", ""))
            edges.append(dict(source=sid, target=tgt, type="skill_bind",
                              meta=dict(category=sk.get("category"))))
            skill_bound += 1

    # ── 叶：病证单元 DSU + 病证桥接 + ICD-11 ──
    icd_nodes, syn_nodes, dis_nodes = {}, {}, {}
    for u in dsu:
        did = u["id"]
        d, sy, br = u.get("disease_side", {}), u.get("syndrome_side", {}), u.get("bridge", {})
        disp, syn = d.get("disease_name", ""), sy.get("syndrome_name", "")
        route = DSU_DEFAULT_SUBJECT
        hay = f"{disp}{syn}{sy.get('zangfu', '')}{d.get('category', '')}"
        for kws, code in DSU_ROUTE:
            if any(k in hay for k in kws) and code in subj_by_code:
                route = code
                break
        add(did, "leaf", 4, f"{disp} × {syn}", route, "dsu",
            code5=f"0.0.{_dom_num(route)}.{_obj_num(route):02d}.D{int(did.split('-')[1])}",
            disease=disp, syndrome=syn, six_channel=sy.get("six_channels"),
            mapping_type=br.get("mapping_type"), evidence=br.get("evidence_level"),
            icd11=d.get("icd11_code"), icd=d.get("icd_code"))
        sc = sy.get("six_channels")
        if sc in SIX:
            edges.append(dict(source=did, target=f"SC-{SIX.index(sc) + 1}", type="bridge"))
        if syn:
            sid = "SYN-%05d" % (abs(hash(syn)) % 100000)
            if sid not in syn_nodes:
                syn_nodes[sid] = syn
                add(sid, "concept", 3, syn, None, "syndrome", code5=f"SYN.{len(syn_nodes):04d}")
            edges.append(dict(source=did, target=sid, type="manifests_as"))
        if disp:
            dis_id = "DIS-%05d" % (abs(hash(disp)) % 100000)
            if dis_id not in dis_nodes:
                dis_nodes[dis_id] = disp
                add(dis_id, "concept", 3, disp, None, "disease", code5=f"DIS.{len(dis_nodes):04d}")
            edges.append(dict(source=did, target=dis_id, type="disease_is"))
        icd = d.get("icd11_code")
        if icd:
            iid = f"ICD-{icd}"
            if iid not in icd_nodes:
                icd_nodes[iid] = icd
                add(iid, "concept", 3, f"ICD-11 {icd} {d.get('icd11_title_cn', '')}".strip(),
                    None, "icd11", code5=f"ICD.{icd}")
            edges.append(dict(source=did, target=iid, type="icd11_map"))

    lv = Counter(n["level"] for n in nodes)
    kd = Counter(n["kind"] for n in nodes)
    et = Counter(e["type"] for e in edges)
    child = Counter(n["parent"] for n in nodes if n["parent"])
    stats = dict(
        nodes=len(nodes), edges=len(edges),
        levels={k: lv.get(k, 0) for k in ["hair", "root", "trunk", "branch", "leaf", "concept"]},
        kinds=dict(kd.most_common()), edge_types=dict(et.most_common()),
        knowledge_points=kp, dsu=len(dsu), skills=len(skills), skill_bound=skill_bound,
        syndromes=len(syn_nodes), diseases=len(dis_nodes), icd11=len(icd_nodes),
        domains=len(domains), subjects=len(subjects),
        prerequisites=et.get("prerequisite", 0),
        max_fanout=max(child.values()) if child else 0,
    )
    meta = dict(
        name="中医知识树", en="TCM Knowledge Tree", version="1.0.0",
        metaphor="树图一体：须—根—干—枝—叶 五级骨架 × 跨枝经脉图边",
        sources=[
            "data/tcmP-subjects.json (8 域 / 120 学科，源自 tcmP 主仓 domain-specs)",
            "domain-specs/DOMAIN_SPEC_D0*.md (章节目录叶 + 前置依赖边)",
            "kg/samples/dsu-samples-*.json (103 病证单元 / 病证桥接 / ICD-11)",
            "agent-tcmedu-skills/catalog.json (84 教育技能挂点)",
            "内嵌中医哲学根基（须 6 / 根 4 / 五行 / 十二经脉 / 六经传变）",
        ],
        encoding="五级点分编码 须.根.干.枝.叶（横向读即完整编码）",
        generated_by="scripts/build_knowledge_tree.py",
    )
    return meta, nodes, edges, stats


SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "中医知识树 v1 · 树图一体结构",
    "version": "1.0.0",
    "description": "五级骨架（须—根—干—枝—叶）× 跨枝经脉图边；叶＝图节点，枝干路径＝图的分层聚类。",
    "type": "object",
    "required": ["meta", "stats", "nodes", "edges"],
    "properties": {
        "meta": {"type": "object"},
        "stats": {"type": "object"},
        "nodes": {"type": "array", "items": {
            "type": "object",
            "required": ["id", "level", "level_index", "name", "kind"],
            "properties": {
                "id": {"type": "string"},
                "code5": {"type": "string", "description": "五级点分编码 须.根.干.枝.叶"},
                "level": {"enum": ["hair", "root", "trunk", "branch", "leaf", "concept"]},
                "level_index": {"type": "integer", "minimum": 0, "maximum": 4},
                "name": {"type": "string"},
                "parent": {"type": ["string", "null"]},
                "kind": {"enum": ["foundation", "axiom", "domain", "subject", "knowledge_point",
                                  "dsu", "concept", "meridian", "six_channel", "syndrome",
                                  "disease", "icd11", "skill"]},
                "attrs": {"type": "object"},
            }}},
        "edges": {"type": "array", "items": {
            "type": "object",
            "required": ["source", "target", "type"],
            "properties": {
                "source": {"type": "string"}, "target": {"type": "string"},
                "type": {"enum": ["hierarchy", "nourish", "spine", "prerequisite", "skill_bind",
                                  "bridge", "icd11_map", "manifests_as", "disease_is",
                                  "wuxing_sheng", "wuxing_ke", "meridian_liuzhu",
                                  "meridian_biaoli", "six_chuanbian"]},
                "weight": {"type": "number"}, "meta": {"type": "object"},
            }}},
    },
}


def validate(nodes, edges):
    """返回 (致命错误, 告警)。告警不阻断构建（如个别学科暂未解析到章节叶）。"""
    errs, warns = [], []
    ids = [n["id"] for n in nodes]
    idset = set(ids)
    if len(ids) != len(idset):
        errs.append("节点 id 存在重复")
    for n in nodes:
        if n["parent"] and n["parent"] not in idset:
            errs.append(f"孤儿节点：{n['id']} 的父 {n['parent']} 不存在")
    for e in edges:
        if e["source"] not in idset or e["target"] not in idset:
            errs.append(f"悬空边：{e['source']}->{e['target']} ({e['type']})")
    kids = Counter(n["parent"] for n in nodes if n["parent"])
    for n in nodes:
        if n["kind"] == "subject" and kids.get(n["id"], 0) == 0:
            warns.append(f"{n['id']} {n['name']}")
    return errs, warns


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--domains", default=str(DEFAULT_DOMAINS))
    ap.add_argument("--subjects-json", default=str(DEFAULT_SUBJECTS))
    ap.add_argument("--dsu", default=str(DEFAULT_DSU))
    ap.add_argument("--catalog", default=str(DEFAULT_CATALOG))
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    args = ap.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    print("═" * 62)
    print(" 中医知识树 · 构建开始（树图一体）")
    print("═" * 62)

    domains, subjects = load_subjects(Path(args.subjects_json))
    print(f"[源] 学科目录 : {args.subjects_json} -> 域 {len(domains)} · 学科 {len(subjects)}")

    chapters, prereq = parse_markdown(Path(args.domains), subjects)
    print(f"[源] domain-specs: {args.domains}")
    print(f"     含章节目录学科 {len(chapters)} · 章节叶 {sum(len(v) for v in chapters.values())}"
          f" · 前置边 {len(prereq)}")

    dsu = parse_dsu(Path(args.dsu))
    print(f"[源] dsu-samples : {args.dsu} -> 病证单元 {len(dsu)}")

    skills = parse_catalog(Path(args.catalog))
    print(f"[源] 教育技能    : {args.catalog} -> {len(skills)}")

    meta, nodes, edges, stats = build(domains, subjects, chapters, prereq, dsu, skills)
    errs, warns = validate(nodes, edges)
    if errs:
        print("\n[校验] 失败：")
        for e in errs[:20]:
            print("   ✗", e)
        sys.exit(1)
    stats["chapter_coverage"] = f"{len(chapters)}/{len(subjects)}"
    stats["bare_branches"] = len(warns)

    (out / "tcm-knowledge-tree.json").write_text(
        json.dumps(dict(meta=meta, stats=stats, nodes=nodes, edges=edges),
                   ensure_ascii=False, indent=1), encoding="utf-8")
    (out / "schema.json").write_text(
        json.dumps(SCHEMA, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\n[校验] 通过 ✓（无重复 id / 无孤儿 / 无悬空边）")
    if warns:
        print(f"[告警] {len(warns)} 个学科暂未解析到章节叶（不阻断）：")
        print("       " + "、".join(warns[:12]) + (" …" if len(warns) > 12 else ""))
    print(f"[产出] {out / 'tcm-knowledge-tree.json'}")
    print(f"[产出] {out / 'schema.json'}")
    print("\n── 结构概览 ──")
    print(f"  节点 {stats['nodes']}  边 {stats['edges']}")
    print(f"  层级 {stats['levels']}")
    print(f"  类型 {stats['kinds']}")
    print(f"  边型 {stats['edge_types']}")
    print(f"  知识叶 {stats['knowledge_points']} · DSU {stats['dsu']} · 技能挂点 {stats['skill_bound']}/{stats['skills']}")
    print(f"  证候 {stats['syndromes']} · 西医病 {stats['diseases']} · ICD-11 {stats['icd11']}")
    print(f"  章节覆盖 {stats['chapter_coverage']} 学科")


if __name__ == "__main__":
    main()
