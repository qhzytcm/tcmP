# -*- coding: utf-8 -*-
"""样式调整: 删注释 + 字幕3件套(原文-讲解-图表) + 字体统一左对齐 → 重建单文件版"""
import base64
import re
from pathlib import Path

D = Path(r'C:\Users\DELL\tcmP\docs\视频')
src = D / '素问01-上古天真论-视频课程.html'
out = D / '素问01-上古天真论-视频授课.html'
mp4 = D / '素问01-上古天真论.mp4'

t = src.read_text(encoding='utf-8')

# ① 删除注释行（.note 整行）—— 只读原文与讲解
t = re.sub(r'\n\s*<div class="note">.*?</div>', '', t, flags=re.S)
n_note = t.count('class="note"')
print(f'① 注释行删除: 剩余 note={n_note}（应为 0）')

# ② 字体统一 + 左对齐横排
t = t.replace(
    '.orig { font-size: 16px; line-height: 2.05; color: #2c3e50; text-align: justify;',
    '.orig { font-size: 17px; line-height: 1.9; color: #2c3e50; text-align: left;')
t = t.replace(
    '.talk { font-size: 15px; line-height: 2.0; color: #4a4a4a; text-align: justify; margin-top: 10px; }',
    '.talk { font-size: 16px; line-height: 1.9; color: #4a4a4a; text-align: left; margin-top: 10px; }')
t = t.replace(
    '.cap-orig { color: #fdf9ef; font-size: 16px; line-height: 1.8; }',
    '.cap-orig { color: #fdf9ef; font-size: 17px; line-height: 1.8; text-align: left; }')
t = t.replace(
    '.cap-talk { color: #9fc7ae; font-size: 14px; line-height: 1.7; margin-top: 4px; }',
    '.cap-talk { color: #9fc7ae; font-size: 15px; line-height: 1.7; margin-top: 4px; text-align: left; }')
# 图表框样式（统一字体左对齐）
if '.cap-chart' not in t:
    t = t.replace(
        '.cap-talk { color: #9fc7ae; font-size: 15px; line-height: 1.7; margin-top: 4px; text-align: left; }',
        '.cap-talk { color: #9fc7ae; font-size: 15px; line-height: 1.7; margin-top: 4px; text-align: left; }\n'
        '  .cap-chart { margin-top: 8px; border-top: 1px solid #1e3b2a; padding-top: 8px; }\n'
        '  .cap-chart img { max-height: 130px; border-radius: 6px; border: 1px solid #2c4a38; display: block; text-align: left; }\n'
        '  .cap-chart .lbl { color: #7ee2a8; font-size: 13px; margin-bottom: 4px; text-align: left; }')
print('② 字体统一+左对齐: OK')

# ③ 字幕区加图表位（3件套）
if 'capChart' not in t:
    t = t.replace(
        '<div class="cap-talk" id="capTalk">开篇立"人"：黄帝——生而神灵的圣人，向天师岐伯请教生命的根本问题。</div>',
        '<div class="cap-talk" id="capTalk">开篇立"人"：黄帝——生而神灵的圣人，向天师岐伯请教生命的根本问题。</div>\n'
        '      <div class="cap-chart" id="capChart"></div>')
print('③ 字幕区图表位: OK')

