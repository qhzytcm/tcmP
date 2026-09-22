# -*- coding: utf-8 -*-
"""《中医场景强化学习》第2章 核心图生成脚本（v3 费曼图标准重构版，图表工程师 2026-08-18）

费曼图重构标准落地（7 条，与第1章一致）：
  ① 节点（方块/圆）+ 连线（实线/虚线/点线/箭头）为主体结构；
  ② 黑白灰线稿为主（v4 颜色对齐批次：第2章图注无颜色词 → 全图黑白灰，
     原灰红点缀（0.1 直入 s3 箭头、t=0 投入标注）改回黑白灰；
  ③ 极简：去圆角/渐变/阴影/背景网格/大面积色块；
  ④ 方向明确：诊疗循环、时间轴、转移方向一律箭头；
  ⑤ 信息密度高：概率/奖励/价值直接标注在节点与线上；
  ⑥ 聚焦图段延续：继承 v2 的 xlim/ylim 聚焦坐标；
  ⑦ 中医场景语义保留：证候=状态、方剂=动作、疗效=奖励、传变=转移、治未病=长期回报。

数值约定（与正文 2.2–2.6 节一致，不得另造）：
  转移概率 0.7/0.2/0.1（2.2.2、2.3.2）；γ=0.5 → G=2，γ=0.9 → G=10（2.4.2）
  G1=9（未病先防）> G3=8.5（时防时忽）> G2=8（病后才治），差值 0.5（2.4.2）
  四状态 v=(9,10,10,10)，s4 吸收态自环 +1，γ=0.9（2.6.2）

生成：fig2-1 / fig2-2 / fig2-3 / fig2-4（覆盖 figures/ch02/*.png，SimHei + unicode_minus=False + dpi=200；
v4 批次：图注无颜色词 → 全图黑白灰，彩色像素占比 0%）
"""
import os
import math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, Arc, Patch
from matplotlib.lines import Line2D

plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ch02')
os.makedirs(OUT, exist_ok=True)

# ---- 费曼色板 ----
K   = '#111111'
DK  = '#333333'
MG  = '#666666'
LG  = '#999999'
B   = '#5b7d9e'   # 点缀1 灰蓝：正向/关键/路径
R   = '#a35555'   # 点缀2 灰红：警示/负值
G0  = '#efefef'
G1  = '#f4f4f4'
G2  = '#e2e2e2'
G3  = '#cfcfcf'


