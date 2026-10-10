# -*- coding: utf-8 -*-
"""中医信息学 · /informatics/* 端点（挂载于 sage-api）。"""
from __future__ import annotations
import json
import sys
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "kg" / "informatics"))
try:
    import tcm_mining as M
except Exception:  # 引擎缺失时降级为只读目录
    M = None

router = APIRouter(prefix="/informatics", tags=["中医信息学"])


def _cat() -> dict:
    if M is not None:
        return M.load_catalog()
    return json.loads((ROOT / "kg" / "informatics" / "tcm-informatics.json").read_text(encoding="utf-8"))


@router.get("/stats")
def stats():
    return _cat()["stats"]


@router.get("/standards")
def standards():
    return {"count": len(_cat()["standards"]), "items": _cat()["standards"]}


@router.get("/assets")
def assets():
    return {"count": len(_cat()["assets"]), "items": _cat()["assets"]}


@router.get("/operators")
def operators():
    return {"count": len(_cat()["operators"]), "items": _cat()["operators"]}


@router.get("/dist/{key}")
def dist(key: str):
    d = _cat()["distributions"].get(key)
    if d is None:
        raise HTTPException(404, f"unknown distribution key: {key}")
    return {"key": key, "items": d}


@router.get("/rules/{kind}")
def rules(kind: str):
    r = _cat()["rules"].get(kind)
    if r is None:
        raise HTTPException(404, f"unknown rule kind: {kind}")
    return {"kind": kind, "count": len(r), "items": r}


@router.get("/clusters")
def clusters():
    c = _cat()["clusters"]
    return {"count": len(c), "items": c}


@router.get("/coverage")
def coverage():
    return _cat()["icd_coverage"]


@router.get("/quality")
def quality():
    return _cat()["data_quality"]


@router.get("/retrieve")
def retrieve(q: str = Query(..., min_length=1), k: int = Query(5, ge=1, le=20)):
    if M is None:
        raise HTTPException(503, "mining engine unavailable")
    units = M.load_units()
    idx = M.TfidfIndex([dict(id=u["id"], text=M.doc_text(u)) for u in units])
    vec = [i for _, i in idx.retrieve(q, k)]
    lex = [u["id"] for u in sorted(
        units, key=lambda u: -len(set(M.bigrams(q)) & set(M.bigrams(M.doc_text(u)))))[:k]]
    fused = [d for d, _ in M.rrf([vec, lex])][:k]
    return {"q": q, "k": k, "vector": vec, "lexical": lex, "rrf": fused,
            "meta": {"fusion": "RRF(k=60)", "vectorizer": "char-bigram TF-IDF"}}