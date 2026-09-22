# -*- coding: utf-8 -*-
"""cron 待评阅核验：看板 textbook 全量任务的状态×assignee 分布，确认无漏筛"""
import json
from collections import Counter
from pathlib import Path

def main():
    raw_bytes = Path("kanban_tmp.json").read_bytes()
    if raw_bytes.startswith(b"\xff\xfe") or raw_bytes.startswith(b"\xfe\xff"):
        text = raw_bytes.decode("utf-16")
    else:
        text = raw_bytes.decode("utf-8-sig")
    data = json.loads(text)
    tasks = data if isinstance(data, list) else data.get("tasks", data.get("cards", []))

    print("=== 状态分布 ===")
    for k, v in Counter(t.get("status", "?") for t in tasks).most_common():
        print(f"  {k}: {v}")

    print("=== assignee 分布 ===")
    for k, v in Counter(t.get("assignee", "?") for t in tasks).most_common():
        print(f"  {k}: {v}")

    print("=== assignee=textbook-reviewer 的全部任务 ===")
    rev = [t for t in tasks if str(t.get("assignee", "") or "").strip().lower() == "textbook-reviewer"]
    if not rev:
        print("  (无)")
    for t in rev:
        print(f"  [{t.get('status','?')}] {t.get('title','?')} id={t.get('id','?')}")

    # 全量 ready 任务（无论 assignee），确认 ready 是否根本不存在
    print("=== 全部 ready 任务 ===")
    rd = [t for t in tasks if str(t.get("status", "") or "").strip().lower() == "ready"]
    if not rd:
        print("  (无 ready 任务)")
    for t in rd:
        print(f"  [assignee={t.get('assignee','?')}] {t.get('title','?')} id={t.get('id','?')}")

if __name__ == "__main__":
    main()
