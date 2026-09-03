# -*- coding: utf-8 -*-
"""更新进度 14/31 + 清理"""
import json

p = r'C:\Users\DELL\tcmP\scripts\progress\hjnj_writing_progress.json'
d = json.load(open(p, encoding='utf-8'))
d['done'] = 14
json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print(f"进度: {d['done']}/{d['total']}")
print(f"下一章: {d['chapters']['15'][:40]}")
print("备注: 已修复 sharedStrings 截断（重建工作簿）+ 表头 + 通读/补注/编码")
