# -*- coding: utf-8 -*-
"""中医知识树 · 端到端自检（构建物 + 运行时 + API 路由）。
运行：python scripts/verify_knowledge_tree.py
"""
from __future__ import annotations
import sys
import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TREE_DIR = REPO / "kg" / "tree"
sys.path.insert(0, str(TREE_DIR))
sys.path.insert(0, str(REPO / "api"))

from tcm_tree import KnowledgeTree  # noqa: E402

fails = []


def check(name, cond, extra=""):
    print(("  ✓ " if cond else "  ✗ ") + name + (f"  [{extra}]" if extra else ""))
    if not cond:
        fails.append(name)


def main():
    print("═" * 62)
    print(" 中医知识树 · 端到端自检")
    print("═" * 62)
    raw = json.loads((TREE_DIR / "tcm-knowledge-tree.json").read_text(encoding="utf-8"))
    sch = json.loads((TREE_DIR / "schema.json").read_text(encoding="utf-8"))
    t = KnowledgeTree()

    print("\n[1] 结构完整性")
    check("schema 版本 1.0.0", sch.get("version") == "1.0.0")
    check("节点数 > 2500", t.stats["nodes"] > 2500, t.stats["nodes"])
    check("边数 > 2500", t.stats["edges"] > 2500, t.stats["edges"])
    check("8 域", t.stats["levels"]["trunk"] == 8)
    check("120 学科", t.stats["levels"]["branch"] == 120)
    check("六层刻度齐全(hair/root/trunk/branch/leaf/concept)",
          all(t.stats["levels"].get(k, 0) > 0 for k in
              ["hair", "root", "trunk", "branch", "leaf", "concept"]))
    check("章节覆盖 120/120", t.stats.get("chapter_coverage") == "120/120")
    check("id 无重复", len(raw["nodes"]) == len({n["id"] for n in raw["nodes"]}))

    print("\n[2] 树导航")
    n = t.node("D07-S04")
    check("D07-S04 存在且为 branch", n and n["level"] == "branch", n["name"] if n else "")
    p = [x["id"] for x in t.path("D07-S04")]
    check("D07-S04 祖先链 = D07 → D07-S04", p == ["D07", "D07-S04"], p)
    kids = t.children("D07")
    check("D07 有 14 学科枝", len(kids) == 14, len(kids))
    sub = t.subtree("D01")
    check("D01 子树 > 400 节点", len(sub) > 400, len(sub))

    print("\n[3] 图邻接")
    nb = {x["type"] for x in t.neighbors_full("DSU-00001")}
    check("DSU-00001 含 icd11_map 边", "icd11_map" in nb, sorted(nb))
    check("DSU-00001 含 manifests_as 边", "manifests_as" in nb)
    sheng = t.neighbors_full("W-木", "wuxing_sheng")
    check("W-木 相生自洽（出→火 入←水）",
          any(x["dir"] == "out" and x["id"] == "W-火" for x in sheng)
          and any(x["dir"] == "in" and x["id"] == "W-水" for x in sheng), len(sheng))
    ke = t.neighbors_full("W-木", "wuxing_ke")
    check("W-木 相克自洽（出→土 入←金）",
          any(x["dir"] == "out" and x["id"] == "W-土" for x in ke)
          and any(x["dir"] == "in" and x["id"] == "W-金" for x in ke), len(ke))
    sc = t.neighbors_full("SC-1", "six_chuanbian")
    check("太阳病→阳明病 传变边", sc and sc[0]["id"] == "SC-2")

    print("\n[4] 检索")
    hits = t.search("桂枝", limit=5)
    check("检索『桂枝』有结果", len(hits) > 0, len(hits))
    check("检索『知识图谱』命中 D07-S04",
          any(h["id"] == "D07-S04" for h in t.search("知识图谱")))

    print("\n[5] API 路由（函数级）")
    try:
        import tree_router as tr
        s = tr.tree_stats()
        check("GET /tree/stats ok", s["ok"] and s["stats"]["nodes"] == t.stats["nodes"])
        check("GET /tree/levels 返回 5 级", len(tr.tree_levels()["levels"]) == 5)
        check("GET /tree/node/D07-S04 ok", tr.tree_node("D07-S04")["node"]["name"] == "中医知识图谱")
        check("GET /tree/children/D07 ok", len(tr.tree_children("D07")["children"]) == 14)
        check("GET /tree/path/DSU-00001 ok（域→学科→单元）",
              [x["id"] for x in tr.tree_path("DSU-00001")["path"]] == ["D01", "D01-S13", "DSU-00001"])
        check("GET /tree/neighbors/DSU-00001 ok",
              len(tr.tree_neighbors("DSU-00001")["neighbors"]) >= 4)
        check("GET /tree/search?q=桂枝 ok", tr.tree_search(q="桂枝", limit=5)["count"] > 0)
    except Exception as e:  # noqa: BLE001
        check("API 路由可导入并调用", False, repr(e))

    print("\n" + "═" * 62)
    if fails:
        print(f" 自检失败 {len(fails)} 项： " + "、".join(fails))
        sys.exit(1)
    print(" 自检全部通过 ✓")
    print("═" * 62)


if __name__ == "__main__":
    main()
