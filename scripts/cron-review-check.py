# -*- coding: utf-8 -*-
"""Cron 巡检:筛选 assignee=textbook-reviewer 且 status=ready 的任务"""
import json
import sys

def load(path):
    raw = open(path, 'rb').read()
    # 兼容 utf-8-sig (BOM) 与 utf-16 (PS 重定向)
    for enc in ('utf-8-sig', 'utf-16', 'utf-8'):
        try:
            return json.loads(raw.decode(enc))
        except (UnicodeDecodeError, json.JSONDecodeError):
            continue
    raise SystemExit('FAIL: cannot decode JSON')

def main():
    data = load('kanban_tmp.json')
    tasks = data if isinstance(data, list) else data.get('tasks', data.get('items', []))
    # 展平:可能嵌套在 data['tasks'] 或直接是列表
    if isinstance(tasks, dict):
        tasks = list(tasks.values())
    print('total_tasks:', len(tasks))

    pending = []
    for t in tasks:
        assignee = str(t.get('assignee') or t.get('assigned_to') or '').lower()
        status = str(t.get('status') or '').lower()
        if assignee == 'textbook-reviewer' and status == 'ready':
            pending.append(t)

    print('pending_review_count:', len(pending))
    print('----')
    for t in pending:
        title = t.get('title') or t.get('name') or '(untitled)'
        body = (t.get('body') or t.get('description') or '').strip()
        tid = t.get('id') or t.get('task_id') or '(noid)'
        # 只取 body 前 300 字符
        body_snippet = body[:300].replace('\n', ' | ')
        print(f'ID: {tid}')
        print(f'TITLE: {title}')
        print(f'BODY: {body_snippet}')
        print('----')

if __name__ == '__main__':
    main()
