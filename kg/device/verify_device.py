# -*- coding: utf-8 -*-
"""中医智能仪器与可穿戴设备 · 自检（标准库，硬证据）。"""
import json
import subprocess
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

JSON = HERE / "tcm-device.json"
ok = fail = 0


def check(name, cond, detail=""):
    global ok, fail
    if cond:
        ok += 1; print("  [OK] " + name)
    else:
        fail += 1; print("  [XX] " + name + "  " + str(detail))


def main():
    print("=" * 62); print(" 中医智能仪器与可穿戴设备 · 自检"); print("=" * 62)
    normal = H.analyze(H.synth("normal"))
    check("正常窦律判读", [d["code"] for d in normal["diagnoses"]] == ["NORMAL_SINUS"], normal["diagnoses"])
    check("正常 HR 落在 60–100", 60 <= normal["metrics"]["hr"] <= 100, normal["metrics"]["hr"])
    check("HRV 指标齐备", all(k in normal["metrics"] for k in ("hr", "sdnn", "rmssd", "pnn50", "cv")))

    t = H.analyze(H.synth("tachy"))
    check("心动过速识别 (HR>100)", "SINUS_TACHYCARDIA" in [d["code"] for d in t["diagnoses"]], t["metrics"]["hr"])
    b = H.analyze(H.synth("brady"))
    check("心动过缓识别 (HR<60)", "SINUS_BRADYCARDIA" in [d["code"] for d in b["diagnoses"]], b["metrics"]["hr"])
    p = H.analyze(H.synth("pause"))
    check("停搏识别 (RR≥2500ms)", "PAUSE" in [d["code"] for d in p["diagnoses"]])
    pr = H.analyze(H.synth("premature"))
    check("早搏偶联识别", "PREMATURE_BEAT" in [d["code"] for d in pr["diagnoses"]])
    af = H.analyze(H.synth("af"))
    check("房颤提示（高不规则度）", "AF_SUSPECT" in [d["code"] for d in af["diagnoses"]], af["metrics"])

    check("严重度排序（danger 优先）", p["diagnoses"][0]["level"] == "danger")
    check("空/单点输入不崩", "error" in H.hrv_metrics([]) and "error" in H.hrv_metrics([800]))
    check("非正 RR 被过滤", H.hrv_metrics([800, 0, -5, 810])["n"] == 2)
    check("中医药关联有输出", len(H.analyze(H.synth("af"))["tcm_hints"]) >= 1)
    check("边界声明存在", "不构成医学诊断" in H.analyze(H.synth("normal"))["disclaimer"])

    # 确定性：同输入必得同输出
    check("分析确定性", H.analyze(H.synth("af")) == H.analyze(H.synth("af")))

    data = json.loads(JSON.read_text(encoding="utf-8"))
    s = data["stats"]
    check("六类器械 / 六形态 / 六信号 / 六算子", (s["classes"], s["forms"], s["signals"], s["operators"]) == (6, 6, 6, 6), s)
    check("平台 械者 6 端点登记", s["platform"] == 6)
    check("Holter 六场景齐备", set(data["holter"]) == {"normal", "tachy", "brady", "pause", "premature", "af"})
    check("D07-S11 归属正确", data["meta"]["code"] == "D07-S11" and data["meta"]["domain"] == "中医智能学院")

    # ── 扩展层：可感测四元 / 六快 / 健康自动评价 / 光遗传学 / 参考实现 ──
    check("四元可感测物理量=4（光子/电/质量/运动）", [q["id"] for q in SD.QUANTA] == ["P", "E", "M", "K"], [q["id"] for q in SD.QUANTA])
    check("六快=6（吃喝拉撒睡+警觉安全）", [q["name"] for q in SD.SIX_QUICK] == ["吃", "喝", "拉", "撒", "睡", "警觉安全"])
    hs = SD.health_score(SD.DEMO_RECORD)
    check("健康自动评价输出总分与分级", hs["total"] is not None and hs["grade"] in ("优", "良", "中", "差"), hs["grade"])
    check("六快每维均有评分", sum(1 for v in hs["dimensions"].values() if v["score"] is not None) == 6)
    check("评价含边界声明", "不构成医学诊断" in hs["disclaimer"])
    check("评价确定性", SD.health_score(SD.DEMO_RECORD) == SD.health_score(SD.DEMO_RECORD))
    check("缺数据覆盖率正确（1/6）", SD.health_score({"sleep_minutes": 420})["coverage"] == round(1 / 6, 3))
    check("无可评维度返回「数据不足」且 coverage=0", SD.health_score({"steps": 100})["coverage"] == 0.0 and SD.health_score({"steps": 100})["grade"] == "数据不足")
    check("单位换算口径（150lb / 1mile / 1min）",
          abs(SD.lb_to_kg(150) - 68.0389) < 1e-3 and abs(SD.mile_to_m(1) - 1609.34) < 0.01 and SD.minutes_to_nanos(1) == 60000000000)
    nw = NE.summary()
    check("Nobel2026 光遗传学三获奖者", nw["nobel"]["laureates"] == ["Karl Deisseroth", "Peter Hegemann", "Georg Nagel"])
    check("光遗传学边界声明齐备（>=4 条）", len(nw["boundary"]) >= 4 and any("不得作为临床疗法宣传" in b for b in nw["boundary"]))
    check("数据集含扩展层（sensing/optogenetics/ref_impl）", set(("sensing", "optogenetics", "ref_impl")).issubset(data.keys()))
    check("参考实现登记（fitbit-googlefit）", data["ref_impl"]["repo"] == "pkpio/fitbit-googlefit")
    # ── 智能中医学对接层（对标《智能中医学概论》2021）──
    it = IT.summary()
    check("书目：人民卫生出版社 2021-11 · ISBN 9787117323505",
          it["book"]["publisher"] == "人民卫生出版社" and it["book"]["date"] == "2021-11" and it["book"]["isbn"] == "9787117323505")
    check("作者 = 田贵华 · 商洪才", it["book"]["authors"] == ["田贵华", "商洪才"])
    check("七章目录（含绪言共 8 条）", it["stats"]["chapters"] == 8 and len(it["toc"]) == 8)
    check("辨证框架 = 象—素—候—证", it["framework"] == "象—素—候—证")
    check("发展理念 = 数据筑基、智慧引航", it["motto"] == "数据筑基、智慧引航")
    check("典型应用 = 中医慢性疼痛智能诊疗", it["case"] == "中医慢性疼痛智能诊疗")
    check("对接点 >=5 且含「四诊数据采集」", it["stats"]["bridge_points"] >= 5 and any("四诊数据采集" in b["book"] for b in it["bridge"]))
    check("数据集含 intelligent_tcm", "intelligent_tcm" in data)
    # ── 智慧中医学对接层（对标《智慧中医学》高教社 2026）──
    wt = WT.summary()
    check("书目：高等教育出版社 2026-03-05 · ISBN 9787040652802",
          wt["book"]["publisher"] == "高等教育出版社" and wt["book"]["date"] == "2026-03-05" and wt["book"]["isbn"] == "9787040652802")
    check("三篇七章结构", wt["stats"]["parts"] == 3 and wt["stats"]["chapters"] == 7)
    check("实训设备 7 件（含四诊仪/艾灸机器人）",
          wt["stats"]["devices"] == 7 and any("艾灸机器人" in d["name"] for d in wt["training_devices"]))
    check("问题导向改进对象 3 件", wt["stats"]["improve"] == 3)
    check("生成式 AI 含 DeepSeek", "开源高性能大模型 DeepSeek" in wt["genai"])
    check("扩展现实/智能装备在技术列表内", "扩展现实" in wt["tech"] and "智能装备" in wt["tech"])
    check("伦理要求 4 条 + 基本条件 2 条", len(wt["ethics"]) == 4 and len(wt["basic_conditions"]) == 2)
    check("发展趋势 6 条", wt["stats"]["trends"] == 6)
    check("数据集含 wise_tcm", "wise_tcm" in data)
    # ── 课程架构层：认知四阶 × 语义张量（v2.0 重构依据）──
    cu = CU.summary()
    check("认知四阶 = L1 感知/L2 理解/L3 应用/L4 创造", [l["name"] for l in cu["ladder"]] == ["感知阶", "理解阶", "应用阶", "创造阶"])
    check("四阶与「象—素—候/证—造」同构", [l["tcm"] for l in cu["ladder"]] == ["象", "素", "候/证", "造"])
    check("语义张量三轴（阴阳/表里/精气神）", [a["axis"] for a in cu["axes"]] == ["X", "Y", "Z"])
    check("四阶×三轴矩阵 12 格且每格有落点", cu["stats"]["matrix_cells"] == 12 and all(m["cell"] for m in cu["matrix"]))
    check("四元→张量 Z 轴（M 精 / E 气 / P·K 神）",
          [cu["quanta_to_tensor"][k]["semantic"] for k in ("M", "E", "P", "K")] == ["精", "气", "神", "神"])
    dd = cu["discipline"]
    check("D07-S11 定位与 8 域 120 学科分布", dd["code"] == "D07-S11" and dd["stats" if False else "total_subjects"] == 120 and len(dd["domains"]) == 8)
    check("D07 张量锚点 = Z 轴「神」极 (0,0,+0.5)", dd["domain_anchor"]["anchor"] == {"x": 0.0, "y": 0.0, "z": 0.5} and dd["domain_anchor"]["theta"] == 90.0)
    check("全书 6 篇 26 章", cu["stats"]["parts"] == 6 and cu["stats"]["chapters"] == 26)
    check("数据集含 curriculum", "curriculum" in data)
    # 确定性构建
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        subprocess.run([sys.executable, str(HERE / "build_device.py"), "--out", td], check=True, capture_output=True)
        check("构建确定性（两次构建字节一致）", JSON.read_bytes() == (Path(td) / "tcm-device.json").read_bytes())

    print("-" * 62)
    print(" 结果：%d 通过 / %d 失败" % (ok, fail))
    if not fail:
        print(" 自检全部通过 ✓")
    print("=" * 62)
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())