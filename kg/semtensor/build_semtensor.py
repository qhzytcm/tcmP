# -*- coding: utf-8 -*-
"""tcmP 语义张量 · 构建器
把平台语义单元（病证单元 DSU 103）与学科安排（8 域 × 120 学科）编码到三维极坐标球面。
产出 kg/semtensor/semtensor.json（含 st_meta 公理指纹，确定性）。
用法：python kg/semtensor/build_semtensor.py [--out kg/semtensor]
"""
from __future__ import annotations
import argparse
import json
import math
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import axioms as A          # noqa: E402
import encoder as E         # noqa: E402

REPO = HERE.parent.parent
SAMPLES = REPO / "kg" / "samples"
SUBJECTS = REPO / "data" / "tcmP-subjects.json"

# ── 学科域锚点（平台裁定 · 可复核）──
# 轴义：X 阴阳(阴−/阳+)，Y 表里(表−/里+)，Z 精气神(精−/神+)
DOMAIN_ANCHOR = {
    "中医学院":      (0.00, +0.30, -0.20),   # 基础理论：脏腑气血为核心，偏精·气
    "中药学院":      (-0.20, +0.20, -0.60),  # 药物属形质，归里
    "针灸学院":      (+0.30, -0.50, +0.20),  # 经络腧穴偏表，调气
    "推拿学院":      (+0.20, -0.70, +0.00),  # 手法作用于体表，最偏表
    "骨伤学院":      (0.00, +0.40, -0.50),   # 筋骨形质，归里
    "五官口腔学院":  (+0.10, -0.40, +0.10),  # 官窍居表
    "中医智能学院":  (0.00, 0.00, +0.50),    # 信息/智能属神（认知·信息）
    "中医管理学院":  (0.00, +0.10, +0.30),   # 管理涉社会心理，偏神
}
SUBJECT_R_DEFAULT = 0.55   # 学科尺度（待接入章节数后细化）


def load_units():
    out = []
    for f in sorted(SAMPLES.glob("dsu-samples-*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        out.extend(d.get("units", d) if isinstance(d, dict) else d)
    return out


def sphere(x, y, z, r):
    n = math.sqrt(x * x + y * y + z * z)
    if not n:
        return dict(x=x, y=y, z=z, r=r, theta=0.0, phi=0.0, color=A.C_O_HEX)
    nv = (x / n, y / n, z / n)
    _, th, ph = A.cart2sph(*(t * r for t in nv))
    return dict(x=round(x, 4), y=round(y, 4), z=round(z, 4), r=round(r, 4),
                theta=round(th, 4), phi=round(ph, 4), color=A.rgb2hex(A.comp(x, y, z)))


def build():
    units = load_units()
    encoded = [E.encode_unit(u) for u in units]

    subj = json.loads(SUBJECTS.read_text(encoding="utf-8"))
    domains, subjects = [], []
    for dm in subj.get("domains", []):
        name = dm.get("name", "")
        ax = DOMAIN_ANCHOR.get(name, (0.0, 0.0, 0.0))
        domains.append(dict(name=name, prefix=dm.get("prefix"),
                            declared=dm.get("declaredCount"), extracted=dm.get("extractedCount"),
                            anchor=dict(zip("xyz", ax)), **sphere(*ax, SUBJECT_R_DEFAULT)))
        for s in dm.get("subjects", []):
            subjects.append(dict(code=s.get("code"), name=s.get("name"), domain=name, **sphere(*ax, SUBJECT_R_DEFAULT)))

    octant = Counter(u["octant"] for u in encoded)
    st_meta = dict(source="tcmP 三维极坐标语义张量-可视化标准 v1.0",
                   generator="kg/semtensor/build_semtensor.py",
                   axiom_fingerprint=A.fingerprint(),
                   domain_anchor=DOMAIN_ANCHOR,
                   subject_r=SUBJECT_R_DEFAULT,
                   note="单位向量承载语义方向；r 承载语义张量尺度；颜色 = 坐标函数（读色即读义）")
    stats = dict(units=len(encoded), subjects=len(subjects), domains=len(domains),
                 octant=dict(octant),
                 x_range=[min(u["x"] for u in encoded), max(u["x"] for u in encoded)],
                 y_range=[min(u["y"] for u in encoded), max(u["y"] for u in encoded)],
                 z_range=[min(u["z"] for u in encoded), max(u["z"] for u in encoded)],
                 r_range=[min(u["r"] for u in encoded), max(u["r"] for u in encoded)],
                 theta_range=[min(u["theta"] for u in encoded), max(u["theta"] for u in encoded)])
    return dict(st_meta=st_meta, units=encoded, domains=domains, subjects=subjects, stats=stats)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(HERE))
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    data = build()
    s = data["stats"]
    if not (s["units"] > 0 and s["subjects"] == 120 and len(s["octant"]) >= 4):
        print("[校验] 失败", s); raise SystemExit(1)
    (out / "semtensor.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print("[语义张量] DSU %d · 学科 %d · 域 %d" % (s["units"], s["subjects"], s["domains"]))
    print("  卦限分布:", s["octant"])
    print("  x∈%s y∈%s z∈%s r∈%s" % (s["x_range"], s["y_range"], s["z_range"], s["r_range"]))
    print("[产出]", out / "semtensor.json")


if __name__ == "__main__":
    main()