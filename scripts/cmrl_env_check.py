# -*- coding: utf-8 -*-
"""cmrl_env_check.py — 检查图表制作环境（matplotlib/中文字体/目录）"""
import importlib
import sys
from pathlib import Path

print('== Python ==', sys.version.split()[0])
for m in ('matplotlib', 'numpy', 'PIL'):
    try:
        mod = importlib.import_module(m)
        print(f'== {m} ==', getattr(mod, '__version__', 'ok'))
    except ImportError:
        print(f'== {m} == MISSING')

try:
    from matplotlib import font_manager
    fonts = {f.name for f in font_manager.fontManager.ttflist}
    zh = sorted(f for f in fonts if any(
        k in f for k in ('SimHei', 'SimSun', 'Microsoft YaHei', 'KaiTi',
                         'FangSong', 'Noto Sans CJK', 'DengXian')))
    print('== 中文字体 ==', zh[:10] or '未发现')
    print('== 默认字体 ==',
          font_manager.findfont(font_manager.FontProperties(family='sans-serif')))
except Exception as e:
    print('== font check ==', e)

# 图表输出目录规划
base = Path(r'C:\Users\DELL\textbook-project\drafts\cmrl')
for sub in ('figures',):
    d = base / sub
    d.mkdir(exist_ok=True)
    print('== 目录 ==', d, '已就绪')
