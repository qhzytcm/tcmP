# -*- coding: utf-8 -*-
"""筛选 Kanban 看板 textbook 中 assignee=textbook-reviewer 且 status=ready 的任务"""
import json, sys, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

with open('kanban_tmp.json', 'rb') as f:
    raw = f.read()
# PowerShell 5.1 `>` 重定向输出 UTF-16 LE；utf-8-sig 兼容带 BOM 的 UTF-8
for enc in ('utf-8-sig', 'utf-16', 'gbk', 'latin-1'):
    try:
        text = raw.decode(enc)
        data = json.loads(text)
        break
    except (UnicodeDecodeError, json.JSONDecodeError):
        continue
else:
    raise SystemExit('无法解码 kanban_tmp.json')

# 兼容两种结构：list 或 {tasks: [...]}
tasks = data if isinstance(data, list) else data.get('tasks', data.get('cards', []))

ready_review = []
for t in tasks:
    assignee = t.get('assignee') or ''
    status = t.get('status') or ''
    if assignee == 'textbook-reviewer' and status == 'ready':
        ready_review.append(t)

print("=" * 70)
print(f"待评阅任务数 (assignee=textbook-reviewer, status=ready): {len(ready_review)}")
print("=" * 70)
for t in ready_review:
    tid = t.get('id', '?')
    title = t.get('title', t.get('name', '?'))
    body = (t.get('body') or '').replace('\r', '')
    print(f"\n[{tid}] {title}")
    if body.strip():
        # 打印 body 前 400 字符
        print("  内容摘要:", body.strip()[:400].replace('\n', ' | '))
