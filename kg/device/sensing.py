# -*- coding: utf-8 -*-
"""人类生命健康 · 可感应参数捕获与健康自动评价（零依赖）
对标：D07-S11《中医智能仪器与可穿戴设备》扩展层
- 四元可感测物理量：光子(光) · 电子/电压(电) · 质量(力/重) · 运动(位移/加速度)
- 中医药通用六快：吃 / 喝 / 拉 / 撒 / 睡 / 警觉安全
- 健康自动评价：多源可穿戴记录 → 六快分维评分 → 总分分级（确定性）
参考实现：pkpio/fitbit-googlefit（Fitbit API → 单位换算 → Google Fit；纳秒时间戳/meters/kg）
⚠️ 评分为教学活动用启发式，不构成医学诊断。
"""
from __future__ import annotations
import math

# ── 四元可感测物理量 ──
QUANTA = [
    dict(id="P", name="光子（光）", unit="cd / nm / lux", sensor="光电二极管·相机·PPG",
         meas="光强/波长/光谱/反射", tcm="望诊（舌色面色）· 脉搏波 · 光疗/光生物调节"),
    dict(id="E", name="电子/电压（电）", unit="mV / Ω / S", sensor="电极·ECG·皮电",
         meas="电位/电流/阻抗/皮电反应", tcm="心电（脉率节律）· 经络电阻 · 情志（皮电）"),
    dict(id="M", name="质量（力/重）", unit="kg / N / mmHg", sensor="应变片·称重·压力阵列",
         meas="体重/体脂/压力/握力", tcm="形体胖瘦 · 脉象压力（脉位脉势）· 握力（筋骨）"),
    dict(id="K", name="运动（位移/加速度）", unit="m / m·s⁻² / °·s⁻¹", sensor="加速度计·陀螺·磁力计",
         meas="步数/体动/姿态/平衡", tcm="行走坐卧（活动）· 震颤（风证）· 睡眠体动"),
]

# ── 中医药通用六快 ──
SIX_QUICK = [
    dict(id="Q1", name="吃", sense="咀嚼加速度·进食图像·餐次/体重", tcm="脾胃运化；饮食自倍，肠胃乃伤"),
    dict(id="Q2", name="喝", sense="饮水量（称重/容量）·皮肤电", tcm="津液代谢；口渴多饮与消渴"),
    dict(id="Q3", name="拉", sense="排便频次/形态（自评）·腹部体动", tcm="大肠传导；便溏便秘辨脾肾"),
    dict(id="Q4", name="撒", sense="尿量/频次（自评+传感）", tcm="肾与膀胱气化；夜尿与肾气"),
    dict(id="Q5", name="睡", sense="加速度+心率+皮温 → 睡眠分期", tcm="心神；阳入于阴则寐"),
    dict(id="Q6", name="警觉安全", sense="跌倒检测（加速度）·HRV·定位", tcm="神与气血；老年跌倒属正气不足"),
]

# 六快 → 四元映射（哪一元承载该快的证据）
SIX_QUICK_QUANTA = {"Q1": ["K", "M", "P"], "Q2": ["M", "E"], "Q3": ["K", "M", "P"],
                    "Q4": ["M", "E"], "Q5": ["K", "E", "M"], "Q6": ["K", "E"]}


def _ramp(x, lo, hi):
    """分段线性：≤lo→0，≥hi→100。"""
    if x is None:
        return None
    if hi == lo:
        return 100.0
    return max(0.0, min(100.0, 100.0 * (x - lo) / (hi - lo)))


def _band(x, lo, hi, soft=0.35):
    """带型：落在 [lo,hi] 为 100，外侧线性衰减到 0（用于"过多/过少皆不佳"的指标）。"""
    if x is None:
        return None
    if lo <= x <= hi:
        return 100.0
    span = (hi - lo) or 1.0
    d = (lo - x) if x < lo else (x - hi)
    return max(0.0, 100.0 * (1 - d / (span * (1 + soft))))


def grade(score):
    return ("优" if score >= 85 else "良" if score >= 70 else "中" if score >= 55 else "差")


