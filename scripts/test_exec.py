# -*- coding: utf-8 -*-
"""测试 exec 提取 ch06 rows 中 6.2.1.7"""
import importlib.util

with open(r'C:\Users\DELL\tcmP\scripts\gen_hjnj_ch06.py', encoding='utf-8') as f:
    src = f.read()
src = src.replace('wb.save(DST)', 'pass  # 拦截')
ns = {}
exec(compile(src, '<gen>', 'exec'), ns)
rows = ns['rows']
print(f"rows: {len(rows)} 行")
for cat, code, text in rows:
    if code == '6.2.1.7':
        print(f"6.2.1.7: len={len(text)}")
        print(f"  {text}")
        break
