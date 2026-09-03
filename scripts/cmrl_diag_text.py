# -*- coding: utf-8 -*-
"""诊断: 各图生成脚本中的文字标注数量与字号（量化图内文字密度）"""
import re
from pathlib import Path

F = Path(r'C:\Users\DELL\textbook-project\drafts\cmrl\figures')
scripts = sorted(F.glob('gen_ch*_figures*.py'))
print(f'{"脚本":<44}{"标注文本数":<10}{"最小字号":<8}{"fontsize出现"}')
print('-' * 80)
for p in scripts:
    t = p.read_text(encoding='utf-8', errors='ignore')
    # 中文标注文本（含中文的字符串字面量）
    labels = re.findall(r'["\']([^"\']*[\u4e00-\u9fff][^"\']*)["\']', t)
    # 过滤注释/docstring 近似: 只统计较短的中文文本（标注特征）
    real = [s for s in labels if 2 <= len(s) <= 40 and not s.startswith(('def ', 'import', '#', '"""'))]
    # 字号
    sizes = [int(x) for x in re.findall(r'fontsize[=:]\s*(\d+)', t)]
    min_size = min(sizes) if sizes else '-'
    n_fs = len(sizes)
    print(f'{p.name:<44}{len(real):<10}{str(min_size):<8}{n_fs}')
