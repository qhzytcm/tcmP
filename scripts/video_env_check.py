# -*- coding: utf-8 -*-
"""视频工具链环境自检: 核心依赖可用性 + ffmpeg/TTS 探活"""
import importlib
import shutil
import subprocess
import sys
from pathlib import Path

CORE = ['pandas', 'openpyxl', 'matplotlib', 'PIL', 'numpy', 'jieba',
        'openai', 'pysrt', 'pptx', 'moviepy', 'graphviz']
OPTIONAL = ['edge_tts', 'modelscope', 'manim', 'torch']

print('=== 核心依赖 ===')
ok_core = 0
for m in CORE:
    try:
        mod = importlib.import_module(m)
        ver = getattr(mod, '__version__', '?')
        print(f'  [OK] {m} {ver}')
        ok_core += 1
    except ImportError:
        print(f'  [MISS] {m}')

print('=== 可选依赖 ===')
for m in OPTIONAL:
    try:
        importlib.import_module(m)
        print(f'  [OK] {m}')
    except ImportError:
        print(f'  [MISS] {m}')

print('=== 系统级 ===')
ff = shutil.which('ffmpeg')
if not ff and Path(r'C:\Tools\ffmpeg.exe').exists():
    ff = r'C:\Tools\ffmpeg.exe'
print(f'  ffmpeg: {ff or "MISS（需安装）"}')
if ff:
    r = subprocess.run([ff, '-version'], capture_output=True, text=True)
    print(f'  {r.stdout.splitlines()[0][:60]}')

print(f'\n=== 核心依赖 {ok_core}/{len(CORE)} 可用 ===')
sys.exit(0 if ok_core >= len(CORE) - 1 else 1)
