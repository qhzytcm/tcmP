# -*- coding: utf-8 -*-
"""第6章图注四要素版同步（一次性）：
1) Excel 6cmrl-approximation sheet 图注行文本 + 行高（保持左顶格格式）
2) 正文 md 图注行同步（4 个文件，纯 LF 行尾保持）
"""
import math
import re
from pathlib import Path
from openpyxl import load_workbook

XLSX = r'C:\Users\DELL\Desktop\强化学习的数学原理-赵世钰.xlsx'
CH06 = Path(r'C:\Users\DELL\textbook-project\drafts\cmrl\ch06')

# ---- 四要素版图注（a.对接正文提示语 b.线的注释 c.符号的注释 d.代表含义的指针图段） ----
CAPTIONS = {
    'fig6-1': (
        '图注：a.对接正文 6.1.1：TD 的学习节奏是"走一步看一步"——每与患者交互一步，'
        '立即用一步真实反馈修正判断，不必等回合结束；本图把这条节奏拆成"老账/新账"'
        '临床比喻与 TD 更新链条两部分。b.线的注释：蓝色实线箭头"复诊看一步"从老账 '
        'v(St) 指向新账 Rt+1+γv(St+1)，竖直黑色箭头表示"相减得差"；右半幅三框链'
        '（旧估计 → TD目标 → TD误差）以横向实线箭头传递，绿色弧线箭头表示由 δt 符号'
        '自动给出的修正方向。c.符号的注释：v(St) 为当前证候的旧估计（老账）；'
        'Rt+1+γv(St+1) 为 TD 目标（新账，一步真实奖励加后继预判）；'
        'δt = v(St) − (Rt+1+γv(St+1)) 为 TD 误差（TD error）；α 为学习率；三要素英文'
        '对照——TD目标（TD target）、TD误差（TD error）、自举（bootstrapping）。'
        'd.代表含义的指针图段：绿色弧线从 TD 误差框指向新估计框 v(St) ← v(St) + α·δt，'
        '并标注"δt 符号自动给出修正方向 ↑/↓"——误差的正负号自动决定上调还是下调，'
        '这正是"用新账修订老账"的自举闭环，也是 TD 区别于统计估计法"等回合结束再修正"'
        '的核心节奏。'
    ),
    'fig6-2': (
        '图注：a.对接正文 6.2.2 例 6.1：四状态链 s1→s2→s3→s4 的 TD(0) 收敛过程'
        '（γ=0.9，α=0.1，初始全 0），横轴聚焦"收敛段"前 15 回合——奖励信息逐格回传、'
        '价值从 0 快速爬升的关键区段（60 回合模拟的其余部分趋势一致、渐趋平缓）。'
        'b.线的注释：四条实线为 v(s1)~v(s4) 的价值估计曲线，从 0 出发按离奖励源'
        '由近及远的顺序依次爬升；同色水平虚线为真实价值 v(s1)=0.729、v(s2)=0.81、'
        'v(s3)=0.9、v(s4)=1。c.符号的注释：圆点为关键手算结果——回合 1 后 v(s4)=0.1；'
        '回合 2 后 v(s3)=0.009、v(s4)=0.19；回合 3 后 v(s2)=0.00081、v(s3)=0.0252'
        '（TD 目标=0.9×0.19=0.171）、v(s4)=0.271；15 回合后各状态约为 0.041、0.149、'
        '0.406、0.794。d.代表含义的指针图段：两条橙色弧线从回合 1 的 v(s4)=0.1 指向'
        '回合 2 的 v(s3)=0.009、再从回合 2 指向回合 3 的 v(s2)=0.00081——奖励信息'
        '沿轨迹反向逐格传播（每回合最多一格），离奖励源越近收敛越快，这正是自举'
        '传播速度的直观形态。'
    ),
    'fig6-3': (
        '图注：a.对接正文 6.5.3 例 6.4 数据 4：s1 选"右"到 s2（奖励 0），Q 学习法'
        '用后继状态的最大价值作目标更新 q(s1,右)（γ=1，α=0.1）。b.线的注释：绿色'
        '实线箭头为 Q 学习法的 max 更新路径——从 max 源 q(s2,右)=0.1 直达更新格 '
        'q(s1,右)=0.01；灰色虚线为 Sarsa 的实际路径——行为策略在 s2 实际选"左"'
        '（q(s2,左)=0），若用 Sarsa 则 q(s1,右) 保持不变；中区两条更新式并排，仅后继项'
        '不同。c.符号的注释：Q 表行=状态（s1、s2），列=动作（左、右）；绿色粗框格 '
        'q(s1,右)=0.01 为本次更新条目，绿色底格 q(s2,右)=0.1 为 max 源'
        '（target=max{0, 0.1}=0.1）；Q 学习法后继项为 max_a′ q(St+1,a′)，Sarsa '
        '后继项为 q(St+1,At+1)。d.代表含义的指针图段：Q 表第 3 列间隙内的绿色向上'
        '箭头从 max 源格指向更新格——更新目标取的是"最优动作"的价值而非行为策略'
        '实际选择的动作，即"目标与行为分离"，这是异策略（off-policy）的本质：学的是'
        '最优做法的价值，而不是当前做法的价值。'
    ),
    'fig6-4': (
        '图注：a.对接正文 6.7.2：在线学习的自适应闭环——每一次对话都是一步经验，'
        '系统在循环中持续自我修正，没有"学成毕业"的终点。b.线的注释：顺时针四条'
        '彩色实线箭头依次连接 ①对话 → ②日志 → ③更新 → ④服务 → 回到①，构成无终点'
        '的进化回路。c.符号的注释：① 对话——患者与医者 Agent 交互，产生"症状—辨证'
        '—反馈"一步经验；② 日志——状态、动作、奖励、误差写入进化记录，每一步都有账'
        '可查；③ 更新——TD 增量更新 v ← v + α(目标 − 旧值)，无需等待批量积累；'
        '④ 服务——价值表刷新，改进后的辨证与推荐反哺临床；中央圆为"在线进化"'
        '（走一步看一步、边走边修正）；底部横带为四条实现路径（增量更新、探索-利用'
        '平衡、基线校准、反馈校准）。d.代表含义的指针图段：环绕箭头与中央圆共同构成'
        '闭环——箭头每转一圈回到起点时价值表已被刷新，故"更好的服务 → 更好的对话'
        ' → 更好的数据"，系统自适应就在这一圈一圈的循环中完成。'
    ),
}

