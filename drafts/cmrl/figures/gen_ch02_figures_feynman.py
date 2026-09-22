# -*- coding: utf-8 -*-
"""《中医场景强化学习》第2章 核心图生成脚本（v4 图内文字精简与字号规范版，图表工程师 2026-08-20）

【图内文字精简与字号规范】批次落地（与第1/3章统一）：
  ① 文字分层精简：每幅图图内只保留核心标注（节点名 + 1-2 个关键数值），每幅 ≤10 个标注；
     长描述、公式细节、次要数值（五元组副文字、转移矩阵、公式、刻度标签等）全部移入图注；
  ② 字号规范：核心标注 fontsize≥11、节点名 ≥10、任何文字禁 <9pt；
  ③ 背景降噪：白底（去浅灰填充 G0/G1/G2）、无网格线、去装饰框、框线细（lw≤1）、
     图例并入节点标注；
  ④ 忠实语义：证候/方剂/传变/疗效/价值等关键语义保留，数值锚点（0.7/0.2/0.1、G1=9、v=(9,10,10,10)）保留在图注；
  ⑤ 图注（md 与 Excel）补『e. 阅读引导』句。

数值约定（与正文 2.2–2.6 节一致，不得另造）：
  转移概率 0.7/0.2/0.1（2.2.2、2.3.2）；γ=0.5 → G=2，γ=0.9 → G=10（2.4.2）
  G1=9（未病先防）> G3=8.5（时防时忽）> G2=8（病后才治），差值 0.5（2.4.2）
  四状态 v=(9,10,10,10)，s4 吸收态自环 +1，γ=0.9（2.6.2）

生成：fig2-1 / fig2-2 / fig2-3 / fig2-4（覆盖 figures/ch02/*.png，SimHei + unicode_minus=False + dpi=200）
"""
import os
import math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, Arc

plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ch02')
os.makedirs(OUT, exist_ok=True)

# ---- 色板 ----
K   = '#111111'
DK  = '#333333'
MG  = '#666666'
LG  = '#999999'
G2  = '#e2e2e2'   # 转归带浅灰（数据灰阶，保留）
G3  = '#cfcfcf'
GRAY_D = '#9c9c9c'  # 转归带加重
GRAY_K = '#3a3a3a'  # 转归带死亡

FS_NODE  = 10   # 节点名
FS_KEY   = 11   # 核心标注（关键数值）
FS_MAIN  = 12   # 主节点名/强调数值
LW_BOX   = 1.0  # 框线细


