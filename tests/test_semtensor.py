# -*- coding: utf-8 -*-
"""语义张量契约测试（纳入 canonical pytest 套件）。"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
ST = REPO / "kg" / "semtensor"
sys.path.insert(0, str(ST))
import axioms as A   # noqa: E402
import encoder as E  # noqa: E402

JSON = ST / "semtensor.json"


@pytest.fixture(scope="module")
def data():
    if not JSON.exists():
        subprocess.run([sys.executable, str(ST / "build_semtensor.py")], check=True, capture_output=True)
    return json.loads(JSON.read_text(encoding="utf-8"))


def test_axis_end_colors_exact():
    for ax in "XYZ":
        for i, t in enumerate((-1, 0, 1)):
            got, want = A.ramp(t, ax), A.RGB[A.AXIS_END_COLOR[ax][i]]
            assert all(abs(a - b) < 1e-9 for a, b in zip(got, want))


def test_O_point_returns_base_green():
    assert all(abs(a - b) < 1e-6 for a, b in zip(A.comp(0, 0, 0), A.C_O))
    assert A.C_O_HEX == "#00B050"


def test_sphere_roundtrip_and_specials():
    for th in (-90, -30, 0, 45, 90):
        for ph in (0, 90, 270, 359):
            r, t2, p2 = A.cart2sph(*A.sph2cart(1.0, th, ph))
            assert abs(t2 - th) < 1e-12 and abs(p2 - ph % 360) < 1e-12
    assert all(abs(a - b) < 1e-12 for a, b in zip(A.sph2cart(1, 90, 0), (0, 0, 1)))
    assert all(abs(a - b) < 1e-12 for a, b in zip(A.sph2cart(1, 0, 0), (1, 0, 0)))


def test_mirror_color_invariance():
    import random
    rnd = random.Random(11)
    for _ in range(200):
        v = (rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-1, 1))
        c0 = A.comp(*v)
        for ball in ("母", "子", "父"):
            back = A.mirror_point(A.mirror_point(v, ball), ball)
            assert all(abs(x - y) < 1e-12 for x, y in zip(A.comp(*back), c0))


def test_structure_and_ranges(data):
    us = data["units"]
    assert len(us) == 103 and len({u["id"] for u in us}) == 103
    assert len(data["subjects"]) == 120 and len(data["domains"]) == 8
    for u in us:
        assert -90 <= u["theta"] <= 90 and 0 <= u["phi"] < 360 and 0 < u["r"] <= 1
        assert u["color"].startswith("#") and len(u["color"]) == 7


def test_fingerprint_roundtrip(data):
    fp = data["st_meta"]["axiom_fingerprint"]
    assert fp["version"] == A.VERSION
    assert fp["axis_end_color"] == {k: list(v) for k, v in A.AXIS_END_COLOR.items()}
    assert fp["C_O"] == A.C_O_HEX


def test_encoder_deterministic():
    f = sorted((REPO / "kg" / "samples").glob("dsu-samples-*.json"))[0]
    u = json.loads(f.read_text(encoding="utf-8"))
    units = u.get("units", u) if isinstance(u, dict) else u
    a = E.encode_unit(units[0])
    b = E.encode_unit(units[0])
    assert a == b and "x" in a and "octant" in a


def test_verify_script_green():
    r = subprocess.run([sys.executable, str(ST / "verify_semtensor.py")],
                       capture_output=True, text=True, timeout=300, cwd=str(REPO))
    assert r.returncode == 0, (r.stdout[-2000:] + r.stderr[-500:])
    assert "校验规范全部通过" in r.stdout