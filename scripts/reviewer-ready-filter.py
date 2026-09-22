# -*- coding: utf-8 -*-
"""Cron 巡检脚本：筛选 textbook 看板中 assignee=textbook-reviewer 且 status=ready 的任务"""
import json
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# PowerShell `>` 重定向输出为 UTF-16LE（带 BOM），自动探测编码
with open('kanban_tmp.json', 'rb') as f:
    raw = f.read()
if raw.startswith(b'\xff\xfe') or raw.startswith(b'\xfe\xff'):
    text = raw.decode('utf-16')
else:
    text = raw.decode('utf-8')
tasks = json.loads(text)

reviewer_tasks = []
for t in tasks:
    assignee = t.get('assignee') or ''
    status = t.get('status') or ''
    if assignee == 'textbook-reviewer' and status == 'ready':
        reviewer_tasks.append(t)

print(f"TOTAL_TASKS={len(tasks)}")
print(f"REVIEWER_READY_TASKS={len(reviewer_tasks)}")
print("=" * 60)
if reviewer_tasks:
    for t in reviewer_tasks:
        print(f"ID: {t.get('id')}")
        print(f"TITLE: {t.get('title')}")
        print(f"STATUS: {t.get('status')} | ASSIGNEE: {t.get('assignee')}")
        body = (t.get('body') or '').replace('\n', ' | ')
        print(f"BODY: {body[:300]}")
        print("-" * 60)
else:
    # 顺便打印所有状态分布，便于诊断
    from collections import Counter
    status_dist = Counter(t.get('status') for t in tasks)
    assignee_dist = Counter(t.get('assignee') for t in tasks)
    print("STATUS_DIST:", dict(status_dist))
    print("ASSIGNEE_DIST:", dict(assignee_dist))
