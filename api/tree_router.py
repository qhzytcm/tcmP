# -*- coding: utf-8 -*-
"""
中医知识树 · sage-api 路由挂载（应用层）
=====================================================================
把「中医知识树」作为平台的**统一知识结构**注入 sage-api：
        /tree/stats            结构统计
        /tree/meta             元信息
        /tree/levels           层级刻度
        /tree/node/{nid}       节点详情（含 code5 编码与属性）
        /tree/children/{nid}   子节点
        /tree/path/{nid}       根→节点 祖先链
        /tree/neighbors/{nid}  图邻接（可 ?rel= 过滤边型）
        /tree/search?q=        全文检索（可 ?level=/?kind=/?limit=）

挂载方式（在 main.py 末尾追加，幂等、失败不阻断）：
    try:
        from tree_router import router as tree_router
        app.include_router(tree_router)
    except Exception as e:
        import logging; logging.getLogger("uvicorn").warning(f"knowledge-tree not mounted: {e}")

数据源：<repo>/kg/tree/tcm-knowledge-tree.json（由 scripts/build_knowledge_tree.py 生成）
"""
from __future__ import annotations

import sys
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

TREE_DIR = Path(__file__).resolve().parent.parent / "kg" / "tree"
if str(TREE_DIR) not in sys.path:
    sys.path.insert(0, str(TREE_DIR))

from tcm_tree import KnowledgeTree  # noqa: E402

router = APIRouter(prefix="/tree", tags=["中医知识树"])
_TREE = None


def tree() -> KnowledgeTree:
    global _TREE
    if _TREE is None:
        _TREE = KnowledgeTree(TREE_DIR / "tcm-knowledge-tree.json")
    return _TREE


@router.get("/stats")
def tree_stats():
    """知识树结构统计（节点/边/层级/边型）。"""
    t = tree()
    return {"ok": True, "name": t.meta.get("name", "中医知识树"),
            "version": t.meta.get("version"), "stats": t.stats,
            "levels": t.level_counts(), "edge_types": t.edge_counts()}


@router.get("/meta")
def tree_meta():
    return {"ok": True, "meta": tree().meta}


@router.get("/levels")
def tree_levels():
    t = tree()
    return {"ok": True, "levels": [
        {"index": 0, "key": "hair", "zh": "须", "meaning": "哲学根基（根须吸养）"},
        {"index": 1, "key": "root", "zh": "根", "meaning": "核心公理"},
        {"index": 2, "key": "trunk", "zh": "干", "meaning": "院系域主干"},
        {"index": 3, "key": "branch", "zh": "枝", "meaning": "学科分枝"},
        {"index": 4, "key": "leaf", "zh": "叶", "meaning": "终末知识点 / 病证单元"},
    ], "counts": t.level_counts()}


@router.get("/node/{nid}")
def tree_node(nid: str):
    n = tree().node(nid)
    if not n:
        raise HTTPException(status_code=404, detail=f"节点不存在: {nid}")
    return {"ok": True, "node": n}


@router.get("/children/{nid}")
def tree_children(nid: str):
    t = tree()
    if nid not in t.nodes:
        raise HTTPException(status_code=404, detail=f"节点不存在: {nid}")
    return {"ok": True, "parent": nid,
            "children": [{"id": c["id"], "name": c["name"], "level": c["level"],
                          "kind": c["kind"]} for c in t.children(nid)]}


@router.get("/path/{nid}")
def tree_path(nid: str):
    t = tree()
    if nid not in t.nodes:
        raise HTTPException(status_code=404, detail=f"节点不存在: {nid}")
    return {"ok": True, "path": [{"id": n["id"], "name": n["name"], "level": n["level"]}
                                 for n in t.path(nid)]}


@router.get("/neighbors/{nid}")
def tree_neighbors(nid: str, rel: str = Query(None, description="按边型过滤")):
    t = tree()
    if nid not in t.nodes:
        raise HTTPException(status_code=404, detail=f"节点不存在: {nid}")
    if not isinstance(rel, str):
        rel = None  # 允许函数级直调（HTTP 未传时 rel 为 FieldInfo）
    return {"ok": True, "id": nid, "neighbors": t.neighbors_full(nid, rel)}


@router.get("/search")
def tree_search(q: str = Query(..., min_length=1), level: str = None,
                kind: str = None, limit: int = 30):
    hits = tree().search(q, level=level, kind=kind, limit=limit)
    return {"ok": True, "q": q, "count": len(hits),
            "hits": [{"id": n["id"], "name": n["name"], "level": n["level"],
                      "kind": n["kind"]} for n in hits]}
