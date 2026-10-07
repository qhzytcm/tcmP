# -*- coding: utf-8 -*-
"""中医知识树（kg/tree）契约测试 —— 纳入仓库 canonical 套件。

覆盖：结构完整性 / 树导航 / 图邻接 / 检索 / API 路由函数级。
构建物缺失或陈旧时跳过（由 scripts/build_knowledge_tree.py 生成）。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
TREE_DIR = REPO / "kg" / "tree"
TREE_JSON = TREE_DIR / "tcm-knowledge-tree.json"

pytestmark = pytest.mark.skipif(not TREE_JSON.exists(),
                                reason="知识树未构建：先跑 scripts/build_knowledge_tree.py")

sys.path.insert(0, str(TREE_DIR))
sys.path.insert(0, str(REPO / "api"))

from tcm_tree import KnowledgeTree  # noqa: E402


@pytest.fixture(scope="module")
def t():
    return KnowledgeTree()


def test_structure_shape(t):
    s = t.stats
    assert s["levels"]["trunk"] == 8 and s["levels"]["branch"] == 120
    assert s["chapter_coverage"] == "120/120"
    assert s["nodes"] > 2500 and s["edges"] > 2500


def test_no_duplicate_ids_and_no_dangling_edges(t):
    raw = json.loads(TREE_JSON.read_text(encoding="utf-8"))
    ids = [n["id"] for n in raw["nodes"]]
    assert len(ids) == len(set(ids))
    idset = set(ids)
    assert all(e["source"] in idset and e["target"] in idset for e in raw["edges"])


def test_tree_navigation(t):
    assert t.node("D07-S04")["name"] == "中医知识图谱"
    assert [x["id"] for x in t.path("D07-S04")] == ["D07", "D07-S04"]
    assert len(t.children("D07")) == 14
    assert [x["id"] for x in t.path("DSU-00001")] == ["D01", "D01-S13", "DSU-00001"]


def test_graph_edges(t):
    rels = {x["type"] for x in t.neighbors_full("DSU-00001")}
    assert {"icd11_map", "manifests_as", "disease_is", "bridge"} <= rels
    # 五行生克自洽：木生火、水（被）生木；木克土、金克木
    sheng = t.neighbors_full("W-木", "wuxing_sheng")
    assert any(x["dir"] == "out" and x["id"] == "W-火" for x in sheng)
    assert any(x["dir"] == "in" and x["id"] == "W-水" for x in sheng)
    # 六经传变：太阳→阳明
    assert t.neighbors_full("SC-1", "six_chuanbian")[0]["id"] == "SC-2"


def test_search(t):
    assert any(h["id"] == "D07-S04" for h in t.search("知识图谱"))


def test_router_and_e2e_script():
    """API 路由 + 端到端自检：以子进程运行（隔离 fastapi 导入——本机 pytest 内导入
    fastapi 会挂起，见 pytest.ini 的 anyio 说明），并带硬超时。"""
    import subprocess
    r = subprocess.run([sys.executable, str(REPO / "scripts" / "verify_knowledge_tree.py")],
                       capture_output=True, text=True, timeout=180, cwd=str(REPO))
    assert r.returncode == 0, (r.stdout[-2000:] + "\n" + r.stderr[-1000:])
    assert "自检全部通过" in r.stdout
