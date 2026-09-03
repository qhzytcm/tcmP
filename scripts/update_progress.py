# -*- coding: utf-8 -*-
"""更新编写进度: 标记第1章完成"""
import json

p = r'C:\Users\DELL\tcmP\scripts\progress\hjnj_writing_progress.json'
d = json.load(open(p, encoding='utf-8'))
d['done'] = 1
json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print(f"进度: {d['done']}/{d['total']} 章完成")
print(f"下一章: 第2章 {d['chapters']['2'][:30]}")
