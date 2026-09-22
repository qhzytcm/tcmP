#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""周报数据筛选脚本：统计 drafts/reviews/feedback 文件数 + Kanban 看板状态。

cron 复用姿势（每周五周报）：
  1. cd ~/textbook-project
  2. hermes kanban boards switch textbook
  3. hermes kanban list --json > kanban_tmp.json
  4. python scripts/weekly-report-filter.py [kanban_json路径，可选]
  5. 运行后删除 kanban_tmp.json
"""
import json, sys
from pathlib import Path

BASE = Path.home() / "textbook-project"
# 可选参数：kanban JSON 路径（默认 ~/textbook-project/kanban_tmp.json）
KANBAN_JSON = Path(sys.argv[1]) if len(sys.argv) > 1 else BASE / "kanban_tmp.json"

# 与上周报告的对比基线 —— 每次生成周报后更新为最新数字
# 截至 2026-09-04 周报：textbook 看板 done=24, blocked=2, ready=14（40 卡）
# 截至 2026-09-11 周报：textbook 板已于 9/8 16:59 归档重建（当前 0 卡）；
#   归档板 hermes-home/kanban/boards/_archived/textbook-1788857952/kanban.db 终态 = 65 done + 2 archived（67 卡）
BASELINE = {"done": 65, "blocked": 0, "ready": 0, "archived": 2}

def count_md_files(subdir):
    """统计某目录下所有 .md 文件（递归）。"""
    d = BASE / subdir
    if not d.exists():
        return 0
    return sum(1 for p in d.rglob("*") if p.is_file() and p.suffix.lower() == ".md")

def count_all_files(subdir):
    d = BASE / subdir
    if not d.exists():
        return 0
    return sum(1 for p in d.rglob("*") if p.is_file())

print("=== 文件统计 ===")
for sub in ["drafts", "reviews", "reviews/L2-reviews", "reviews/L3-reviews", "feedback", "archive", "assets", "kg-schema/samples", "domain-specs", "scripts", "dashboard"]:
    print(f"{sub}: md={count_md_files(sub)} all={count_all_files(sub)}")

# drafts 明细
d = BASE / "drafts"
md_files = sorted(p.relative_to(BASE).as_posix() for p in d.rglob("*.md")) if d.exists() else []
print(f"\ndrafts/*.md 总数: {len(md_files)}")
for f in md_files:
    print("  ", f)

print("\n=== Kanban 看板状态 ===")
def load_json(path):
    """编码鲁棒读取：兼容 UTF-8 / UTF-8-BOM / PowerShell 重定向的 UTF-16。"""
    raw = Path(path).read_bytes()
    for enc in ("utf-8-sig", "utf-16", "utf-8"):
        try:
            return json.loads(raw.decode(enc))
        except (UnicodeDecodeError, json.JSONDecodeError):
            continue
    raise ValueError(f"无法解析 kanban JSON: {path}")
kb = load_json(KANBAN_JSON)
# 兼容不同结构：可能是 list 或 {tasks: [...]}
tasks = kb if isinstance(kb, list) else kb.get("tasks", kb.get("cards", []))
print(f"看板 'textbook' 卡片总数: {len(tasks)}")
from collections import Counter
status_counter = Counter(t.get("status", "?") for t in tasks)
print("状态分布:", dict(status_counter))

# 每张卡片详情
print("\n卡片明细:")
for t in tasks:
    title = t.get("title", t.get("name", "?"))
    status = t.get("status", "?")
    assignee = t.get("assignee", t.get("assignees", "-"))
    prio = t.get("priority", "-")
    tid = t.get("id", t.get("task_id", "?"))
    print(f"  [{status}] {tid} prio={prio} assignee={assignee} :: {title}")

# 与上周报告基线对比（BASELINE 常量见文件头部）
print("\n=== 与上周报告基线对比 ===")
print("textbook 看板: 基线(上周)", BASELINE, "本周", dict(status_counter))
