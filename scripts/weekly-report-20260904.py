#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""2026-09-04 周报统计：目录计数 + 本周(8/28后)变更明细 + textbook看板状态。"""
import json, sys
from pathlib import Path
from collections import Counter

BASE = Path.home() / "textbook-project"
CUTOFF = "2026-08-28"  # 与上周周报（20260828）对比的变更窗口起点

def count_md(d):
    p = BASE / d
    return sum(1 for f in p.rglob("*.md") if f.is_file()) if p.exists() else 0

def count_all(d):
    p = BASE / d
    return sum(1 for f in p.rglob("*") if f.is_file()) if p.exists() else 0

print("=== 目录文件计数（截至 2026-09-04） ===")
for sub in ["drafts", "drafts/cmrl", "drafts/cmrl/figures/book/video", "drafts/D01-S01",
            "reviews", "feedback", "archive", "domain-specs", "kg-schema/samples",
            "ai-curriculum", "scripts", "dashboard"]:
    print(f"{sub}: md={count_md(sub)} all={count_all(sub)}")

# 本周（>8/28）变更文件：按 顶层/二级 目录聚合
print("\n=== 2026-08-28 后变更文件（按目录，仅列 >=2 与重点目录） ===")
changed = {}
for root in ["drafts", "feedback", "reviews", "archive", "scripts", "ai-curriculum", "domain-specs"]:
    d = BASE / root
    if not d.exists():
        continue
    for f in d.rglob("*"):
        if f.is_file():
            try:
                import datetime
                mtime = datetime.datetime.fromtimestamp(f.stat().st_mtime)
                if mtime >= datetime.datetime(2026, 8, 28):
                    rel = f.relative_to(BASE).as_posix()
                    parts = rel.split("/")
                    key = "/".join(parts[:3]) if len(parts) > 3 else "/".join(parts[:2])
                    changed.setdefault(key, []).append(rel)
            except OSError:
                pass
for k in sorted(changed, key=lambda x: -len(changed[x])):
    marker = "  ⭐" if len(changed[k]) >= 100 else ""
    print(f"{len(changed[k]):>5}  {k}{marker}")
print(f"\n本周变更文件总数: {sum(len(v) for v in changed.values())}")

# 视频顶层 mp4 数量（素问成片清单）
video_top = BASE / "drafts/cmrl/figures/book/video"
mp4s = sorted(p.name for p in video_top.glob("*.mp4")) if video_top.exists() else []
print(f"\n=== 视频成片（video/ 顶层 *.mp4）: {len(mp4s)} 个 ===")
for m in mp4s:
    print("  ", m)

# suwen* 子目录计数
subs = sorted(p.name for p in video_top.glob("suwen*")) if video_top.exists() else []
print(f"suwen* 素材子目录: {len(subs)} 个")

print("\n=== textbook 看板状态 ===")
def load_json(path):
    raw = Path(path).read_bytes()
    for enc in ("utf-8-sig", "utf-16", "utf-8"):
        try:
            return json.loads(raw.decode(enc))
        except (UnicodeDecodeError, json.JSONDecodeError):
            continue
    raise ValueError(f"无法解析: {path}")

kb = load_json(BASE / "kanban_tmp.json")
tasks = kb if isinstance(kb, list) else kb.get("tasks", kb.get("cards", []))
sc = Counter(t.get("status", "?") for t in tasks)
print(f"textbook 卡片总数: {len(tasks)}  状态分布: {dict(sc)}")
print("\n卡片明细:")
for t in sorted(tasks, key=lambda x: x.get("status", "")):
    print(f"  [{t.get('status'):>8}] {t.get('id')} :: {t.get('title','?')}")