# ---------------------------------------------------------------- 图 2-1
def fig2_1():
    """图 2-1 健康演化决策过程模型：五元组环图与诊疗循环（费曼版）
    节点 = 中心"诊疗循环"圆（白底黑粗边）+ 五元组 S/A/P/R/γ 方块（白/浅灰底黑边）
          + 底部轨迹链 s1→s2→s3 方块；
    连线 = 黑色实线环向箭头（S→A→P→γ→R→S）+ 底部轨迹推进箭头；
    方向 = 环向箭头顺时针，轨迹链从左到右。
    """
    fig, ax = plt.subplots(figsize=(9.6, 5.9))
    ax.set_xlim(-0.4, 12.4)
    ax.set_ylim(0, 7.0)
    ax.axis('off')
    # 中心：诊疗循环（圆圈节点）
    hub = Circle((6.3, 4.55), 1.28, facecolor='white', edgecolor=K, lw=2.0, zorder=2)
    ax.add_patch(hub)
    ax.text(6.3, 4.95, '诊疗循环', ha='center', fontsize=10.5, fontweight='bold',
            color=K, zorder=3)
    ax.text(6.3, 4.55, '观察—决策—反馈—再观察', ha='center', fontsize=8.2,
            color=DK, zorder=3)
    ax.text(6.3, 4.18, '医者（智能体）× 患者机体（环境）', ha='center', fontsize=7.4,
            color=MG, zorder=3)

    # 五元组节点（环状排布，白/浅灰底黑边）
    nodes = [
        (2.35, 6.35, 'S 状态集', 'state', '证候 / 症状组合\n"此刻我在哪" · 四诊信息', 'white'),
        (10.25, 6.35, 'A 动作集', 'action', '治法方剂 / 八法\n"可以怎么改变" · 辨证论治', 'white'),
        (11.45, 4.0, 'P 转移概率', 'transition prob.', '传变规律\n"下一步到哪、概率多大"', 'white'),
        (1.15, 4.0, 'R 奖励函数', 'reward', '疗效反馈\n"做得好不好" · 向愈为正、传变为负', G1),
        (6.3, 1.85, 'γ 折扣率', 'discount rate', '远期健康\n"看多远" · γ=0.9 愿为远期投入', G0),
    ]
    lines_pool = [
        ['证候 / 症状组合', '"此刻我在哪" · 四诊信息'],
        ['治法方剂 / 八法', '"可以怎么改变" · 辨证论治'],
        ['传变规律', '"下一步到哪、概率多大" · p(s\'|s,a)'],
        ['疗效反馈', '"做得好不好" · 向愈为正、传变为负'],
        ['远期健康', '"看多远" · γ=0.9 愿为远期投入'],
    ]
    for (cx, cy, title, en, sub, fc), lines in zip(nodes, lines_pool):
        ax.add_patch(Rectangle((cx - 1.32, cy - 0.92), 2.64, 1.8,
                               facecolor=fc, edgecolor=K, lw=1.5, zorder=3))
        ax.text(cx, cy + 0.56, f'{title}（{en}）', ha='center', fontsize=8.8,
                fontweight='bold', color=K, zorder=4)
        ax.text(cx, cy - 0.22, lines[0], ha='center', fontsize=7.9, color=DK, zorder=4)
        ax.text(cx, cy - 0.62, lines[1], ha='center', fontsize=7.2, color=MG, zorder=4)

    # 环向箭头：S→A→P→γ→R→S（黑色实线）
    arrows = [
        ((3.67, 6.35), (8.93, 6.35)),
        ((11.55, 6.15), (11.4, 4.9)),
        ((10.2, 3.5), (7.6, 2.4)),
        ((5.0, 2.4), (2.3, 3.15)),
        ((1.35, 4.9), (1.75, 5.65)),
    ]
    for (x1, y1), (x2, y2) in arrows:
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle='-|>', color=K, lw=1.9), zorder=3)
    ax.text(6.3, 6.75, '辨证立法：选动作', ha='center', fontsize=8.2, color=K, fontweight='bold')
    ax.text(11.0, 5.55, '用药 → 传变（P）', ha='center', fontsize=8.2, color=DK)
    ax.text(9.0, 2.95, '疗效 Rt+1\n（按 γ 折算入回报）', ha='center', fontsize=7.8,
            color=DK, linespacing=1.3)
    ax.text(3.55, 2.48, '折算远期\n（为未来定价）', ha='center', fontsize=7.8,
            color=DK, linespacing=1.3)
    ax.text(2.45, 5.28, '复诊转归 → 新状态', ha='center', fontsize=7.8, color=DK)

    # 底部：MDP 五元组一行 + 轨迹链（节点-连线）
    ax.plot([-0.3, 12.3], [1.02, 1.02], color=LG, lw=1.0, zorder=1)
    ax.text(6.3, 0.88, 'MDP 五元组 (S, A, P, R, γ)：一次完整诊疗 = 一次决策过程 —— 缺一不可，循环才转得起来',
            ha='center', fontsize=8.8, fontweight='bold', color=DK, zorder=3)
    traj = [('s1', '初诊证候', 0.9), ('s2', '复诊证候', 3.9), ('s3', '再诊证候', 6.9)]
    for s, txt, x0 in traj:
        ax.add_patch(Rectangle((x0, 0.08), 1.85, 0.6, facecolor='white',
                               edgecolor=K, lw=1.2, zorder=2))
        ax.text(x0 + 0.92, 0.38, f'{s} {txt}', ha='center', va='center',
                fontsize=8.4, color=DK, zorder=3)
    ax.annotate('', xy=(3.9, 0.38), xytext=(2.75, 0.38),
                arrowprops=dict(arrowstyle='-|>', color=K, lw=1.7), zorder=3)
    ax.annotate('', xy=(6.9, 0.38), xytext=(5.75, 0.38),
                arrowprops=dict(arrowstyle='-|>', color=K, lw=1.7), zorder=3)
    ax.text(3.32, 0.58, 'a1, r2', ha='center', fontsize=7.5, color=DK)
    ax.text(6.32, 0.58, 'a2, r3', ha='center', fontsize=7.5, color=DK)
    ax.text(9.45, 0.38, '轨迹（trajectory）：\n什么证 · 用什么方 · 得什么效 · 变成什么证',
            ha='left', va='center', fontsize=7.6, color=MG, linespacing=1.3)

    fig.savefig(os.path.join(OUT, 'fig2-1.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('fig2-1 done')


# ---------------------------------------------------------------- 图 2-2
def fig2_2():
    """图 2-2 病邪传变状态转移图：三状态模型与随机转移概率（费曼版）
    节点 = s1/s2/s3 状态方块（s1 白底黑粗边、s2/s3 浅灰底黑边）+ 右侧转移矩阵表；
    连线 = 三条转移箭头（0.7 自环黑粗弧、0.2 转 s2 黑实线、0.1 直入 s3 黑实线），
          灰色虚线 s2→s3 为传变示意；
    标注 = 转移概率直接标注在箭头上，矩阵第一行 (0.7,0.2,0.1) 黑粗高亮；
    底部 = 转归带五级灰阶（痊愈→好转→迁延→加重→死亡）。
    """
    fig, ax = plt.subplots(figsize=(10.0, 5.6))
    ax.set_xlim(-0.3, 12.9)
    ax.set_ylim(0, 6.8)
    ax.axis('off')

    # 三个状态（节点）
    ax.add_patch(Rectangle((0.7, 2.75), 2.7, 1.6, facecolor='white',
                           edgecolor=K, lw=2.0, zorder=3))
    ax.text(2.05, 3.72, 's1 表寒证', ha='center', fontsize=10.5, fontweight='bold',
            color=K, zorder=4)
    ax.text(2.05, 3.28, '（在 s1 用解表方后）', ha='center', fontsize=7.8, color=MG, zorder=4)

    ax.add_patch(Rectangle((4.6, 4.7), 2.4, 1.28, facecolor=G0,
                           edgecolor=K, lw=1.5, zorder=3))
    ax.text(5.8, 5.34, 's2 半表半里证', ha='center', fontsize=9.6, fontweight='bold',
            color=K, zorder=4)

    ax.add_patch(Rectangle((4.6, 0.85), 2.4, 1.28, facecolor=G1,
                           edgecolor=K, lw=1.5, zorder=3))
    ax.text(5.8, 1.49, 's3 里热证', ha='center', fontsize=9.6, fontweight='bold',
            color=K, zorder=4)

    # 转移箭头（数值与正文 2.3.2 一致；概率直接标注在线上）
    ax.annotate('', xy=(1.0, 4.15), xytext=(3.25, 4.15),
                arrowprops=dict(arrowstyle='-|>', color=K, lw=3.2,
                                connectionstyle='arc3,rad=-0.5'), zorder=3)
    ax.text(2.12, 4.65, '0.7 仍居 s1（自环）', ha='center', fontsize=8.6,
            fontweight='bold', color=K, zorder=4)
    ax.annotate('', xy=(4.6, 4.85), xytext=(3.4, 3.85),
                arrowprops=dict(arrowstyle='-|>', color=K, lw=2.2), zorder=3)
    ax.text(3.75, 4.5, '0.2 转 s2', ha='center', fontsize=8.6,
            fontweight='bold', color=K, zorder=4)
    ax.annotate('', xy=(4.6, 1.55), xytext=(3.4, 2.95),
                arrowprops=dict(arrowstyle='-|>', color=K, lw=2.2), zorder=3)
    ax.text(3.75, 2.15, '0.1 直入 s3', ha='center', fontsize=8.6,
            fontweight='bold', color=K, zorder=4)
    ax.annotate('', xy=(5.8, 2.13), xytext=(5.8, 4.7),
                arrowprops=dict(arrowstyle='-|>', color=LG, lw=1.4,
                                linestyle=(0, (3, 2))), zorder=3)
    ax.text(6.25, 3.5, '传变（示意）', ha='center', fontsize=7.8, color=MG, zorder=4)

    # 右侧：转移矩阵（黑白表，第一行高亮）
    ax.text(9.55, 6.35, '转移矩阵 P：把传变规律压缩成一张表', ha='center', fontsize=9.6,
            fontweight='bold', color=K)
    ax.text(9.55, 6.0, r'$[P]_{ij} = p(s_j | s_i, a)$；复合矩阵 $[P_\pi]_{ij} = \sum_a \pi(a|s_i)\, p(s_j | s_i, a)$',
            ha='center', fontsize=7.4, color=MG)
    ax.text(7.9, 5.45, '当前状态 \\ 下一状态', ha='center', fontsize=7.4, color=MG)
    for x0, col in [(8.95, '→ s1'), (10.05, '→ s2'), (11.15, '→ s3')]:
        ax.text(x0, 5.22, col, ha='center', fontsize=7.8, color=MG)
    row_data = [
        ('s1 表寒证', ['0.7', '0.2', '0.1'], True),
        ('s2 半表半里', ['·', '·', '·'], False),
        ('s3 里热证', ['·', '·', '·'], False),
    ]
    for i, (rlabel, cells, hl) in enumerate(row_data):
        ytop = 4.9 - i * 0.55
        ax.text(7.9, ytop - 0.26, rlabel, ha='center', va='center', fontsize=7.9,
                color=K)
        for j, val in enumerate(cells):
            x0 = 8.4 + j * 1.1
            fc = G1 if hl else 'white'
            ec = K if hl else LG
            lw = 1.8 if hl else 0.8
            ax.add_patch(Rectangle((x0, ytop - 0.5), 1.1, 0.5, facecolor=fc,
                                   edgecolor=ec, lw=lw, zorder=2))
            ax.text(x0 + 0.55, ytop - 0.25, val, ha='center', va='center',
                    fontsize=(9.6 if hl else 8.2),
                    color=(K if hl else LG),
                    fontweight=('bold' if hl else 'normal'), zorder=3)
    ax.text(9.55, 3.08, '每行之和 = 1（随机矩阵）——未来不会凭空消失，只会落入某个状态',
            ha='center', fontsize=8.6, fontweight='bold', color=K)
    ax.text(9.55, 2.7, '转移概率估计：数据统计（100 例麻黄汤 70/20/10）· 专家经验 · 文献证据（A/B/C 分级）',
            ha='center', fontsize=7.3, color=MG)

    # 底部：转归带（五级灰阶，黑边）
    outcomes = [('痊愈', 'white', K), ('好转', G2, K), ('迁延', G3, K),
                ('加重', '#9c9c9c', 'white'), ('死亡', '#3a3a3a', 'white')]
    x0 = 0.4
    ax.text(6.6, 1.62, '转归是转移的终点或中间站 —— 预判转归，先安未受邪之地（既病防变）',
            ha='center', fontsize=7.8, color=MG)
    for name, color, tc in outcomes:
        ax.add_patch(Rectangle((x0, 0.12), 2.42, 0.6, facecolor=color,
                               edgecolor=K, lw=1.0, zorder=2))
        ax.text(x0 + 1.21, 0.42, name, ha='center', va='center', fontsize=8.8,
                fontweight='bold', color=tc, zorder=3)
        x0 += 2.42

    fig.savefig(os.path.join(OUT, 'fig2-2.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('fig2-2 done')


# ---------------------------------------------------------------- 图 2-3
def fig2_3():
    """图 2-3 治未病与折扣回报时间轴：γ 决定眼光，防大于治（费曼版）
    节点 = 时间轴刻度点 + γ 旋钮（半圆弧 + 指针）+ 三策略灰阶柱 + 治未病三层次方块；
    连线 = 黑色时间轴箭头（0→3 步）、旋钮指针箭头（γ=0.9）、柱间差值双箭头；
    标注 = γ^k 权重、G1=9/G3=8.5/G2=8、差值 0.5 全部直接标在线上/柱顶。
    """
    fig, ax = plt.subplots(figsize=(10.4, 6.4))
    ax.set_xlim(-0.2, 13.0)
    ax.set_ylim(0, 7.9)
    ax.axis('off')

    # ---- 第一栏：折扣回报时间轴（聚焦 0~4 步权重段）----
    ax.text(0.4, 7.45, r'折扣回报 $G_t = R_{t+1} + \gamma R_{t+2} + \gamma^2 R_{t+3} + \dots$（γ ∈ (0,1)）',
            ha='left', fontsize=10.2, fontweight='bold', color=K)
    ax.annotate('', xy=(9.3, 6.6), xytext=(1.0, 6.6),
                arrowprops=dict(arrowstyle='-|>', color=K, lw=2.0), zorder=3)
    ax.text(9.7, 6.52, '时间步 t →', ha='left', fontsize=8.4, color=MG)
    for k in range(4):
        x = 1.0 + k * 2.0
        ax.plot([x, x], [6.53, 6.67], color=K, lw=1.1, zorder=3)
        ax.add_patch(Circle((x, 6.6), 0.07, facecolor=K, edgecolor='none', zorder=3))
        ax.text(x, 6.9, f'权重 ' + r'$\gamma^{%d}$' % k, ha='center', fontsize=7.8, color=DK)
        if k == 0:
            ax.text(x, 6.3, 't=0 当下\n投入：0 或 -1', ha='center', fontsize=7.5, color=DK)
        else:
            ax.text(x, 6.3, '+1\n每期健康奖励', ha='center', fontsize=7.5, color=K)
    ax.text(10.5, 7.45, '把未来每步得失按折扣折算到当下再相加；\n越远的未来权重越小 —— 现在的一分健康\n比未来的一分更真实（时间偏好）',
            ha='center', fontsize=7.7, color=MG, linespacing=1.35)
    ax.text(0.4, 5.7, 'γ 小 → 短视（急则治标）　·　γ 大 → 远视（缓则治本）',
            ha='left', fontsize=8.4, color=DK, fontweight='bold')

    # ---- 第二栏左：γ 旋钮 ----
    ax.text(2.9, 5.35, 'γ 旋钮：为时间定价（目光远近）', ha='center', fontsize=9.4,
            fontweight='bold', color=K)
    cx, cy, r = 2.9, 3.45, 1.25
    theta = [math.pi - math.pi * g for g in [0, 0.25, 0.5, 0.75, 0.9, 1]]
    for t in theta:
        x1, y1 = cx + (r - 0.1) * math.cos(t), cy + (r - 0.1) * math.sin(t)
        x2, y2 = cx + (r + 0.1) * math.cos(t), cy + (r + 0.1) * math.sin(t)
        ax.plot([x1, x2], [y1, y2], color=MG, lw=1.3, zorder=3)
    arc = Arc((cx, cy), 2 * r, 2 * r, theta1=0, theta2=180, color=K, lw=2.0, zorder=3)
    ax.add_patch(arc)
    ax.text(1.5, 3.3, '0', ha='center', fontsize=8.4, color=DK)
    ax.text(2.9, 4.82, '0.5', ha='center', fontsize=8.4, color=DK)
    ax.text(4.35, 3.3, '1', ha='center', fontsize=8.4, color=DK)
    # 指针 γ=0.9（黑色粗箭头）
    t90 = math.pi - math.pi * 0.9
    ax.annotate('', xy=(cx + r * math.cos(t90), cy + r * math.sin(t90)),
                xytext=(cx + 0.22 * math.cos(t90), cy + 0.22 * math.sin(t90)),
                arrowprops=dict(arrowstyle='-|>', color=K, lw=3.0), zorder=4)
    ax.text(4.2, 4.15, 'γ=0.9\n（愿为远期健康投入）', ha='left', fontsize=7.8,
            fontweight='bold', color=K, zorder=4, linespacing=1.3)
    ax.text(1.6, 2.62, 'γ→0\n只看眼前（急症）', ha='center', fontsize=7.4, color=MG, linespacing=1.3)
    ax.text(4.3, 2.62, 'γ→1\n未来≈现在（治未病）', ha='center', fontsize=7.4, color=MG, linespacing=1.3)
    ax.text(2.9, 2.12, '奖励恒为 +1 时：' + r'$G = 1/(1-\gamma)$' + ' → ' + r'$\gamma=0.5$' + ' 得 2；' + r'$\gamma=0.9$' + ' 得 10',
            ha='center', fontsize=8.4, fontweight='bold', color=K)

    # ---- 第二栏右：三策略柱状图（γ=0.9；聚焦 8~9 刻度区间，灰阶柱）----
    ax.text(9.7, 5.35, '三策略回报比较（γ = 0.9）', ha='center', fontsize=9.4,
            fontweight='bold', color=K)
    base = 2.6
    ax.plot([6.9, 6.9], [base, 5.05], color=K, lw=1.1, zorder=2)
    for val, yy in [(8, base + 8 * 0.2), (8.5, base + 8.5 * 0.2), (9, base + 9 * 0.2)]:
        ax.plot([6.85, 6.95], [yy, yy], color=K, lw=0.9, zorder=2)
        ax.text(6.75, yy, f'{val}', ha='right', va='center', fontsize=7.4, color=DK)
    ax.text(6.75, 3.7, 'G', ha='right', va='center', fontsize=8.4, color=DK, rotation=90)
    bars = [
        ('未病先防', 9, 'white', K, 'G1 = 9'),
        ('时防时忽', 8.5, G3, K, 'G3 = 8.5'),
        ('病后才治', 8, '#6f6f6f', K, 'G2 = 8'),
    ]
    for i, (name, val, fc, ec, vlab) in enumerate(bars):
        cx0 = 8.0 + i * 1.6
        h = val * 0.2
        ax.add_patch(Rectangle((cx0 - 0.55, base), 1.1, h, facecolor=fc,
                               edgecolor=ec, lw=1.4, zorder=3))
        tc = 'white' if fc == '#6f6f6f' else K
        ax.text(cx0, base + h + 0.11, vlab, ha='center', fontsize=8.8,
                fontweight='bold', color=tc, zorder=4)
        ax.text(cx0, base - 0.3, name, ha='center', fontsize=8.2, color=DK, zorder=4)
    # 差值箭头（0.5 / 0.5，黑色双箭头）
    ax.annotate('', xy=(9.15, 4.85), xytext=(8.55, 4.85),
                arrowprops=dict(arrowstyle='<->', color=K, lw=1.6), zorder=4)
    ax.text(8.85, 4.98, '0.5', ha='center', fontsize=8.2, fontweight='bold', color=K)
    ax.annotate('', xy=(10.75, 4.85), xytext=(10.15, 4.85),
                arrowprops=dict(arrowstyle='<->', color=K, lw=1.6), zorder=4)
    ax.text(10.45, 4.98, '0.5', ha='center', fontsize=8.2, fontweight='bold', color=K)
    ax.text(9.7, 2.0, 'G1 > G3 > G2：预防优于时防时忽，更优于病后才治（防大于治）\n'
                      '差距由第一步的即时奖励决定 —— 一步之差，千里之遥',
            ha='center', fontsize=7.6, color=K, linespacing=1.35)

    # ---- 第三栏：治未病三层次（三个方块节点）----
    levels = [
        (0.5, '未病先防', ['大 γ · 十年尺度', '健康管理 · 调摄养生', '"圣人不治已病治未病"'], 'white'),
        (4.6, '既病防变', ['中 γ · 疗程尺度', '治疗期 · 截断传变', '"见肝之病，知肝传脾"'], G0),
        (8.7, '瘥后防复', ['较大 γ · 随访尺度', '康复期 · 巩固调养', '愈后随访，防其复发'], G1),
    ]
    for x0, title, lines, fc in levels:
        ax.add_patch(Rectangle((x0, 0.28), 3.9, 1.5, facecolor=fc,
                               edgecolor=K, lw=1.4, zorder=2))
        ax.text(x0 + 1.95, 1.5, title, ha='center', fontsize=9.2, fontweight='bold',
                color=K, zorder=3)
        ax.text(x0 + 1.95, 1.05, lines[0], ha='center', fontsize=7.9, color=DK, zorder=3)
        ax.text(x0 + 1.95, 0.72, lines[1], ha='center', fontsize=7.9, color=DK, zorder=3)
        ax.text(x0 + 1.95, 0.42, lines[2], ha='center', fontsize=7.3, color=MG, zorder=3)

    fig.savefig(os.path.join(OUT, 'fig2-3.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('fig2-3 done')


# ---------------------------------------------------------------- 图 2-4
def fig2_4():
    """图 2-4 价值函数阶梯：从认知走向判断（四状态价值求解）（费曼版）
    节点 = 认知阶梯 6 级灰阶台阶 + 四状态方块（s4 吸收态深灰底黑粗边）
          + 贝尔曼方程黑边方框；
    连线 = 黑色虚线粗箭头（认知→判断）+ 状态间黑色实线转移箭头（r 标线上）；
    标注 = v=(9,10,10,10) 直接标在节点旁，s4 自环 +1 标在弧线上。
    """
    fig, ax = plt.subplots(figsize=(9.9, 6.1))
    ax.set_xlim(-0.3, 12.9)
    ax.set_ylim(0, 7.5)
    ax.axis('off')

    # ---- 上部：认知阶梯（六阶，灰阶递增，黑边）----
    steps = ['看全 2.1', '建准 2.2', '算转移 2.3', '明回报 2.4', '知边界 2.5', '定价值 2.6']
    grays = ['#ffffff', '#f5f5f5', '#eeeeee', '#e6e6e6', '#dedede', '#d6d6d6']
    base_y, x0, step_w, gap = 4.9, 0.9, 1.5, 0.18
    for i, name in enumerate(steps):
        h = 0.45 + i * 0.3
        cx = x0 + i * (step_w + gap)
        ax.add_patch(Rectangle((cx - step_w / 2, base_y), step_w, h,
                               facecolor=grays[i], edgecolor=K, lw=1.4, zorder=3))
        ax.text(cx, base_y + h / 2, name, ha='center', va='center', fontsize=8.8,
                fontweight='bold', color=K, zorder=4)
    ax.annotate('', xy=(9.9, 7.0), xytext=(0.9, 5.5),
                arrowprops=dict(arrowstyle='-|>', color=K, lw=1.9,
                                linestyle=(0, (6, 2))), zorder=3)
    ax.text(5.4, 7.28, r'认知 → 判断：$v_\pi(s) = E[G_t | S_t = s]$' + '（期望 × 折扣回报）',
            ha='center', fontsize=8.6, fontweight='bold', color=K)
    ax.text(0.9, 4.65, '认知：描述世界\n（观测—建模—转移—回报—期望）',
            ha='center', fontsize=7.6, color=MG, linespacing=1.3)
    ax.text(10.6, 7.0, '判断：行动有依据\n（状态好坏可比较、可排序）',
            ha='center', fontsize=7.6, color=DK, linespacing=1.3)

    # ---- 左下：四状态转移图 ----
    ax.text(3.3, 4.15, '四状态健康模型（γ = 0.9）', ha='center', fontsize=9.6,
            fontweight='bold', color=K)
    states = [
        (1.8, 1.35, 's1 表证初起', 'white', 1.4),
        (4.35, 2.95, 's2 向愈', G0, 1.4),
        (1.6, 3.2, 's3 里证正治', G0, 1.4),
        (6.1, 1.5, 's4 痊愈（吸收态）', '#d6d6d6', 2.4),
    ]
    for cx, cy, name, fc, lw in states:
        ax.add_patch(Rectangle((cx - 1.1, cy - 0.5), 2.2, 1.0, facecolor=fc,
                               edgecolor=K, lw=lw, zorder=3))
        ax.text(cx, cy, name, ha='center', va='center', fontsize=8.4,
                fontweight='bold', color=K, zorder=4)
    ax.annotate('', xy=(3.2, 2.55), xytext=(2.9, 1.55),
                arrowprops=dict(arrowstyle='-|>', color=K, lw=1.9), zorder=3)
    ax.text(3.6, 1.95, 'r=0', ha='center', fontsize=7.9, color=MG)
    ax.annotate('', xy=(5.8, 2.05), xytext=(4.4, 2.45),
                arrowprops=dict(arrowstyle='-|>', color=K, lw=1.9), zorder=3)
    ax.text(5.25, 2.5, 'r=+1', ha='center', fontsize=7.9, color=DK, fontweight='bold')
    ax.annotate('', xy=(4.95, 1.75), xytext=(2.75, 2.95),
                arrowprops=dict(arrowstyle='-|>', color=K, lw=1.9), zorder=3)
    ax.text(3.8, 2.6, 'r=+1', ha='center', fontsize=7.9, color=DK, fontweight='bold')
    ax.annotate('', xy=(5.45, 2.05), xytext=(6.75, 2.05),
                arrowprops=dict(arrowstyle='-|>', color=K, lw=1.9,
                                connectionstyle='arc3,rad=0.45'), zorder=3)
    ax.text(6.1, 2.55, 'r=+1 自环', ha='center', fontsize=7.3, color=K, fontweight='bold')
    # 价值标注（直接标节点旁）
    ax.text(0.65, 1.35, 'v=9', ha='center', va='center', fontsize=8.8,
            fontweight='bold', color=K, zorder=4)
    ax.text(0.8, 2.35, 'v=10', ha='center', va='center', fontsize=8.8,
            fontweight='bold', color=K, zorder=4)
    ax.text(5.9, 3.2, 'v=10', ha='center', va='center', fontsize=8.8,
            fontweight='bold', color=K, zorder=4)
    ax.text(7.3, 1.0, 'v=10', ha='left', va='center', fontsize=9.2,
            fontweight='bold', color=K, zorder=4)
    ax.text(4.15, 0.42, r'$v_\pi(s_4) = 1 + 0.9\, v_\pi(s_4) \to 10$' + '；价值向量 v = (9, 10, 10, 10)',
            ha='center', fontsize=8.8, fontweight='bold', color=K)
    ax.text(4.15, 0.1, '离健康越近，价值越高 —— 这个"距离"正是折扣的直观体现',
            ha='center', fontsize=7.8, color=MG)

    # ---- 右下：贝尔曼方程框（白底黑边直角框）----
    ax.add_patch(Rectangle((7.6, 0.28), 5.1, 3.85, facecolor='white',
                           edgecolor=K, lw=1.6, zorder=2))
    ax.text(10.15, 3.82, '贝尔曼方程（自举 + 条件期望）', ha='center', fontsize=9.4,
            fontweight='bold', color=K, zorder=3)
    ax.text(10.15, 3.4,
            r'$v_\pi(s) = \sum_a \pi(a|s)\left[\sum_r p(r|s,a)\,r + \gamma \sum_{s^{\prime}} p(s^{\prime}|s,a)\,v_\pi(s^{\prime})\right]$',
            ha='center', fontsize=7.2, color=K, zorder=3)
    ax.text(10.15, 2.98, r'矩阵形式：$v = r_\pi + \gamma P_\pi v$　解析解：$v = (I - \gamma P_\pi)^{-1} r_\pi$',
            ha='center', fontsize=8.2, fontweight='bold', color=K, zorder=3)
    ax.text(10.15, 2.56, r'迭代：$v_{k+1} = r_\pi + \gamma P_\pi v_k$，误差每步至少缩小 γ 倍',
            ha='center', fontsize=7.8, color=DK, zorder=3)
    ax.text(10.15, 2.14, '三个基本性质：存在性 · 唯一性 · 迭代收敛',
            ha='center', fontsize=7.8, color=DK, zorder=3)
    ax.text(10.15, 1.72, '状态价值 = 临床价值（证候的期望疗效）\n动作价值 = 方证对应（有是证用是方）',
            ha='center', fontsize=7.6, color=K, zorder=3, fontweight='bold', linespacing=1.3)
    ax.text(10.15, 1.0, r'自举：$G_t = R_{t+1} + \gamma G_{t+1}$' + ' —— 未来从当下生长出来',
            ha='center', fontsize=7.4, color=MG, zorder=3)

    fig.savefig(os.path.join(OUT, 'fig2-4.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('fig2-4 done')


if __name__ == '__main__':
    fig2_1()
    fig2_2()
    fig2_3()
    fig2_4()
    print('ALL DONE ->', OUT)
