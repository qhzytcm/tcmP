# -*- coding: utf-8 -*-
"""cron 待评阅任务筛选：读取 kanban_tmp.json，筛选 assignee=textbook-reviewer 且 status=ready 的任务"""
import json
import sys
from pathlib import Path

def main():
    raw_bytes = Path("kanban_tmp.json").read_bytes()
    # PowerShell `>` 重定向产生 UTF-16LE (BOM ff fe)；write_file 为 UTF-8。按 BOM 自动检测。
    if raw_bytes.startswith(b"\xff\xfe") or raw_bytes.startswith(b"\xfe\xff"):
        text = raw_bytes.decode("utf-16")
    else:
        text = raw_bytes.decode("utf-8-sig")
    data = json.loads(text)

    # 兼容两种结构：列表 或 {tasks: [...]}
    tasks = data if isinstance(data, list) else data.get("tasks", data.get("cards", []))

    ready_review = []
    for t in tasks:
        assignee = str(t.get("assignee", "") or "")
        status = str(t.get("status", "") or "")
        if assignee.strip().lower() == "textbook-reviewer" and status.strip().lower() == "ready":
            ready_review.append(t)

    print(f"TOTAL_TASKS={len(tasks)}")
    print(f"READY_REVIEWER_TASKS={len(ready_review)}")
    if ready_review:
        print("---LIST---")
        for t in ready_review:
            title = t.get("title") or t.get("name") or "(无标题)"
            body = (t.get("body") or "").strip().replace("\n", " ")
            print(f"[{t.get('id','?')}] {title} | body: {body[:200]}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