# ④ SUBS 数据加 chart 字段 + JS 渲染图表
old_subs_start = 'const SUBS = ['
i0 = t.index(old_subs_start)
i1 = t.index('];', i0)
new_subs = '''const SUBS = [
  { sec: '第 1 段 · 开篇', dur: 2, chart: null,
    orig: '昔在黄帝，生而神灵，弱而能言，幼而徇齐，长而敦敏，成而登天。',
    talk: '开篇立"人"：黄帝——生而神灵的圣人，向天师岐伯请教生命的根本问题。' },
  { sec: '第 2 段 · 发问', dur: 4, chart: null,
    orig: '余闻上古之人，春秋皆度百岁，而动作不衰；今时之人，年半百而动作皆衰者，时世异耶？人将失之耶？',
    talk: '今人半寿早衰何因？一问双问：时世之变（外因）？人自失道（内因）？岐伯只答内因。' },
  { sec: '第 3 段 · 总答', dur: 4, chart: null,
    orig: '上古之人，其知道者，法于阴阳，和于术数，食饮有节，起居有常，不妄作劳，故能形与神俱，而尽终其天年，度百岁乃去。',
    talk: '四个基本盘：法于阴阳 + 和于术数 + 食饮有节 + 起居有常（不妄作劳）。' },
  { sec: '第 4 段 · 论上古人与论今人', dur: 10, chart: 'tables/表3-男女对比.png',
    orig: '今时之人不然也，以酒为浆，以妄为常，醉以入房，以欲竭其精，以耗散其真……故半百而衰也。',
    talk: '精气神三维度对比：精（物质结构）守精vs竭精；气（能量信息）顺气vs乱气；神（储备潜能）全神vs耗神。' },
  { sec: '第 5 段 · 圣人教下', dur: 20, chart: null,
    orig: '虚邪贼风，避之有时，恬惔虚无，真气从之，精神内守，病安从来。',
    talk: '精气神=物质结构-能量信息-适应储备潜能最适化：恬惔虚无（神）+真气从之（气）+精神内守（精）。' },
  { sec: '第 6 段 · 德全不危', dur: 20, chart: null,
    orig: '志闲而少欲，心安而不惧，形劳而不倦……以其德全不危也。',
    talk: '深思远虑的生命战略：志闲少欲（神）+心安不惧（气）+形劳不倦（精）=德全不危。' },
  { sec: '第 7 段 · 女子七纪', dur: 20, chart: 'tables/表1-女子生命周期.png',
    orig: '女子七岁肾气盛……七七任脉虚，天癸竭，地道不通，故形坏而无子。',
    talk: '三线表一七→七七：观察-思考-行动多循环迭代式自主成长，逐阶段引导养护。' },
  { sec: '第 8 段 · 男子八纪', dur: 20, chart: 'tables/表2-男子生命周期.png',
    orig: '丈夫八岁肾气实……八八则齿发去。',
    talk: '三线表一八→八八：观察-思考-行动多循环迭代式自主成长，逐阶段引导养护。' },
  { sec: '第 9 段 · 贤人·圣人', dur: 120, chart: null,
    orig: '其次有贤人者，法则天地……亦可使益寿而有极时。其次有圣人者，处天地之和……亦可以百数。',
    talk: '认知递进第一阶：先讲贤人（跳跃式设计）→ 再讲圣人（随遇而安式设计）。' },
  { sec: '第 10 段 · 至人·真人', dur: 120, chart: null,
    orig: '中古之时，有至人者，淳德全道……亦归于真人。余闻上古有真人者，提挈天地，把握阴阳……此其道生。',
    talk: '认知递进终阶：先讲至人（适应式设计）→ 再讲真人（塔顶式设计）。四境界由低到高：贤人→圣人→至人→真人。' },
];'''
t = t[:i0] + new_subs + t[i1 + 2:]

# JS 渲染图表
old_render = """  if (cur) {
    capSec.textContent = '▍' + cur.sec;
    capOrig.textContent = cur.orig;
    capTalk.textContent = cur.talk;
  }"""
new_render = """  if (cur) {
    capSec.textContent = '▍' + cur.sec;
    capOrig.textContent = cur.orig;
    capTalk.textContent = cur.talk;
    // 图表 3 件套: 原文-讲解-图表
    const cc = document.getElementById('capChart');
    if (cur.chart) {
      cc.innerHTML = '<div class="lbl">📊 图表</div><img src="' + cur.chart + '" alt="图表">';
    } else {
      cc.innerHTML = '<div class="lbl">📊 图表</div><span style="color:#5a7d6a;font-size:13px;">（本段无图表）</span>';
    }
  }"""
assert old_render in t
t = t.replace(old_render, new_render)
print('④ 字幕3件套(原文-讲解-图表): OK')

# 源 HTML 保存
src.write_text(t, encoding='utf-8')
print(f'源 HTML 已更新: {src.name} ({src.stat().st_size // 1024}KB)')

# ⑤ 重建单文件版（视频内嵌）
b64 = base64.b64encode(mp4.read_bytes()).decode('ascii')
data_uri = f'data:video/mp4;base64,{b64}'
t2 = t.replace(
    '<source src="素问01-上古天真论.mp4" type="video/mp4">',
    f'<source src="{data_uri}" type="video/mp4">\n'
    '      <source src="素问01-上古天真论.mp4" type="video/mp4">')
out.write_text(t2, encoding='utf-8')
print(f'✅ 单文件版重建: {out.name} ({out.stat().st_size // (1024*1024)}MB)')
