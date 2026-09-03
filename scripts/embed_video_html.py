# -*- coding: utf-8 -*-
"""生成自包含单文件 HTML 视频授课（视频 base64 内嵌, 双击即用, 单文件分享）
输出: docs/视频/素问01-上古天真论-视频授课.html (约 23MB)
"""
import base64
from pathlib import Path

D = Path(r'C:\Users\DELL\tcmP\docs\视频')
html_src = D / '素问01-上古天真论-视频课程.html'
mp4 = D / '素问01-上古天真论.mp4'
out = D / '素问01-上古天真论-视频授课.html'

t = html_src.read_text(encoding='utf-8')
print(f'源 HTML: {html_src.stat().st_size // 1024}KB')

# 视频 base64
b64 = base64.b64encode(mp4.read_bytes()).decode('ascii')
print(f'视频 base64: {len(b64) // (1024 * 1024)}MB')

# 替换 <source> 为 data URI（保留 mp4 引用作降级）
data_uri = f'data:video/mp4;base64,{b64}'
t_new = t.replace(
    '<source src="素问01-上古天真论.mp4" type="video/mp4">',
    f'<source src="{data_uri}" type="video/mp4">\n'
    '      <source src="素问01-上古天真论.mp4" type="video/mp4">'
)

# 顶部加单文件说明
note = ('<div style="max-width:1100px;margin:10px auto 0;padding:0 20px;font-size:13px;color:#7f8c8d;">'
        '📦 自包含单文件版：视频已内嵌，双击即用，可单文件分享（无需同目录视频文件）。</div>')
t_new = t_new.replace('<div class="container">', note + '\n<div class="container">')

out.write_text(t_new, encoding='utf-8')
print(f'✅ 单文件 HTML: {out.name} ({out.stat().st_size // (1024 * 1024)}MB)')
