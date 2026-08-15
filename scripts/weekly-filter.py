# -*- coding: utf-8 -*-
"""周报看板数据筛选脚本：解析 kanban_tmp.json（===BOARD:<slug>=== 分隔的多 board JSON）
输出：各 board 状态分布 + textbook 看板卡片清单 + 总计。用法：python weekly-filter.py"""
import json, sys, io
from collections import Counter

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

path = r'C:\Users\DELL\textbook-project\kanban_tmp.json'
raw = open(path, encoding='utf-8').read()

# 按 board 头切分
parts = raw.split('===BOARD:')
boards = {}
for p in parts[1:]:
    slug, _, body = p.partition('\n')
    slug = slug.strip().rstrip('=').strip()
    try:
        data = json.loads(body.strip())
        boards[slug] = data if isinstance(data, list) else []
    except Exception as e:
        print(f'PARSE_ERR {slug}: {e}')
        boards[slug] = []

total_all = 0
print('=== 各看板状态分布 ===')
for slug in ['textbook', 'tcm-epic', 'tcm-domain-d01', 'tcm-domain-d02', 'tcm-domain-d03',
             'tcm-domain-d04', 'tcm-domain-d05', 'tcm-domain-d06', 'tcm-domain-d07',
             'tcm-domain-d08', 'network-service-engineering']:
    cards = boards.get(slug, [])
    c = Counter(x.get('status', '?') for x in cards)
    n = len(cards)
    total_all += n
    parts_s = ' '.join(f'{k}={v}' for k, v in sorted(c.items()))
    print(f'{slug}: total={n} | {parts_s}')

print(f'=== 总计卡片: {total_all} ===')

print()
print('=== textbook 看板卡片明细 ===')
for card in boards.get('textbook', []):
    print(f"{card.get('status','?'):10s} | {card.get('assignee') or 'unassigned':20s} | {card.get('title','')[:80]}")