def score_six_quick(rec: dict) -> dict:
    """按六快分维评分。rec 为多源可穿戴记录（Fitbit/Google Fit 风格字段）。"""
    dims = {}
    # 吃：餐次 + 活动量（以进餐规律性与能量平衡表征）
    meals = rec.get("meals_count")
    s1 = _band(meals, 3, 4) if meals is not None else None
    dims["Q1"] = dict(name="吃", score=round(s1, 1) if s1 is not None else None,
                      evidence={"meals_count": meals},
                      tcm="餐次规律则脾胃安；暴食/漏餐伤运化")
    # 喝：饮水量 1200–2000 ml/日 为佳
    w = rec.get("water_ml")
    s2 = _band(w, 1200, 2000) if w is not None else None
    dims["Q2"] = dict(name="喝", score=round(s2, 1) if s2 is not None else None,
                      evidence={"water_ml": w}, tcm="津液充足则口不渴；多饮多尿当察消渴")
    # 拉：排便 1–2 次/日 为佳
    b = rec.get("bowel_count")
    s3 = _band(b, 1, 2) if b is not None else None
    dims["Q3"] = dict(name="拉", score=round(s3, 1) if s3 is not None else None,
                      evidence={"bowel_count": b}, tcm="一日一次、成形为常；溏/秘辨虚实")
    # 撒：排尿 4–8 次/日
    u = rec.get("urine_count")
    s4 = _band(u, 4, 8) if u is not None else None
    dims["Q4"] = dict(name="撒", score=round(s4, 1) if s4 is not None else None,
                      evidence={"urine_count": u}, tcm="小便通利为气化正常；夜尿多为肾气虚")
    # 睡：睡眠时长 7–9 h 为佳（分钟）
    sl = rec.get("sleep_minutes")
    s5 = _band((sl / 60.0) if sl is not None else None, 7, 9) if sl is not None else None
    dims["Q5"] = dict(name="睡", score=round(s5, 1) if s5 is not None else None,
                      evidence={"sleep_minutes": sl}, tcm="阳入于阴则寐；少寐多梦多属心神不宁")
    # 警觉安全：跌倒次数（0 最佳）+ HRV（SDNN 越高越好，20–100ms 参考）
    falls = rec.get("fall_events")
    sdnn = rec.get("hrv_sdnn")
    sf = 100.0 if (falls is None or falls == 0) else max(0.0, 100.0 - 50.0 * falls)
    sh = _ramp(sdnn, 15, 60) if sdnn is not None else None
    parts = [x for x in (sf if falls is not None else None, sh) if x is not None]
    s6 = (sum(parts) / len(parts)) if parts else None
    dims["Q6"] = dict(name="警觉安全", score=round(s6, 1) if s6 is not None else None,
                      evidence={"fall_events": falls, "hrv_sdnn": sdnn},
                      tcm="神清气足则步稳；跌仆多因正气不足、眩晕")
    return dims


def health_score(rec: dict, weights=None) -> dict:
    """健康自动评价：六快加权总分 + 分级 + 中医药提示 + 边界声明。"""
    dims = score_six_quick(rec)
    w = weights or {k: 1.0 for k in dims}
    vals = [(dims[k]["score"], w.get(k, 1.0)) for k in dims if dims[k]["score"] is not None]
    if not vals:
        return dict(total=None, grade="数据不足", dimensions=dims, coverage=0.0,
                    weak_dimensions=[], tcm_hint="无可评维度", disclaimer=DISCLAIMER)
    total = round(sum(s * wt for s, wt in vals) / sum(wt for _, wt in vals), 1)
    weak = sorted([(dims[k]["name"], dims[k]["score"]) for k in dims if dims[k]["score"] is not None],
                  key=lambda x: x[1])[:2]
    return dict(total=total, grade=grade(total), dimensions=dims,
                coverage=round(len(vals) / len(dims), 3),
                weak_dimensions=[n for n, _ in weak],
                tcm_hint="优先关注：" + "、".join(n for n, _ in weak) + "；" +
                         "；".join(dims[k]["tcm"] for k in dims if dims[k]["name"] == weak[0][0]) if weak else "",
                disclaimer=DISCLAIMER)


DISCLAIMER = ("本评分由确定性的启发式规则生成，用于教学与自我记录参考，"
              "不构成医学诊断或治疗建议；异常须就医，不得据以调整用药。")


# ── Fitbit → Google Fit 参考实现的单位/时间换算（复刻 PK 实现口径）──
POUNDS_PER_KILOGRAM = 2.20462
METERS_PER_MILE = 1609.34
NANOS_PER_SECOND = 1000 * 1000 * 1000
NANOS_PER_MINUTE = NANOS_PER_SECOND * 60


def lb_to_kg(lb): return round(lb / POUNDS_PER_KILOGRAM, 4)
def mile_to_m(mi): return round(mi * METERS_PER_MILE, 2)
def minutes_to_nanos(m): return int(m) * NANOS_PER_MINUTE


DEMO_RECORD = dict(steps=8420, distance_mi=3.7, resting_hr=62, hrv_sdnn=41.5,
                   weight_kg=68.2, body_fat_pct=22.4, calories=1980,
                   meals_count=3, water_ml=1500, bowel_count=1, urine_count=6,
                   sleep_minutes=445, fall_events=0, activity_minutes=48)


if __name__ == "__main__":
    import json
    r = health_score(DEMO_RECORD)
    print(json.dumps({k: v for k, v in r.items() if k != "dimensions"}, ensure_ascii=False, indent=1))
    for k, v in r["dimensions"].items():
        print("  %-4s %-6s %s" % (k, v["name"], v["score"]))