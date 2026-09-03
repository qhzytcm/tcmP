# -*- coding: utf-8 -*-
"""HTML 调整: 字幕时间轴校准(提前2.5s) + 引导观看者→岐伯暗喻重点突出"""
import re
from pathlib import Path

D = Path(r'C:\Users\DELL\tcmP\docs\视频')
src = D / '素问01-上古天真论-视频课程.html'
t = src.read_text(encoding='utf-8')

# ① 字幕时间轴校准: 字幕提前 2.5s 显示（文字先于声音, 消除发声早于文字 2-5 秒）
old_ts = 'const tRef = frac * totalRef;'
new_ts = 'const tRef = Math.max(0, frac * totalRef - 2.5);  // 字幕提前2.5s(校准发声早于文字)'
assert old_ts in t, '时间轴锚点缺失'
t = t.replace(old_ts, new_ts)
print('① 字幕时间轴校准(提前2.5s): OK')

# ② CSS: 岐伯暗喻块样式
if '.muyu' not in t:
    t = t.replace(
        '  .footer { text-align: center; color: #999; font-size: 13px; padding: 20px; }',
        '  .footer { text-align: center; color: #999; font-size: 13px; padding: 20px; }\n'
        '  .muyu { display: block; background: #fdf6e3; border-left: 4px solid var(--gold);\n'
        '          padding: 10px 14px; margin-top: 10px; font-size: 15px; line-height: 1.9;\n'
        '          color: #7a5c00; font-weight: 700; text-align: left; }\n'
        '  .muyu .tag { color: var(--gold); font-size: 12.5px; display: block; margin-bottom: 4px; font-weight: 700; }')
print('② 暗喻块样式: OK')

# ③ 正文中"引导观看者…"整句 → 岐伯暗喻块（重点突出）
def wrap_muyu(match):
    sent = match.group(0).strip()
    return ('<div class="muyu"><span class="tag">岐伯暗喻 · 语言的语义群</span>'
            + sent + '</div>')

# 匹配 talk 中从"引导观看者"到句号(。)的句子（含嵌套 <b> 标签）
pat = re.compile(r'引导观看者[^。]*。')
n_hits = len(pat.findall(t))
t = pat.sub(wrap_muyu, t)
print(f'③ 岐伯暗喻高亮: {n_hits} 处')

src.write_text(t, encoding='utf-8')
print(f'源 HTML 已更新: {src.stat().st_size // 1024}KB')
