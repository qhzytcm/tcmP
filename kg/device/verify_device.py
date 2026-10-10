# -*- coding: utf-8 -*-
"""中医智能仪器与可穿戴设备 · 自检（标准库，硬证据）。"""
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import holter as H  # noqa: E402

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