# -*- coding: utf-8 -*-
"""课程架构层：认知四阶 × 中医药领域语义张量（D07-S11 v2.0 目录重构依据）
数据来源（均实测/平台既有）：
  - data/tcmP-subjects.json      → 8 域 × 120 学科分布
  - kg/semtensor/semtensor.json  → 域锚点与学科张量坐标
"""
from __future__ import annotations
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent

# ── 认知四阶（与「象—素—候—证」同构）──
LADDER = [
    dict(id="L1", name="感知阶", tcm="象", verb="采集", outcome="生命现象 → 物理量",
         chapters="第三~五章", part="第2篇"),
    dict(id="L2", name="理解阶", tcm="素", verb="处理", outcome="物理量 → 可计算指标",
         chapters="第六~十章", part="第3篇"),
    dict(id="L3", name="应用阶", tcm="候/证", verb="判读", outcome="指标 → 证候提示与场景方案",
         chapters="第十一~十七章", part="第4篇"),
    dict(id="L4", name="创造阶", tcm="造", verb="研发", outcome="方案 → 设备·标准·产业",
         chapters="第十八~二十五章", part="第5篇"),
]

# ── 语义张量三轴 ──
AXES = [
    dict(axis="X", name="阴阳（八纲·寒热）", ends=("阴", "中", "阳"), here="红外热像（寒热客观化）"),
    dict(axis="Y", name="表里（八纲·表里虚实）", ends=("表", "半表半里", "里"), here="经穴探测/皮电（表）↔ 心电（里）"),
    dict(axis="Z", name="精气神", ends=("精", "气", "神"), here="四元 P/E/M/K 的语义归位"),
]

# ── 四阶 × 三轴 矩阵（每格=本课程落点）──
MATRIX = [
    dict(level="L1", axis="X", cell="红外热像仪（寒热客观化）"),
    dict(level="L1", axis="Y", cell="人体经穴探测实训系统（表）/ 心电（里）"),
    dict(level="L1", axis="Z", cell="可感测物理量四元 P·E·M·K"),
    dict(level="L2", axis="X", cell="温差量化与色卡校正（光源一致性）"),
    dict(level="L2", axis="Y", cell="通道选择与多模态融合"),
    dict(level="L2", axis="Z", cell="HRV · 脉象 · 舌色 指标化"),
    dict(level="L3", axis="X", cell="寒热证候提示（TCM_RULES）"),
    dict(level="L3", axis="Y", cell="表里证候提示 / 六快评分"),
    dict(level="L3", axis="Z", cell="精气神偏颇提示（六快 → 证候）"),
    dict(level="L4", axis="X", cell="寒热类器械标准化与合规"),
    dict(level="L4", axis="Y", cell="设备改进（量程/部位/安全边界）"),
    dict(level="L4", axis="Z", cell="研发 · 标准化 · 产业化"),
]

QUANTA_TO_TENSOR = {
    "M": dict(semantic="精", reason="体重·体脂·脉压·组织——最有形", axis="Z"),
    "E": dict(semantic="气", reason="心电·经络阻抗·皮电——功能与能量活动", axis="Z"),
    "P": dict(semantic="神", reason="眼象·舌色·表情——神之外候", axis="Z"),
    "K": dict(semantic="神", reason="体动·睡眠·跌倒——神主的活动与警觉", axis="Z"),
}


def discipline():
    """学科定位：8 域分布 + D07 锚点 + D07-S11 坐标。"""
    subj = json.loads((REPO / "data" / "tcmP-subjects.json").read_text(encoding="utf-8"))
    dist = []
    for dm in subj["domains"]:
        dist.append(dict(domain=dm["name"], prefix=dm.get("prefix", ""), count=len(dm["subjects"])))
    anchor = coord = None
    st_file = REPO / "kg" / "semtensor" / "semtensor.json"
    if st_file.exists():
        st = json.loads(st_file.read_text(encoding="utf-8"))
        for d in st.get("domains", []):
            if d["name"] == "中医智能学院":
                anchor = {k: d[k] for k in ("name", "declared", "anchor", "r", "theta", "phi", "color")}
        for s in st.get("subjects", []):
            if s["code"] == "D07-S11":
                coord = {k: s[k] for k in ("code", "name", "domain", "x", "y", "z", "r", "theta", "phi", "color")}
    return dict(code="D07-S11", subject="中医智能仪器与可穿戴设备", domain="中医智能学院",
                domains=dist, total_subjects=sum(d["count"] for d in dist),
                domain_anchor=anchor, subject_coord=coord,
                role="D07 唯一的「硬件入口」：负责数据从哪来（其余 13 门处理数据/知识/算法）")


def summary():
    disc = discipline()
    return dict(ladder=LADDER, axes=AXES, matrix=MATRIX, quanta_to_tensor=QUANTA_TO_TENSOR,
                discipline=disc,
                stats=dict(cog_levels=len(LADDER), axes=len(AXES), matrix_cells=len(MATRIX),
                           chapters=26, parts=6, domains=len(disc["domains"]),
                           subjects=disc["total_subjects"]))


if __name__ == "__main__":
    import sys
    s = summary()
    print("认知四阶:", " → ".join("%s %s(%s)" % (l["id"], l["name"], l["tcm"]) for l in s["ladder"]))
    print("矩阵格:", s["stats"]["matrix_cells"], "| 章:", s["stats"]["chapters"], "| 篇:", s["stats"]["parts"])
    print("学科定位:", s["discipline"]["role"])
    a = s["discipline"]["domain_anchor"]
    print("D07 锚点:", a["anchor"], "r=%.2f θ=%.1f 色=%s" % (a["r"], a["theta"], a["color"]))
    print("域分布:", " ".join("%s:%d" % (d["domain"][:2], d["count"]) for d in s["discipline"]["domains"]))