# ---- 1) Excel 图注行更新（左顶格格式保持） ----
wb = load_workbook(XLSX)
ws = wb['6cmrl-approximation']
note_rows = [r for r in range(1, ws.max_row + 1)
             if str(ws.cell(r, 3).value or '').startswith('图注：')]
assert len(note_rows) == 4, note_rows
print('Excel 图注行:', note_rows)

# 行高估算：C 列宽 115，黑体 10pt 汉字约 60 字/行，行高 13.5/行 + 余量
for r, key in zip(sorted(note_rows), ['fig6-1', 'fig6-2', 'fig6-3', 'fig6-4']):
    text = CAPTIONS[key]
    n_chars = len(re.sub(r'\s', '', text))
    lines = max(2, math.ceil(n_chars / 55))
    ws.cell(r, 3).value = text
    ws.row_dimensions[r].height = (lines + 1) * 13.5
    # 保持左顶格格式（alignment 不覆盖：只改值不改样式）
    al = ws.cell(r, 3).alignment
    print('  R%d %s | 字数 %d → 行高 %.1f | align h=%s v=%s wrap=%s'
          % (r, key, n_chars, ws.row_dimensions[r].height,
             al.horizontal, al.vertical, al.wrap_text))
wb.save(XLSX)
print('[Excel] 图注行已更新并保存')

# ---- 2) 正文 md 图注行同步（纯 LF 保持） ----
MD_MAP = {
    '01-1.1.md': 'fig6-1',
    '02-1.2.md': 'fig6-2',
    '05-1.5.md': 'fig6-3',
    '07-1.7.md': 'fig6-4',
}
for fname, key in MD_MAP.items():
    p = CH06 / fname
    lines = p.read_text(encoding='utf-8').split('\n')
    hit = 0
    for i, ln in enumerate(lines):
        if ln.startswith('图注：'):
            lines[i] = CAPTIONS[key]
            hit += 1
    assert hit == 1, (fname, hit)
    p.write_text('\n'.join(lines), encoding='utf-8')
    print('[md] %s 图注行已同步（%d 处）' % (fname, hit))
print('ALL DONE')
