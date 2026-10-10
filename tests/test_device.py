# -*- coding: utf-8 -*-
"""中医智能仪器与可穿戴设备契约测试（纳入 canonical pytest 套件）。"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
DEV = REPO / "kg" / "device"
sys.path.insert(0, str(DEV))
import holter as H  # noqa: E402

JSON = DEV / "tcm-device.json"


@pytest.fixture(scope="module")
def data():
    if not JSON.exists():
        subprocess.run([sys.executable, str(DEV / "build_device.py")], check=True, capture_output=True)
    return json.loads(JSON.read_text(encoding="utf-8"))


def test_normal_sinus():
    r = H.analyze(H.synth("normal"))
    assert [d["code"] for d in r["diagnoses"]] == ["NORMAL_SINUS"]
    assert 60 <= r["metrics"]["hr"] <= 100


@pytest.mark.parametrize("kind,code", [("tachy", "SINUS_TACHYCARDIA"), ("brady", "SINUS_BRADYCARDIA"),
                                       ("pause", "PAUSE"), ("premature", "PREMATURE_BEAT"), ("af", "AF_SUSPECT")])
def test_rhythm_detection(kind, code):
    assert code in [d["code"] for d in H.analyze(H.synth(kind))["diagnoses"]]


def test_severity_ordering_and_disclaimer():
    r = H.analyze(H.synth("pause"))
    assert r["diagnoses"][0]["level"] == "danger"
    assert "不构成医学诊断" in r["disclaimer"]
    assert r["tcm_hints"]


def test_input_robustness():
    assert "error" in H.hrv_metrics([])
    assert "error" in H.hrv_metrics([800])
    assert H.hrv_metrics([800, 0, -5, 810])["n"] == 2


def test_deterministic():
    assert H.analyze(H.synth("af")) == H.analyze(H.synth("af"))


def test_dataset_shape(data):
    assert data["meta"]["code"] == "D07-S11"
    s = data["stats"]
    assert (s["classes"], s["forms"], s["signals"], s["operators"], s["platform"]) == (6, 6, 6, 6, 6)
    assert set(data["holter"]) == {"normal", "tachy", "brady", "pause", "premature", "af"}


def test_verify_script_green():
    r = subprocess.run([sys.executable, str(DEV / "verify_device.py")],
                       capture_output=True, text=True, timeout=300, cwd=str(REPO))
    assert r.returncode == 0, (r.stdout[-2000:] + r.stderr[-500:])
    assert "自检全部通过" in r.stdout