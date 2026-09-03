# -*- coding: utf-8 -*-
"""更新进度: 第16章重写完成（全文照抄版）"""
import json

p = r'C:\Users\DELL\tcmP\scripts\progress\hjnj_writing_progress.json'
d = json.load(open(p, encoding='utf-8'))
d['done'] = 17
json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print(f"进度: {d['done']}/{d['total']}")
print("第16章已按'全文照抄+悬疑注释'重写完成")
