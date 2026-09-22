# -*- coding: utf-8 -*-
"""筛选 assignee=textbook-reviewer 且 status=ready 的任务（cron 待评阅巡检）。"""
import json
import sys
from pathlib import Path

RAW = Path("kanban_tmp.json")

def load_tasks():
    data = json.loads(RAW.read_text(encoding="utf-8-sig"))
    # 兼容两种形态：list 直接是任务数组；dict 含 tasks 键
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("tasks", "items", "cards", "results", "data"):
            if isinstance(data.get(key), list):
                return data[key]
    return []

def main():
    tasks = load_tasks()
    print(f"TOTAL_TASKS={len(tasks)}")
    hits = []
    for t in tasks:
        if not isinstance(t, dict):
            continue
        assignee = str(t.get("assignee") or t.get("assignee_id") or t.get("assignees") or "")
        status = str(t.get("status") or "")
        # assignee 可能是数组/对象
        if isinstance(assignee, (list, tuple)):
            assignee = ",".join(str(a) for a in assignee)
        if "textbook-reviewer" in assignee and status.strip().lower() == "ready":
            hits.append(t)
    print(f"READY_REVIEW_TASKS={len(hits)}")
    if not hits:
        print("NO_PENDING_REVIEW")
        return
    print("=" * 70)
    for i, t in enumerate(hits, 1):
        tid = t.get("id") or t.get("task_id") or "?"
        title = t.get("title") or t.get("name") or "(untitled)"
        body = (t.get("body") or t.get("description") or "").strip()
        prio = t.get("priority", "?")
        tenant = t.get("tenant", "")
        print(f"[{i}] ID={tid} | PRI={prio} | TENANT={tenant}")
        print(f"    TITLE: {title}")
        if body:
            # 截取 body 前 600 字符做简介
            brief = body.replace("\r", "").replace("\n", " / ")[:600]
            print(f"    BODY : {brief}")
        print("-" * 70)

if __name__ == "__main__":
    main()
