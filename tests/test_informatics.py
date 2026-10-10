# -*- coding: utf-8 -*-
"""中医信息学契约测试（纳入 canonical pytest 套件）。"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
INFO = REPO / "kg" / "informatics"
CAT = INFO / "tcm-informatics.json"


@pytest.fixture(scope="module")
def cat():
    if not CAT.exists():
        subprocess.run([sys.executable, str(REPO / "scripts" / "build_informatics.py")],
                       check=True, capture_output=True, cwd=str(REPO))
    return json.loads(CAT.read_text(encoding="utf-8"))


def test_three_layers_present(cat):
    assert len(cat["standards"]) >= 3
    assert len(cat["assets"]) >= 3
    assert len(cat["operators"]) >= 5


def test_coverage_self_consistent(cat):
    c = cat["icd_coverage"]
    assert c["mapped"] + c["unmapped"] == c["total"] == cat["stats"]["units"]
    assert 0 < c["rate"] <= 1


def test_rules_well_formed(cat):
    assert set(cat["rules"]) == {"symptom_to_syndrome", "syndrome_to_formula", "zangfu_to_formula"}
    for rs in cat["rules"].values():
        for r in rs:
            assert r["left"] and r["right"]
            assert 0 <= r["support"] <= 1 and 0 <= r["confidence"] <= 1.0001 and r["lift"] >= 0


def test_quality_detects_known_anomaly(cat):
    by = cat["data_quality"]["by_field"]
    assert by.get("evidence_level", 0) >= 1        # I级-专家共识 越界
    assert by.get("six_channels", 0) >= 1
    assert by.get("icd11_code", 0) >= 1


def test_clusters_valid(cat):
    assert all(len(set(c["members"])) == c["size"] >= 2 for c in cat["clusters"])


def test_retrieval_engine_deterministic():
    sys.path.insert(0, str(INFO))
    import tcm_mining as M
    docs = [dict(id=u["id"], text=M.doc_text(u)) for u in M.load_units()]
    a = [i for _, i in M.TfidfIndex(docs).retrieve("失眠 多梦", 5)]
    b = [i for _, i in M.TfidfIndex(docs).retrieve("失眠 多梦", 5)]
    assert a == b and len(a) > 0


def test_router_and_e2e_script():
    r = subprocess.run([sys.executable, str(REPO / "scripts" / "verify_informatics.py")],
                       capture_output=True, text=True, timeout=300, cwd=str(REPO))
    assert r.returncode == 0, (r.stdout[-2500:] + "\n" + r.stderr[-1000:])
    assert "自检全部通过" in r.stdout