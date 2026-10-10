# -*- coding: utf-8 -*-
"""中医智能仪器与可穿戴设备 · /device/* 端点（含 Holter 心律检测）。"""
from __future__ import annotations
import json
import sys
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parent.parent
DEV = ROOT / "kg" / "device"
sys.path.insert(0, str(DEV))
try:
    import holter as H
except Exception:
    H = None

router = APIRouter(prefix="/device", tags=["中医智能仪器与可穿戴设备"])
_DATA = None


def _d():
    global _DATA
    if _DATA is None:
        _DATA = json.loads((DEV / "tcm-device.json").read_text(encoding="utf-8"))
    return _DATA


@router.get("/schema")
def schema():
    d = _d()
    return {"subject": d["meta"], "sections": ["classes", "forms", "signals", "standards", "operators", "platform", "holter"], "stats": d["stats"]}


@router.get("/classes")
def classes():
    d = _d(); return {"count": len(d["classes"]), "items": d["classes"]}


@router.get("/forms")
def forms():
    d = _d(); return {"count": len(d["forms"]), "items": d["forms"]}


@router.get("/signals")
def signals():
    d = _d(); return {"count": len(d["signals"]), "items": d["signals"]}


@router.get("/operators")
def operators():
    d = _d(); return {"count": len(d["operators"]), "items": d["operators"]}


@router.get("/stats")
def stats():
    return _d()["stats"]


@router.get("/holter/demo")
def holter_demo():
    return {"count": len(_d()["holter"]), "cases": _d()["holter"], "note": "验证序列为标注的仿真数据，非临床"}


class RRRequest(BaseModel):
    rr_ms: list = []
    note: str = ""


@router.post("/holter/analyze")
def holter_analyze(req: RRRequest):
    if H is None:
        raise HTTPException(503, "holter engine unavailable")
    if not req.rr_ms or len(req.rr_ms) < 2:
        raise HTTPException(422, "rr_ms 至少需要 2 个 RR 间期（ms）")
    return H.analyze(req.rr_ms)