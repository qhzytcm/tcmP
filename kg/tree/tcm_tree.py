# -*- coding: utf-8 -*-
"""
中医知识树 · 运行时查询引擎（树图一体）
=====================================================================
读取 build_knowledge_tree.py 产出的 tcm-knowledge-tree.json，
提供「树导航 + 图邻接 + 全文检索 + 补全」四类只读查询，供
sage-api、六者 Agent、教材工具链与 PWA 终端调用。

零外部依赖（stdlib）。可作为库导入，也可作 CLI：
    python tcm_tree.py stats
    python tcm_tree.py node D07-S04
    python tcm_tree.py path DSU-00001
    python tcm_tree.py children W-木
    python tcm_tree.py neighbors DSU-00001 --rel icd11_map
    python tcm_tree.py search 桂枝汤
    python tcm_tree.py subtree D07
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

DEFAULT_PATH = Path(__file__).resolve().parent / "tcm-knowledge-tree.json"


class KnowledgeTree:
    """树图一体知识结构：树（层）＋图（边）。"""

    def __init__(self, path=None):
        self.source_path = Path(path) if path else DEFAULT_PATH
        data = json.loads(self.source_path.read_text(encoding="utf-8"))
        self.meta = data.get("meta", {})
        self.stats = data.get("stats", {})
        self._nodes = data.get("nodes", [])
        self.nodes = {n["id"]: n for n in self._nodes}
        self.edges = data.get("edges", [])
        self.out, self.inc, self._children = {}, {}, {}
        for e in self.edges:
            self.out.setdefault(e["source"], []).append(e)
            self.inc.setdefault(e["target"], []).append(e)
        for n in self._nodes:
            if n.get("parent"):
                self._children.setdefault(n["parent"], []).append(n["id"])

    # ── 树导航 ──
    def node(self, nid):
        return self.nodes.get(nid)

    def children(self, nid):
        return [self.nodes[c] for c in self._children.get(nid, [])]

    def parent(self, nid):
        n = self.nodes.get(nid)
        return self.nodes.get(n["parent"]) if n and n.get("parent") else None

    def path(self, nid):
        """从根到该节点的祖先链（含自身）。"""
        chain, cur = [], nid
        while cur and cur in self.nodes:
            chain.append(self.nodes[cur])
            cur = self.nodes[cur].get("parent")
        return list(reversed(chain))

    def subtree(self, root_id):
        """以某节点为根的子树全部 id（含自身，BFS）。"""
        out, stack = [], [root_id]
        while stack:
            cur = stack.pop()
            if cur not in self.nodes:
                continue
            out.append(cur)
            stack.extend(self._children.get(cur, []))
        return out

    # ── 图邻接 ──
    def neighbors(self, nid, rel=None, direction="both"):
        res = []
        if direction in ("out", "both"):
            res += [e for e in self.out.get(nid, []) if not rel or e["type"] == rel]
        if direction in ("in", "both"):
            res += [e for e in self.inc.get(nid, []) if not rel or e["type"] == rel]
        return res

    def neighbors_full(self, nid, rel=None, direction="both"):
        """返回带对端节点信息的邻居列表。"""
        out = []
        for e in self.neighbors(nid, rel, direction):
            other = e["target"] if e["source"] == nid else e["source"]
            out.append(dict(type=e["type"], dir=("out" if e["source"] == nid else "in"),
                            id=other, name=self.nodes.get(other, {}).get("name", "")))
        return out

    # ── 检索 ──
    def search(self, kw, level=None, kind=None, limit=30):
        hits = []
        for n in self._nodes:
            if level and n.get("level") != level:
                continue
            if kind and n.get("kind") != kind:
                continue
            if kw in n.get("name", "") or kw == n.get("id"):
                hits.append(n)
                if len(hits) >= limit:
                    break
        return hits

    def by_level(self, level):
        return [n for n in self._nodes if n.get("level") == level]

    def by_kind(self, kind):
        return [n for n in self._nodes if n.get("kind") == kind]

    def level_counts(self):
        return dict(Counter(n["level"] for n in self._nodes))

    def edge_counts(self):
        return dict(Counter(e["type"] for e in self.edges))


# ── CLI ────────────────────────────────────────────────────────────
def _main(argv):
    t = KnowledgeTree()
    cmd = argv[0] if argv else "stats"
    if cmd == "stats":
        print(json.dumps(dict(meta=t.meta, stats=t.stats), ensure_ascii=False, indent=2))
    elif cmd == "node" and len(argv) > 1:
        print(json.dumps(t.node(argv[1]), ensure_ascii=False, indent=2))
    elif cmd == "children" and len(argv) > 1:
        for c in t.children(argv[1]):
            print(f"  {c['id']:20s} {c['level']:14s} {c['name']}")
    elif cmd == "path" and len(argv) > 1:
        for n in t.path(argv[1]):
            print(f"  {'  ' * n['level_index']}{n['id']:20s} {n['name']}")
    elif cmd == "neighbors" and len(argv) > 1:
        rel = argv[argv.index("--rel") + 1] if "--rel" in argv else None
        for nb in t.neighbors_full(argv[1], rel):
            print(f"  [{nb['dir']}] {nb['type']:16s} {nb['id']}  {nb['name']}")
    elif cmd == "search" and len(argv) > 1:
        for n in t.search(argv[1]):
            print(f"  {n['id']:20s} {n['level']:14s} {n['name']}")
    elif cmd == "subtree" and len(argv) > 1:
        ids = t.subtree(argv[1])
        print(f"  {argv[1]} 子树节点数：{len(ids)}")
        for i in ids[:40]:
            print(f"    {i}  {t.nodes[i]['name']}")
    else:
        print(__doc__)


if __name__ == "__main__":
    _main(sys.argv[1:])
