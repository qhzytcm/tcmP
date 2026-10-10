# -*- coding: utf-8 -*-
"""中医智能仪器 · Holter 心律检测与 HRV 分析（零依赖）
对标：D07-S11《中医智能仪器与可穿戴设备》
输入：RR 间期序列（ms）。输出：时域 HRV 指标 + 节律判读 + 中医药关联提示。
⚠️ 本模块算法为真实实现；验证使用**标注的仿真 RR 序列**（非临床数据）。
"""
from __future__ import annotations
import math

NORMAL_HR = (60.0, 100.0)


def hrv_metrics(rr_ms):
    """时域 HRV：HR · SDNN · RMSSD · pNN50 · CV。"""
    rr = [float(x) for x in rr_ms if x and x > 0]
    if len(rr) < 2:
        return {"n": len(rr), "error": "insufficient RR intervals"}
    n = len(rr)
    mean_rr = sum(rr) / n
    var = sum((x - mean_rr) ** 2 for x in rr) / (n - 1)
    sdnn = math.sqrt(var)
    diffs = [rr[i + 1] - rr[i] for i in range(n - 1)]
    rmssd = math.sqrt(sum(d * d for d in diffs) / len(diffs))
    pnn50 = 100.0 * sum(1 for d in diffs if abs(d) > 50) / len(diffs)
    return dict(n=n, hr=round(60000.0 / mean_rr, 2), mean_rr=round(mean_rr, 1),
                sdnn=round(sdnn, 2), rmssd=round(rmssd, 2), pnn50=round(pnn50, 2),
                cv=round(sdnn / mean_rr, 4))


def detect_rhythm(rr_ms, pause_ms=2500.0):
    """节律判读：心动过速 / 心动过缓 / 停搏 / 早搏(短-长偶联) / 房颤提示。"""
    m = hrv_metrics(rr_ms)
    flags = []
    if "error" in m:
        return {"metrics": m, "diagnoses": [{"code": "DATA_INSUFFICIENT", "level": "warning",
                "note": "RR 序列不足，无法判读"}]}
    hr = m["hr"]
    if hr > NORMAL_HR[1]:
        flags.append(dict(code="SINUS_TACHYCARDIA", level="warning",
                          note="心率 > 100 bpm（心动过速）"))
    if hr < NORMAL_HR[0]:
        flags.append(dict(code="SINUS_BRADYCARDIA", level="warning",
                          note="心率 < 60 bpm（心动过缓）"))
    rr = [float(x) for x in rr_ms if x and x > 0]
    for i in range(len(rr) - 1):
        if rr[i] >= pause_ms:
            flags.append(dict(code="PAUSE", level="danger", at=i,
                              note="RR ≥ %.0f ms（停搏/长间歇）" % pause_ms))
            break
    for i in range(len(rr) - 1):
        if rr[i] < 0.8 * m["mean_rr"] and rr[i + 1] > 1.15 * m["mean_rr"]:
            flags.append(dict(code="PREMATURE_BEAT", level="info", at=i,
                              note="短-长偶联，提示早搏（期前收缩）"))
            break
    if m["rmssd"] > 120 and m["pnn50"] > 45 and m["cv"] > 0.12:
        flags.append(dict(code="AF_SUSPECT", level="warning",
                          note="RR 高度不规则（RMSSD/pNN50/CV 同高），提示房颤可能，需医师确认"))
    if not flags:
        flags.append(dict(code="NORMAL_SINUS", level="normal", note="窦性节律，未见明显异常"))
    order = {"danger": 0, "warning": 1, "info": 2, "normal": 3}
    flags.sort(key=lambda f: order[f["level"]])
    return {"metrics": m, "diagnoses": flags}


# ── 中医药关联（规则表 · 平台裁定，供教学/研究，不构成诊断）──
TCM_RULES = [
    dict(when="hr>100 且 rmssd>60", tcm="心火亢盛 / 阴虚火旺（心悸、心烦）", basis="心率快而变异保留"),
    dict(when="hr>100 且 rmssd<=60", tcm="心气不足兼热（气虚发热、心神不宁）", basis="心率快而变异降低"),
    dict(when="hr<60 且 sdnn>80", tcm="心阳不振（迟脉、畏寒）", basis="心率慢而变异高"),
    dict(when="sdnn<30", tcm="心气虚 / 心脉瘀阻（自主神经调节减退）", basis="HRV 总变异降低"),
    dict(when="AF_SUSPECT", tcm="心悸、怔忡（脉结代 / 促 / 涩）", basis="节律绝对不齐"),
]


def map_to_tcm(metrics, diagnoses):
    """把 HRV 指标与节律判读映射到中医证候**提示**（非诊断）。"""
    codes = {d["code"] for d in diagnoses}
    hit = []
    hr, sdnn, rmssd = metrics.get("hr", 0), metrics.get("sdnn", 0), metrics.get("rmssd", 0)
    if hr > 100 and rmssd > 60:
        hit.append(TCM_RULES[0])
    if hr > 100 and rmssd <= 60:
        hit.append(TCM_RULES[1])
    if hr < 60 and sdnn > 80:
        hit.append(TCM_RULES[2])
    if sdnn < 30:
        hit.append(TCM_RULES[3])
    if "AF_SUSPECT" in codes:
        hit.append(TCM_RULES[4])
    return [dict(syndrome=h["tcm"], basis=h["basis"], rule=h["when"]) for h in hit] or \
           [dict(syndrome="（未见明确证候倾向）", basis="指标均在参考区间", rule="-")]


def analyze(rr_ms):
    r = detect_rhythm(rr_ms)
    r["tcm_hints"] = map_to_tcm(r["metrics"], r["diagnoses"]) if "error" not in r["metrics"] else []
    r["disclaimer"] = "本结果由算法生成，仅供教学/研究参考，不构成医学诊断；临床须由医师结合症状、舌脉与体征判断。"
    return r


# ── 确定性仿真序列（用于自检，非临床数据）──
def synth(kind, n=60):
    if kind == "normal":
        return [round(800 + 40 * math.sin(i * 0.7)) for i in range(n)]
    if kind == "tachy":
        return [round(560 + 20 * math.sin(i * 0.7)) for i in range(n)]
    if kind == "brady":
        return [round(1200 + 30 * math.sin(i * 0.7)) for i in range(n)]
    if kind == "pause":
        s = [round(800 + 20 * math.sin(i * 0.7)) for i in range(n)]
        s[20] = 3200
        return s
    if kind == "premature":
        s = [round(800 + 20 * math.sin(i * 0.7)) for i in range(n)]
        s[15] = 520
        s[16] = 1000
        return s
    if kind == "af":
        return [round(780 + 220 * math.sin(i * 1.9) * math.cos(i * 0.37)) for i in range(n)]
    raise ValueError("unknown kind: %s" % kind)


if __name__ == "__main__":
    import json
    import sys
    kinds = sys.argv[1:] or ["normal", "tachy", "brady", "pause", "premature", "af"]
    for k in kinds:
        print("=== %s ===" % k)
        print(json.dumps(analyze(synth(k)), ensure_ascii=False, indent=1)[:600])