# ---------------------------------------------------------------- 图 2-1
def fig2_1():
    """图 2-1 健康演化决策过程模型：五元组环图与诊疗循环（精简版）
    图内 10 个标注：中心诊疗循环 + 五元组 S/A/P/R/γ 节点名 + 轨迹链 s1/s2/s3 + 1 行说明；
    节点副文字、环向箭头注释全部移入图注。
    """
    fig, ax = plt.subplots(figsize=(10.0, 6.0))
    ax.set_xlim(-0.4, 12.4)
    ax.set_ylim(0, 7.0)
    ax.axis('off')

    # 中心：诊疗循环（圆圈节点）
    hub = Circle((6.3, 4.55), 1.28, facecolor='white', edgecolor=K, lw=LW_BOX, zorder=2)
    ax.add_patch(hub)
    ax.text(6.3, 4.55, '诊疗循环', ha='center', va='center', fontsize=FS_MAIN,
            fontweight='bold', color=K, zorder=3)

    # 五元组节点（环状排布，白底黑细边；只保留节点名）
    nodes = [
        (2.35, 6.35, 'S 证候集'),
        (10.25, 6.35, 'A 方剂集'),
        (11.45, 4.0, 'P 传变规律'),
        (1.15, 4.0, 'R 疗效反馈'),
        (6.3, 1.85, 'γ 远期权重'),
    ]
    for cx, cy, title in nodes:
        ax.add_patch(Rectangle((cx - 1.32, cy - 0.6), 2.64, 1.2,
                               facecolor='white', edgecolor=K, lw=LW_BOX, zorder=3))
        ax.text(cx, cy, title, ha='center', va='center', fontsize=FS_KEY,
                fontweight='bold', color=K, zorder=4)

    # 环向箭头：S→A→P→γ→R→S（黑色细实线）
    arrows = [
        ((3.67, 6.35), (8.93, 6.35)),
        ((11.55, 6.15), (11.4, 4.9)),
        ((10.2, 3.5), (7.6, 2.4)),
        ((5.0, 2.4), (2.3, 3.15)),
        ((1.35, 4.9), (1.75, 5.65)),
    ]
    for (x1, y1), (x2, y2) in arrows:
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle='-|>', color=K, lw=1.3), zorder=3)

    # 底部：轨迹链 s1→s2→s3（白底黑细边）
    ax.plot([-0.3, 12.3], [1.02, 1.02], color=LG, lw=0.8, zorder=1)
    traj = [('s1', '初诊', 0.9), ('s2', '复诊', 3.9), ('s3', '再诊', 6.9)]
    for s, txt, x0 in traj:
        ax.add_patch(Rectangle((x0, 0.08), 1.85, 0.6, facecolor='white',
                               edgecolor=K, lw=LW_BOX, zorder=2))
        ax.text(x0 + 0.92, 0.38, f'{s} {txt}', ha='center', va='center',
                fontsize=FS_NODE, fontweight='bold', color=DK, zorder=3)
    ax.annotate('', xy=(3.9, 0.38), xytext=(2.75, 0.38),
                arrowprops=dict(arrowstyle='-|>', color=K, lw=1.3), zorder=3)
    ax.annotate('', xy=(6.9, 0.38), xytext=(5.75, 0.38),
                arrowprops=dict(arrowstyle='-|>', color=K, lw=1.3), zorder=3)

    # 第 10 个标注：五元组核心语义
    ax.text(6.3, 0.82, '五元组 (S, A, P, R, γ)：一次完整诊疗 = 一次决策过程',
            ha='center', va='center', fontsize=FS_NODE, fontweight='bold', color=DK, zorder=3)

    fig.savefig(os.path.join(OUT, 'fig2-1.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('fig2-1 done')


# ---------------------------------------------------------------- 图 2-2
def fig2_2():
    """图 2-2 病邪传变状态转移图：三状态模型与随机转移概率（精简版）
    图内 7 个标注：s1/s2/s3 节点名 + 0.7/0.2/0.1 概率 + 转归带 1 行；
    转移矩阵、公式、估计途径全部移入图注。
    """
    fig, ax = plt.subplots(figsize=(9.2, 5.4))
    ax.set_xlim(-0.3, 12.9)
    ax.set_ylim(0, 6.8)
    ax.axis('off')

    # 三个状态（节点，白底黑细边）
    ax.add_patch(Rectangle((0.7, 2.75), 2.7, 1.6, facecolor='white',
                           edgecolor=K, lw=LW_BOX, zorder=3))
    ax.text(2.05, 3.55, 's1 表寒证', ha='center', va='center', fontsize=FS_KEY,
            fontweight='bold', color=K, zorder=4)
    ax.add_patch(Rectangle((4.6, 4.7), 2.4, 1.28, facecolor='white',
                           edgecolor=K, lw=LW_BOX, zorder=3))
    ax.text(5.8, 5.34, 's2 半表半里证', ha='center', va='center', fontsize=FS_KEY,
            fontweight='bold', color=K, zorder=4)
    ax.add_patch(Rectangle((4.6, 0.85), 2.4, 1.28, facecolor='white',
                           edgecolor=K, lw=LW_BOX, zorder=3))
    ax.text(5.8, 1.49, 's3 里热证', ha='center', va='center', fontsize=FS_KEY,
            fontweight='bold', color=K, zorder=4)

    # 转移箭头（概率直接标注在线上，核心数值）
    ax.annotate('', xy=(1.0, 4.15), xytext=(3.25, 4.15),
                arrowprops=dict(arrowstyle='-|>', color=K, lw=1.5,
                                connectionstyle='arc3,rad=-0.5'), zorder=3)
    ax.text(2.12, 4.72, '0.7 自环', ha='center', fontsize=FS_KEY,
            fontweight='bold', color=K, zorder=4)
    ax.annotate('', xy=(4.6, 4.85), xytext=(3.4, 3.85),
                arrowprops=dict(arrowstyle='-|>', color=K, lw=1.3), zorder=3)
    ax.text(3.75, 4.5, '0.2 转 s2', ha='center', fontsize=FS_KEY,
            fontweight='bold', color=K, zorder=4)
    ax.annotate('', xy=(4.6, 1.55), xytext=(3.4, 2.95),
                arrowprops=dict(arrowstyle='-|>', color=K, lw=1.3), zorder=3)
    ax.text(3.75, 2.15, '0.1 直入 s3', ha='center', fontsize=FS_KEY,
            fontweight='bold', color=K, zorder=4)
    # 传变示意虚线（s2→s3，图形不写字）
    ax.annotate('', xy=(5.8, 2.13), xytext=(5.8, 4.7),
                arrowprops=dict(arrowstyle='-|>', color=LG, lw=0.9,
                                linestyle=(0, (3, 2))), zorder=3)

    # 底部：转归带（五级灰阶，保留数据灰阶；文字合并为 1 行）
    outcomes = [('痊愈', 'white', K), ('好转', G2, K), ('迁延', G3, K),
                ('加重', GRAY_D, 'white'), ('死亡', GRAY_K, 'white')]
    x0 = 0.4
    for name, color, tc in outcomes:
        ax.add_patch(Rectangle((x0, 0.12), 2.42, 0.6, facecolor=color,
                               edgecolor=K, lw=LW_BOX, zorder=2))
        x0 += 2.42
    ax.text(6.6, 1.15, '转归带：痊愈 → 好转 → 迁延 → 加重 → 死亡',
            ha='center', va='center', fontsize=FS_NODE, color=MG, zorder=4)

    fig.savefig(os.path.join(OUT, 'fig2-2.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('fig2-2 done')


# ---------------------------------------------------------------- 图 2-3
def fig2_3():
    """图 2-3 治未病与折扣回报时间轴：γ 决定眼光，防大于治（精简版）
    图内 10 个标注：时间轴 γ^k 说明 1 + γ 旋钮指针 1 + 三策略柱（名称+数值合并）3
    + 差值 0.5 两个 + 治未病三层次 3；权重公式、刻度、折算计式全部移入图注。
    """
    fig, ax = plt.subplots(figsize=(10.4, 6.4))
    ax.set_xlim(-0.2, 13.0)
    ax.set_ylim(0, 7.9)
    ax.axis('off')

    # ---- 第一栏：折扣回报时间轴（图形保留，刻度权重文本移图注）----
    ax.annotate('', xy=(9.3, 6.6), xytext=(1.0, 6.6),
                arrowprops=dict(arrowstyle='-|>', color=K, lw=1.3), zorder=3)
    for k in range(4):
        x = 1.0 + k * 2.0
        ax.plot([x, x], [6.53, 6.67], color=K, lw=0.8, zorder=3)
        ax.add_patch(Circle((x, 6.6), 0.07, facecolor=K, edgecolor='none', zorder=3))
    ax.text(0.4, 6.9, r'时间轴：远期权重 $\gamma^k$ 逐期递减', ha='left', fontsize=FS_NODE,
            fontweight='bold', color=DK)

    # ---- 第二栏左：γ 旋钮（图形保留；刻度 0/0.5/1 移图注）----
    cx, cy, r = 2.9, 3.45, 1.25
    theta = [math.pi - math.pi * g for g in [0, 0.25, 0.5, 0.75, 0.9, 1]]
    for t in theta:
        x1, y1 = cx + (r - 0.1) * math.cos(t), cy + (r - 0.1) * math.sin(t)
        x2, y2 = cx + (r + 0.1) * math.cos(t), cy + (r + 0.1) * math.sin(t)
        ax.plot([x1, x2], [y1, y2], color=MG, lw=0.8, zorder=3)
    arc = Arc((cx, cy), 2 * r, 2 * r, theta1=0, theta2=180, color=K, lw=1.0, zorder=3)
    ax.add_patch(arc)
    t90 = math.pi - math.pi * 0.9
    ax.annotate('', xy=(cx + r * math.cos(t90), cy + r * math.sin(t90)),
                xytext=(cx + 0.22 * math.cos(t90), cy + 0.22 * math.sin(t90)),
                arrowprops=dict(arrowstyle='-|>', color=K, lw=1.6), zorder=4)
    ax.text(3.6, 4.35, r'$\gamma = 0.9$', ha='left', fontsize=FS_MAIN,
            fontweight='bold', color=K, zorder=4)

    # ---- 第二栏右：三策略柱状图（柱内名称+数值合并）----
    base = 2.6
    ax.plot([6.9, 6.9], [base, 5.05], color=K, lw=0.8, zorder=2)
    bars = [
        ('未病先防', 9, 'white', 'G1 = 9'),
        ('时防时忽', 8.5, G3, 'G3 = 8.5'),
        ('病后才治', 8, G2, 'G2 = 8'),
    ]
    for i, (name, val, fc, vlab) in enumerate(bars):
        cx0 = 8.0 + i * 1.6
        h = val * 0.2
        ax.add_patch(Rectangle((cx0 - 0.55, base), 1.1, h, facecolor=fc,
                               edgecolor=K, lw=LW_BOX, zorder=3))
        ax.text(cx0, base + h / 2, f'{vlab}\n{name}', ha='center', va='center',
                fontsize=FS_KEY, fontweight='bold', color=K, zorder=4, linespacing=1.4)
    # 差值箭头（0.5 / 0.5）
    ax.annotate('', xy=(9.15, 4.85), xytext=(8.55, 4.85),
                arrowprops=dict(arrowstyle='<->', color=K, lw=1.0), zorder=4)
    ax.text(8.85, 4.98, '0.5', ha='center', fontsize=FS_KEY, fontweight='bold', color=K)
    ax.annotate('', xy=(10.75, 4.85), xytext=(10.15, 4.85),
                arrowprops=dict(arrowstyle='<->', color=K, lw=1.0), zorder=4)
    ax.text(10.45, 4.98, '0.5', ha='center', fontsize=FS_KEY, fontweight='bold', color=K)

    # ---- 第三栏：治未病三层次（三个方块节点）----
    levels = [
        (0.5, '未病先防'), (4.6, '既病防变'), (8.7, '瘥后防复'),
    ]
    for x0, title in levels:
        ax.add_patch(Rectangle((x0, 0.28), 3.9, 1.5, facecolor='white',
                               edgecolor=K, lw=LW_BOX, zorder=2))
        ax.text(x0 + 1.95, 1.03, title, ha='center', va='center', fontsize=FS_NODE,
                fontweight='bold', color=K, zorder=3)

    fig.savefig(os.path.join(OUT, 'fig2-3.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('fig2-3 done')


# ---------------------------------------------------------------- 图 2-4
def fig2_4():
    """图 2-4 价值函数阶梯：从认知走向判断（四状态价值求解）（精简版）
    图内 10 个标注：认知阶梯 6 级（节点名）+ 四状态方块 4（节点名+价值 v）；
    贝尔曼方程、转移奖励 r、价值推导全部移入图注。
    """
    fig, ax = plt.subplots(figsize=(10.0, 6.2))
    ax.set_xlim(-0.3, 12.9)
    ax.set_ylim(0, 7.5)
    ax.axis('off')

    # ---- 上部：认知阶梯（六阶，白底黑细边，高度递增表达递进）----
    steps = ['看全', '建准', '算转移', '明回报', '知边界', '定价值']
    base_y, x0, step_w, gap = 4.9, 0.9, 1.5, 0.18
    for i, name in enumerate(steps):
        h = 0.45 + i * 0.3
        cx = x0 + i * (step_w + gap)
        ax.add_patch(Rectangle((cx - step_w / 2, base_y), step_w, h,
                               facecolor='white', edgecolor=K, lw=LW_BOX, zorder=3))
        ax.text(cx, base_y + h / 2, name, ha='center', va='center', fontsize=FS_NODE,
                fontweight='bold', color=K, zorder=4)
    # 认知→判断 虚线箭头（图形，文字移图注）
    ax.annotate('', xy=(9.9, 7.0), xytext=(0.9, 5.5),
                arrowprops=dict(arrowstyle='-|>', color=K, lw=1.0,
                                linestyle=(0, (6, 2))), zorder=3)

    # ---- 左下：四状态转移图（节点名 + 价值向量）----
    states = [
        (1.8, 1.35, 's1 表证初起', 'v = 9'),
        (4.35, 2.95, 's2 向愈', 'v = 10'),
        (1.6, 3.2, 's3 里证正治', 'v = 10'),
        (6.1, 1.5, 's4 痊愈', 'v = 10'),
    ]
    for cx, cy, name, val in states:
        fc = 'white'
        if name.startswith('s4'):
            ax.add_patch(Rectangle((cx - 1.13, cy - 0.53), 2.26, 1.06, facecolor='none',
                                   edgecolor=K, lw=LW_BOX, zorder=2))
        ax.add_patch(Rectangle((cx - 1.1, cy - 0.5), 2.2, 1.0, facecolor=fc,
                               edgecolor=K, lw=LW_BOX, zorder=3))
        ax.text(cx, cy, f'{name}\n{val}', ha='center', va='center', fontsize=FS_KEY,
                fontweight='bold', color=K, zorder=4, linespacing=1.3)
    # 转移箭头（图形，奖励 r 移图注）
    ax.annotate('', xy=(3.2, 2.55), xytext=(2.9, 1.55),
                arrowprops=dict(arrowstyle='-|>', color=K, lw=1.2), zorder=3)
    ax.annotate('', xy=(5.8, 2.05), xytext=(4.4, 2.45),
                arrowprops=dict(arrowstyle='-|>', color=K, lw=1.2), zorder=3)
    ax.annotate('', xy=(4.95, 1.75), xytext=(2.75, 2.95),
                arrowprops=dict(arrowstyle='-|>', color=K, lw=1.2), zorder=3)
    ax.annotate('', xy=(5.45, 2.05), xytext=(6.75, 2.05),
                arrowprops=dict(arrowstyle='-|>', color=K, lw=1.2,
                                connectionstyle='arc3,rad=0.45'), zorder=3)

    fig.savefig(os.path.join(OUT, 'fig2-4.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('fig2-4 done')


if __name__ == '__main__':
    fig2_1()
    fig2_2()
    fig2_3()
    fig2_4()
    print('ALL DONE ->', OUT)
