# -*- coding: utf-8 -*-
"""tcmP 语义张量 · /semtensor/* 端点（标准的机器可读镜像 + 公理指纹）。"""
from __future__ import annotations
import json
import sys
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

ROOT = Path(__file__).resolve().parent.parent
ST = ROOT / "kg" / "semtensor"
sys.path.insert(0, str(ST))
try:
    import axioms as A
except Exception:
    A = None

router = APIRouter(prefix="/semtensor", tags=["语义张量"])
_DATA = None


def _data():
    global _DATA
    if _DATA is None:
        _DATA = json.loads((ST / "semtensor.json").read_text(encoding="utf-8"))
    return _DATA


@router.get("/health")
def health():
    """口径与公理指纹（前端/图注/文档一律读此，不得复制常量）。"""
    d = _data()
    return {"status": "ok", "spec": d["st_meta"]["source"], "version": d["st_meta"]["axiom_fingerprint"]["version"],
            "axiom_fingerprint": d["st_meta"]["axiom_fingerprint"],
            "scope": {"units": d["stats"]["units"], "subjects": d["stats"]["subjects"], "domains": d["stats"]["domains"]}}


@router.get("/spec")
def spec():
    """标准的机器可读镜像：坐标裁定 · 轴端色表 · 合成公理 · 三球镜像 · 编码参数 · 值域。"""
    d = _data()
    return {"standard": d["st_meta"]["source"], "st_meta": d["st_meta"],
            "axes": [{"axis": ax, "name": A.AXIS_NAME[ax] if A else ax,
                      "semantics": A.AXIS_SEMANTICS[ax] if A else [],
                      "end_color": A.AXIS_END_COLOR[ax] if A else [],
                      "hex": [A.HEX[c] for c in A.AXIS_END_COLOR[ax]] if A else [],
                      "wavelength_nm": [A.WAVELENGTH_NM[c] for c in A.AXIS_END_COLOR[ax]] if A else []}
                     for ax in "XYZ"],
            "color_axiom": "C = (1-k)*绿 + k*(Σ w_i·c_i/Σ w_i), w_i=clip(|v_i|,0,1), k=max(w_i)",
            "C_O": d["st_meta"]["axiom_fingerprint"]["C_O"],
            "encode": {"x": "0.60·阴阳 + 0.40·寒热", "y": "0.70·表里 + 0.30·虚实",
                       "z": "(神分−精分)/(精分+气分+神分+1)",
                       "r": "clip(0.35·证据 + 0.35·症状密度 + 0.30·桥接完备, 0.20, 1.00)",
                       "evidence": {"A": 1.00, "B": 0.75, "C": 0.50, "其它": 0.40}},
            "ranges": {"theta": [-90, 90], "phi": [0, 360], "r": [0.0, 1.0]},
            "domains": d["domains"], "stats": d["stats"]}


@router.get("/cloud")
def cloud(scope: str = Query("units", pattern="^(units|subjects|domains)$")):
    d = _data()
    return {"scope": scope, "count": len(d[scope]), "points": d[scope]}


@router.get("/encode/{dsu_id}")
def encode_dsu(dsu_id: str):
    d = _data()
    for u in d["units"]:
        if u["id"] == dsu_id:
            return u
    raise HTTPException(404, f"unknown dsu: {dsu_id}")


@router.get("/encode_text")
def encode_text_(q: str = Query(..., min_length=1)):
    if A is None:
        raise HTTPException(503, "axioms unavailable")
    sys.path.insert(0, str(ST))
    import encoder as E
    return E.encode_text(q)