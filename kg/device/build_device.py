# -*- coding: utf-8 -*-
"""中医智能仪器与可穿戴设备（D07-S11）· 构建器
以 tcmP 平台为背景支架，把「器械分类 × 可穿戴形态 × 信号通道 × 数据标准 × AI 算子 × 中医药关联」
织成可复现的知识结构，并把 Holter 心律检测做成可运行实测。
产出：kg/device/tcm-device.json（确定性）
用法：python kg/device/build_device.py [--out kg/device]
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import holter as H  # noqa: E402
import neuro as NE  # noqa: E402
import sensing as SD  # noqa: E402
import itcm as IT  # noqa: E402
import wisetcm as WT  # noqa: E402
import curriculum as CU  # noqa: E402

REPO = HERE.parent.parent

CLASSES = [
    dict(id="C1", name="诊断类仪器", examples="脉诊仪、舌象仪、经络检测仪、四诊合参采集终端", signal="压力/图像/阻抗"),
    dict(id="C2", name="治疗类仪器", examples="针灸治疗仪、艾灸温控仪、中频/低频治疗仪、激光针灸", signal="电/热/光"),
    dict(id="C3", name="监护类仪器", examples="Holter 动态心电、动态血压、睡眠监测、可穿戴 PPG", signal="ECG/PPG/压力"),
    dict(id="C4", name="康复类器械", examples="智能推拿机器人、牵引设备、康复评定系统", signal="力/位移/EMG"),
    dict(id="C5", name="中药装备", examples="智能煎药机、调剂系统、炮制温湿度控制、饮片溯源", signal="温湿度/称重/RFID"),
    dict(id="C6", name="可穿戴设备", examples="智能手环/手表、贴片心电、智能衣、舌象拍照终端", signal="多通道融合"),
]
FORMS = [
    dict(id="F1", name="腕带/手表", sensors=["PPG", "加速度", "皮温"], tcm="脉象（浮沉迟数的粗筛）"),
    dict(id="F2", name="胸贴/心电贴", sensors=["ECG(单导/多导)", "呼吸"], tcm="心脉·脉率与节律（Holter 同类）"),
    dict(id="F3", name="智能衣/背心", sensors=["多导ECG", "EMG", "体动"], tcm="胸胁气机、背部俞穴区"),
    dict(id="F4", name="指夹/血氧", sensors=["PPG", "SpO2"], tcm="气血运行（末梢）"),
    dict(id="F5", name="舌象拍照终端", sensors=["RGB/多光谱", "色卡"], tcm="舌质舌苔"),
    dict(id="F6", name="脉象采集仪", sensors=["压力阵列"], tcm="寸关尺三部九候"),
]
SIGNALS = [
    dict(id="S1", name="心电 ECG", fs="250–1000 Hz", feat="HR/SDNN/RMSSD/pNN50/波形特征"),
    dict(id="S2", name="光电容积 PPG", fs="25–100 Hz", feat="脉率/灌注指数/脉搏波形态"),
    dict(id="S3", name="加速度 ACC", fs="25–100 Hz", feat="体动/睡眠分期/步态"),
    dict(id="S4", name="皮温 TEMP", fs="0.1–1 Hz", feat="体表温度分布"),
    dict(id="S5", name="压力 PRESS", fs="100–500 Hz", feat="脉象三部压力曲线"),
    dict(id="S6", name="图像 IMG", fs="—", feat="舌象色度/纹理"),
]
STANDARDS = [
    dict(code="HL7 FHIR Device", name="设备资源与观测资源（Device / Observation）", verify="待核"),
    dict(code="IEEE 11073", name="个人健康设备通信（PHD）", verify="待核"),
    dict(code="ICD-11 / DSU", name="病证编码与单元（平台侧对齐）", verify="已落地"),
    dict(code="平台 DSU-Schema v1", name="病/证/桥/临床/教学/元 六段式", verify="已落地"),
    dict(code="械者契约", name="tcmP sage-api /devices/*（6 端点）", verify="已落地"),
]
OPERATORS = [
    dict(id="D1", name="节律检测", algo="RR 间期阈值+不规则度", use="心动过速/过缓/停搏/早搏/房颤提示"),
    dict(id="D2", name="HRV 时域分析", algo="SDNN/RMSSD/pNN50/CV", use="自主神经张力评估"),
    dict(id="D3", name="脉象特征提取", algo="压力曲线峰谷/主波/重搏波", use="脉位/脉数/脉形量化"),
    dict(id="D4", name="舌象色度分析", algo="色卡校正 + Lab 色域分割", use="舌质舌苔客观化"),
    dict(id="D5", name="多模态融合", algo="通道对齐 + 特征级融合", use="四诊合参的机器化"),
    dict(id="D6", name="设备质量门禁", algo="信号质量指数 SQI / 电量 / 佩戴依从", use="数据可用性判定"),
]
PLATFORM = [
    dict(api="POST /devices/maintenance", use="设备维护预警（械者）"),
    dict(api="POST /devices/imaging", use="影像辅助"),
    dict(api="POST /devices/procurement", use="器械采购论证"),
    dict(api="GET /devices/qc", use="质控校准"),
    dict(api="GET /devices/trace", use="器械溯源"),
    dict(api="POST /devices/emergency", use="急救场景"),
]


def build():
    kinds = ["normal", "tachy", "brady", "pause", "premature", "af"]
    holter = {}
    for k in kinds:
        rr = H.synth(k)
        res = H.analyze(rr)
        holter[k] = dict(rr=rr, metrics=res["metrics"],
                         diagnoses=[d["code"] for d in res["diagnoses"]],
                         tcm_hints=[h["syndrome"] for h in res["tcm_hints"]])
    hb = SD.health_score(SD.DEMO_RECORD)
    sensing = dict(quanta=SD.QUANTA, six_quick=SD.SIX_QUICK, six_quick_quanta=SD.SIX_QUICK_QUANTA,
                   demo_record=SD.DEMO_RECORD, demo_health=hb,
                   conversions=dict(pounds_per_kilogram=SD.POUNDS_PER_KILOGRAM,
                                    meters_per_mile=SD.METERS_PER_MILE,
                                    nanos_per_second=SD.NANOS_PER_SECOND,
                                    nanos_per_minute=SD.NANOS_PER_MINUTE))
    optogenetics = NE.summary()
    intelligent_tcm = IT.summary()
    wise_tcm = WT.summary()
    curriculum_data = CU.summary()
    ref_impl = dict(repo="pkpio/fitbit-googlefit", stars=518,
                    desc="Export Fitbit data to Google Fit (fine granularity)",
                    pipeline="Fitbit API(OAuth2) -> convertors.py unit/time conversion -> Google Fit API",
                    granularity=dict(steps="分钟级", distance="分钟级", heart_rate="秒级",
                                     calories="分钟级", sleep="分钟级", weight="按次", body_fat="按次"),
                    deps=["fitbit==0.3.1", "google-api-python-client==2.65.0", "oauth2client==4.1.3"],
                    note="本平台以相同口径复刻换算常量（见 sensing.py）")
    stats = dict(classes=len(CLASSES), forms=len(FORMS), signals=len(SIGNALS),
                 sensing_quanta=len(SD.QUANTA), six_quick=len(SD.SIX_QUICK),
                 opto_laureates=len(NE.NOBEL_2026['laureates']), health_total=hb['total'],
                 itcm_chapters=len(IT.TOC), itcm_bridge=len(IT.BRIDGE),
                 wise_parts=wise_tcm['stats']['parts'], wise_chapters=wise_tcm['stats']['chapters'],
                 wise_devices=len(WT.TRAINING_DEVICES),
                 cog_levels=curriculum_data['stats']['cog_levels'],
                 matrix_cells=curriculum_data['stats']['matrix_cells'],
                 tensor_axes=curriculum_data['stats']['axes'],
                 standards=len(STANDARDS), operators=len(OPERATORS), platform=len(PLATFORM),
                 holter_cases=len(holter))
    return dict(meta=dict(subject="中医智能仪器与可穿戴设备", code="D07-S11", domain="中医智能学院",
                          version="1.0.0", model="器械分类 × 可穿戴形态 × 信号通道 × 数据标准 × AI 算子 × 中医药关联",
                          generator="kg/device/build_device.py",
                          note="Holter 心律检测为真实算法；验证序列为标注的仿真数据（非临床）",
                          sources=["kg/device/holter.py", "api/main.py(/devices/*)", "data/tcmP-subjects.json"]),
                classes=CLASSES, forms=FORMS, signals=SIGNALS,
                standards=STANDARDS, operators=OPERATORS, platform=PLATFORM,
                holter=holter, sensing=sensing, optogenetics=optogenetics,
                ref_impl=ref_impl, intelligent_tcm=intelligent_tcm, wise_tcm=wise_tcm, curriculum=curriculum_data, stats=stats)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(HERE))
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    data = build()
    s = data["stats"]
    if not (s["classes"] == 6 and s["holter_cases"] == 6 and s["platform"] == 6 and s["sensing_quanta"] == 4 and s["six_quick"] == 6 and s["opto_laureates"] == 3 and s["itcm_chapters"] == 8 and s["wise_chapters"] == 7 and s["wise_devices"] == 7 and s["cog_levels"] == 4 and s["matrix_cells"] == 12 and s["tensor_axes"] == 3):
        print("[校验] 失败", s); raise SystemExit(1)
    (out / "tcm-device.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print("[器械] 分类 %d · 形态 %d · 信号 %d · 标准 %d · 算子 %d · 平台 %d"
          % (s["classes"], s["forms"], s["signals"], s["standards"], s["operators"], s["platform"]))
    for k, v in data["holter"].items():
        print("  Holter[%-9s] HR=%6.1f SDNN=%6.2f RMSSD=%7.2f pNN50=%5.1f -> %s"
              % (k, v["metrics"]["hr"], v["metrics"]["sdnn"], v["metrics"]["rmssd"],
                 v["metrics"]["pnn50"], ",".join(v["diagnoses"])))
    print("  [架构] 认知四阶 %d · 矩阵 %d 格 · 张量轴 %d · 章 %d 篇 %d"
          % (data["curriculum"]["stats"]["cog_levels"], data["curriculum"]["stats"]["matrix_cells"],
             data["curriculum"]["stats"]["axes"], data["curriculum"]["stats"]["chapters"], data["curriculum"]["stats"]["parts"]))
    print("  [扩展] 可感测四元 %d · 六快 %d · 健康评分 %.1f(%s) · Nobel2026 获奖者 %d"
          % (s["sensing_quanta"], s["six_quick"], data["sensing"]["demo_health"]["total"],
             data["sensing"]["demo_health"]["grade"], s["opto_laureates"]))
    print("[产出]", out / "tcm-device.json")


if __name__ == "__main__":
    main()