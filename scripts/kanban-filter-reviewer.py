# -*- coding: utf-8 -*-
"""筛选 textbook 看板中 assignee=textbook-reviewer 且 status=ready 的任务"""
import json, sys, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# PowerShell 5.1 `>` 重定向输出 UTF-16，可能带 BOM；逐编码尝试
data = None
raw = open('kanban_tmp.json', 'rb').read()
for enc in ('utf-8-sig', 'utf-8', 'utf-16', 'utf-16-le'):
    try:
        data = json.loads(raw.decode(enc))
        break
    except (UnicodeDecodeError, json.JSONDecodeError):
        continue
if data is None:
    print('FATAL: cannot decode kanban_tmp.json')
    sys.exit(1)

# 兼容 list 返回 dict 包裹或直接 list
tasks = data if isinstance(data, list) else data.get('tasks', data.get('items', []))

ready_review = []
for t in tasks:
    status = (t.get('status') or '').lower()
    assignee = t.get('assignee') or ''
    # assignee 可能为字符串或 dict
    if isinstance(assignee, dict):
        assignee_name = assignee.get('name') or assignee.get('username') or ''
    else:
        assignee_name = str(assignee)
    if status == 'ready' and 'textbook-reviewer' in assignee_name.lower():
        ready_review.append(t)

print(f"TOTAL_TASKS={len(tasks)}")
print(f"READY_REVIEWER_COUNT={len(ready_review)}")
for t in ready_review:
    tid = t.get('id')
    title = t.get('title') or t.get('name') or ''
    body = (t.get('body') or '').strip()
    print('-' * 60)
    print(f"ID: {tid}")
    print(f"TITLE: {title}")
    print(f"BODY: {body[:600]}")
