# -*- coding: utf-8 -*-
"""tcmP 语义张量 · 三轴语义映射与 DSU 编码（单一来源）
对标标准 v1.0 §五「三轴语义定义（可计算）」。
权威分量来自八纲字段的确定性映射；encode_text() 仅用于把一句话落到球面。
"""
from __future__ import annotations
import json
import math
import re
from pathlib import Path

from axioms import (AXIS_END_COLOR, C_O, cart2sph, comp, hex2rgb, mirror_point,
                    rgb2hex, sph2cart)

EVIDENCE_SCORE = {"A级-多中心RCT": 1.00, "B级-单中心RCT": 0.75, "C级-队列研究": 0.50}
DEFAULT_EVIDENCE = 0.40

# 八纲取值（未列项 0）
_BAGANG = {
    "yin_yang": {"阳证": +1.0, "阴证": -1.0},
    "cold_heat": {"热证": +1.0, "寒证": -1.0},
    "exterior_interior": {"表证": -1.0, "半表半里": 0.0, "里证": +1.0},
    "deficiency_excess": {"实证": +1.0, "虚证": -1.0},
}
_BAGANG_CN = {"阴": -1.0, "阳": +1.0, "寒": -1.0, "热": +1.0, "表": -1.0, "里": +1.0, "虚": -1.0, "实": +1.0}

# 精气神关键词（判位）
JQS_KEYS = {
    "精": ["精", "形质", "血", "津液", "髓", "骨", "肉", "阴液"],
    "气": ["气", "阳虚", "气虚", "功能", "动力", "能量", "运化", "气机"],
    "神": ["神", "志", "情志", "失眠", "郁", "烦躁", "惊", "悸", "意识", "多梦"],
}


def clip(v, lo, hi):
    return max(lo, min(hi, v))


def bagang_value(eight: dict, key: str) -> float:
    v = (eight or {}).get(key)
    if v in _BAGANG.get(key, {}):
        return _BAGANG[key][v]
    return _BAGANG_CN.get(str(v)[0] if v else "", 0.0)


def jqs_scores(text: str) -> dict:
    return {k: sum(text.count(w) for w in ws) for k, ws in JQS_KEYS.items()}


def symptoms_density(syndrome: dict) -> float:
    n = len(syndrome.get("key_symptoms") or []) + len(syndrome.get("secondary_symptoms") or [])
    return min(1.0, n / 10)


def evidence_score(bridge: dict) -> float:
    return EVIDENCE_SCORE.get((bridge or {}).get("evidence_level", ""), DEFAULT_EVIDENCE)


def bridge_completeness(bridge: dict) -> float:
    t = ((bridge or {}).get("mapping_description") or "") + ((bridge or {}).get("biological_basis") or "")
    return min(1.0, len(t) / 200)


def encode_axes(unit: dict) -> dict:
    """核心编码：x/y/z（语义三分量）+ r（尺度）。"""
    ss = unit.get("syndrome_side") or {}
    br = unit.get("bridge") or {}
    eight = ss.get("eight_principles") or {}
    x = 0.60 * bagang_value(eight, "yin_yang") + 0.40 * bagang_value(eight, "cold_heat")
    y = 0.70 * bagang_value(eight, "exterior_interior") + 0.30 * bagang_value(eight, "deficiency_excess")
    text = (ss.get("field_theory") or "") + (ss.get("classical_basis") or "") + (br.get("mapping_description") or "")
    j = jqs_scores(text)
    denom = j["精"] + j["气"] + j["神"] + 1
    z = (j["神"] - j["精"]) / denom
    r = clip(0.35 * evidence_score(br) + 0.35 * symptoms_density(ss) + 0.30 * bridge_completeness(br), 0.20, 1.00)
    return dict(x=round(x, 4), y=round(y, 4), z=round(z, 4), r=round(r, 4), jqs=j, eight=eight)


def encode_unit(unit: dict) -> dict:
    a = encode_axes(unit)
    v = (a["x"], a["y"], a["z"])
    norm = math.sqrt(sum(t * t for t in v))
    n = tuple(t / norm for t in v) if norm else (0.0, 0.0, 0.0)
    r, theta, phi = (a["r"], math.degrees(math.asin(clip(n[2], -1, 1))) if norm else 0.0,
                     math.degrees(math.atan2(n[1], n[0])) % 360 if norm else 0.0)
    col = comp(*v)
    sec = unit.get("syndrome_side") or {}
    dis = unit.get("disease_side") or {}
    return dict(id=unit.get("id"), disease=dis.get("disease_name", ""), syndrome=sec.get("syndrome_name", ""),
                six_channel=sec.get("six_channels", ""), zangfu=sec.get("zangfu", ""),
                x=a["x"], y=a["y"], z=a["z"], r=a["r"],
                theta=round(theta, 4), phi=round(phi, 4),
                color=rgb2hex(col), color_rgb=[round(c, 4) for c in col],
                octant=("+" if a["x"] >= 0 else "-") + ("+" if a["y"] >= 0 else "-") + ("+" if a["z"] >= 0 else "-"),
                jqs=a["jqs"], eight=a["eight"])


def encode_text(text: str) -> dict:
    """自由文本确定性启发式投影：长短关键词按序切除，避免二次计数。仅用于落球面。"""
    t = text or ""
    x = y = 0.0
    if "阳" in t:
        x += 1
    if "阴" in t:
        x -= 1
    if "热" in t:
        x += 0.4
    if "寒" in t:
        x -= 0.4
    if "表" in t:
        y -= 1
    if "里" in t:
        y += 1
    if "实" in t:
        y += 0.3
    if "虚" in t:
        y -= 0.3
    j = jqs_scores(t)
    z = (j["神"] - j["精"]) / (j["精"] + j["气"] + j["神"] + 1)
    x, y = clip(x, -1, 1), clip(y, -1, 1)
    r = clip(0.35 * DEFAULT_EVIDENCE + 0.35 * min(1.0, len(t) / 60) + 0.30 * 0.5, 0.20, 1.0)
    return dict(x=round(x, 4), y=round(y, 4), z=round(z, 4), r=round(r, 4), text=text[:60])


def main(argv=None):
    import sys
    argv = argv or sys.argv[1:]
    if argv and argv[0] == "text":
        print(json.dumps(encode_text(" ".join(argv[1:])), ensure_ascii=False, indent=2))
        return
    print(json.dumps(dict(fingerprint_hint="见 axioms.fingerprint()"), ensure_ascii=False))


if __name__ == "__main__":
    main()