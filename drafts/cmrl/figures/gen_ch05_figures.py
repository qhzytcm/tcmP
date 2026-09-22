# -*- coding: utf-8 -*-
"""《中医场景强化学习》第5章 核心图生成脚本（图表工程师交付）

生成（4 幅，对应任务 1-3、5-6）：
  fig5-1 最优策略示意：网格世界各状态最优动作箭头（对 v* 贪婪）
  fig5-2 价值迭代扩散图：3x3 网格世界前三轮价值迭代（v0 -> v1 -> v2 -> v3，水波效应）
  fig5-3 策略迭代循环图：评估到底-改进到底（PDCA 风格循环）
  fig5-4 贪婪策略示意：当前最优选择 vs 全局最优（局部最优陷阱）

风格：参照第1章范式（figures/gen_ch01_figures.py）
  - SimHei / axes.unicode_minus=False
  - 图题-图体-图注结构（图题内嵌 PNG，图注由正文【图注】段承担）
  - 输出：drafts/cmrl/figures/ch05/*.png, dpi=200

数值一致性（与正文 5.1-5.6 及 chapter-05-figures.md 完全一致）：
  失眠链：v* = (8.1, 9, 10, 0)；q*(s2,归脾汤)=9；q*(s2,黄连解毒汤)=0；γ=0.9
  3x3 网格：s9 目标（到达后每步 +1）、s6 禁区（进入得 -1）、越界弹回 -1、其余 0、γ=0.9
    例5.4：v1(s9)=1；v2(s8)=0.9；v2(s6)=0.9（向下到 s9）；v3(s5)=0.81；v3(s7)=0.81
  例5.5/5.6 数值不在图中直接引用（图 5-2 使用例5.4 数值）
"""
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyBboxPatch, Circle, Polygon, Patch
from matplotlib.lines import Line2D

plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ch05')
os.makedirs(OUT, exist_ok=True)


def state_xy(s):
    """行优先编号 s1-s9 -> 格心坐标 (col, row)，row 0 在顶端（y 轴反置，同第1章）"""
    i = int(s[1:]) - 1
    return (i % 3, i // 3)


def box(ax, cx, cy, w, h, text, fc, ec, fs=9.5, lw=1.6, style='round,pad=0.06'):
    ax.add_patch(FancyBboxPatch((cx - w / 2, cy - h / 2), w, h,
                                boxstyle=style, facecolor=fc, edgecolor=ec, lw=lw, zorder=2))
    ax.text(cx, cy, text, ha='center', va='center', fontsize=fs,
            color='#1b2631', zorder=3, linespacing=1.5)


def arrow(ax, xy1, xy2, color='#1b2631', lw=2.0, ls='-', rad=0.0, zorder=3):
    ax.annotate('', xy=xy2, xytext=xy1,
                arrowprops=dict(arrowstyle='-|>', color=color, lw=lw,
                                linestyle=ls, connectionstyle=f'arc3,rad={rad}'),
                zorder=zorder)


# =====================================================================
# 图 5-1 最优策略示意（网格世界各状态最优动作箭头，目标格终点）
# =====================================================================
def fig5_1():
    fig, ax = plt.subplots(figsize=(7.8, 7.2))
    ax.set_xlim(-0.6, 2.6)
    ax.set_ylim(2.6, -0.6)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title('图 5-1 最优策略示意：网格世界各状态的最优动作（箭头）\n'
                 '对最优价值 $v^*$ 贪婪——每个状态选择动作价值最大的动作（定理5.1）\n'
                 '每格指向目标方向、绕开禁区 · s9 为终点（到达后每步 +1）',
                 fontsize=11)

    # 最优策略箭头（对 v* 贪婪；s1、s4 处"向下/向右"并列最优，图示取"向下"）
    OPT = {'s1': (0, 1), 's2': (0, 1), 's3': (-1, 0), 's4': (0, 1),
           's5': (0, 1), 's6': (0, 1), 's7': (1, 0), 's8': (1, 0)}
    for s in ['s1', 's2', 's3', 's4', 's5', 's6', 's7', 's8', 's9']:
        col, row = state_xy(s)
        fc = '#f5b041' if s == 's6' else ('#82e0aa' if s == 's9' else 'white')
        ax.add_patch(Rectangle((col - 0.5, row - 0.5), 1, 1, facecolor=fc,
                               edgecolor='#999999', lw=1.2, zorder=1))
        # 编号（左上）
        ax.text(col - 0.20, row - 0.20, s, ha='center', va='center',
                fontsize=10, fontweight='bold', color='#566573', zorder=3)
        if s == 's9':
            ax.text(col, row - 0.10, '终', ha='center', va='center',
                    fontsize=20, fontweight='bold', color='#1e8449', zorder=3)
            ax.text(col, row + 0.30, '目标：每步 +1', ha='center', va='center',
                    fontsize=7, color='#1e8449', zorder=3)
        elif s == 's6':
            ax.text(col, row + 0.30, '禁区：进入 -1', ha='center', va='center',
                    fontsize=7, color='#b03a2e', zorder=3)
        # 最优动作箭头（格心沿动作方向；s9 为目标终点，无动作）
        if s in OPT:
            dx, dy = OPT[s]
            ax.annotate('', xy=(col + 0.32 * dx, row + 0.32 * dy),
                        xytext=(col - 0.18 * dx, row - 0.18 * dy),
                        arrowprops=dict(arrowstyle='-|>', color='#1e8449',
                                        lw=2.8, mutation_scale=20), zorder=4)

    # 越界弹回：四周边框加粗
    for (x0, y0, x1, y1) in [(-0.5, -0.5, 2.5, -0.5), (-0.5, 2.5, 2.5, 2.5),
                             (-0.5, -0.5, -0.5, 2.5), (2.5, -0.5, 2.5, 2.5)]:
        ax.plot([x0, x1], [y0, y1], color='#333333', lw=3.2,
                solid_capstyle='butt', zorder=2)

    handles = [
        Patch(facecolor='white', edgecolor='#999999', label='普通格：可自由进入，r = 0'),
        Patch(facecolor='#f5b041', edgecolor='#999999', label='禁区（s6）：进入得 r = -1'),
        Patch(facecolor='#82e0aa', edgecolor='#999999', label='目标（s9）：到达后每步 +1'),
        Line2D([0], [0], color='#333333', lw=3.2, label='越界弹回：r = -1'),
        Line2D([0], [0], color='#1e8449', lw=2.8, label='最优动作（对 v* 贪婪）'),
    ]
    ax.legend(handles=handles, loc='lower center', bbox_to_anchor=(0.5, -0.16),
              ncol=2, fontsize=8.6, frameon=True, handlelength=2.0)
    fig.text(0.5, 0.015,
             '动作：上 a1 右 a2 下 a3 左 a4 静止 a5 · s1、s4 处"向下"与"向右"并列最优，'
             '图示取"向下"（最优策略可以不唯一，5.1.2）',
             ha='center', fontsize=8.5, color='#566573')
    fig.subplots_adjust(bottom=0.10)
    fig.savefig(os.path.join(OUT, 'fig5-1.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('fig5-1 done')


# =====================================================================
# 图 5-2 价值迭代扩散图（v0 -> v1 -> v2 -> v3，水波效应；例5.4 配套）
# =====================================================================
def fig5_2():
    rounds = [
        ('v0 初值（全 0）', '初值 $v_0 = 0$', {}),
        ('第 1 轮 v1', '$v_1(s_9) = 1$（到达目标）', {'s9': 1}),
        ('第 2 轮 v2', '$v_2(s_8) = 0 + 0.9\\times1 = 0.9$（向右到 s9）\n'
                       '$v_2(s_6) = 0 + 0.9\\times1 = 0.9$（向下到 s9）', {'s8': 0.9, 's6': 0.9, 's9': 1}),
        ('第 3 轮 v3', '$v_3(s_5) = 0.9\\times v_2(s_8) = 0.81$（向下到 s8）\n'
                       '$v_3(s_7) = 0.9\\times v_2(s_8) = 0.81$（向右到 s8）',
         {'s5': 0.81, 's7': 0.81, 's8': 0.9, 's6': 0.9, 's9': 1}),
    ]
    fig, axes = plt.subplots(1, 4, figsize=(15.0, 5.6))
    fig.suptitle('图 5-2 价值如水波扩散：3×3 网格世界前三轮价值迭代（v0 → v1 → v2 → v3）\n'
                 '每轮 $v_{k+1}(s) = \\max_a q_k(s,a)$，q 一律用上轮价值 $v_k$ 计算（同步更新）',
                 fontsize=12.5, y=0.99)
    for ax, (title, note, vals) in zip(axes, rounds):
        ax.set_xlim(-0.9, 2.9)
        ax.set_ylim(3.3, -0.9)
        ax.set_aspect('equal')
        ax.axis('off')
        ax.set_title(title, fontsize=10.5)
        # 同心弧线：以目标格 s9 为中心的扩散圈（示意）
        if title != 'v0 初值（全 0）':
            for r, al in [(1.0, 0.55), (2.0, 0.32)]:
                ax.add_patch(Circle((2, 2), r, fill=False, ls='--',
                                    ec='#2874a6', lw=1.1, alpha=al, zorder=2))
        for s in ['s1', 's2', 's3', 's4', 's5', 's6', 's7', 's8', 's9']:
            col, row = state_xy(s)
            v = vals.get(s, 0.0)
            if s == 's9':
                fc = '#82e0aa'
            elif s == 's6':
                fc = '#fdebd0'
            else:
                fc = '#eafaf1' if v > 0 else 'white'
            ax.add_patch(Rectangle((col - 0.5, row - 0.5), 1, 1, facecolor=fc,
                                   edgecolor='#999999', lw=1.1, zorder=1))
            if s == 's9':
                ax.text(col - 0.22, row - 0.20, '终', ha='center', va='center',
                        fontsize=7.5, color='#1e8449', zorder=3)
            elif s == 's6':
                ax.text(col - 0.26, row - 0.18, '禁区', ha='center', va='center',
                        fontsize=6, color='#b03a2e', zorder=3)
            txt = ('1' if v == 1.0 else ('%.2f' % v).rstrip('0').rstrip('.') if v else '0')
            ax.text(col, row + 0.03, txt, ha='center', va='center',
                    fontsize=13 if v > 0 else 11,
                    fontweight='bold' if v > 0 else 'normal',
                    color='#1e8449' if v > 0 else '#b3b6b7', zorder=3)
        ax.text(1.0, 2.92, note, ha='center', va='center', fontsize=7.6,
                color='#1a5276', zorder=3, linespacing=1.45)
    fig.text(0.5, 0.035,
             '同心虚线弧：以目标格 s9 为中心的扩散圈（示意）——第 1 圈经 s8、s6，第 2 圈经 s5、s7、s3；'
             '价值逐圈外扩、每外扩一圈乘 $\\gamma = 0.9$，价值来自未来。'
             '目标格 s9 自身价值随轮次累积（1 → 1.9 → 2.71 → … → 10），图中统一标注其单步奖励 1。',
             ha='center', fontsize=8.8, color='#566573')
    fig.subplots_adjust(left=0.02, right=0.98, top=0.82, bottom=0.12, wspace=0.14)
    fig.savefig(os.path.join(OUT, 'fig5-2.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('fig5-2 done')


# =====================================================================
# 图 5-3 策略迭代循环图（评估到底-改进到底，PDCA 风格循环）
# =====================================================================
def fig5_3():
    fig, ax = plt.subplots(figsize=(10.8, 9.4))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 11)
    ax.set_aspect('equal')
    ax.axis('off')
    fig.suptitle('图 5-3 策略迭代：评估到底、改进到底，有限步到达最优\n'
                 '"评估"与"改进"各自做到位再交替：评估（解方程组）→ 改进（贪婪更新）→ 再评估 → ……',
                 fontsize=12, y=0.965)

    # PDCA 带（顶部）
    box(ax, 5.7, 10.55, 10.4, 0.78,
        '对应 PDCA：计划（定策略）→ 执行（走流程）→ 检查（评估价值）→ 改进（贪婪更新）——循环不止，质量渐优',
        '#fef9e7', '#b7950b', fs=9.2)

    # 主循环
    box(ax, 4.2, 9.55, 4.2, 0.95, '① 初始化：任取策略 $\\pi_0$\n（如全部取第一个动作）',
        '#eaf2f8', '#1f618d', fs=9.2)
    box(ax, 4.2, 7.15, 4.7, 1.8,
        '② 策略评估：评估到底\n解线性方程组 $v_{\\pi_k} = (I - \\gamma P_{\\pi_k})^{-1} r_{\\pi_k}$\n'
        '（$\\gamma < 1$ 且 $P_{\\pi_k}$ 为随机矩阵，故 $I - \\gamma P_{\\pi_k}$ 可逆）',
        '#eaf2f8', '#1f618d', fs=9.0)
    box(ax, 4.2, 4.3, 4.7, 1.8,
        '③ 策略改进：贪婪更新\n$\\pi_{k+1}(s) = \\mathrm{arg\\,max}_a [\\, r(s,a) + \\gamma \\sum_{s^{\\prime}} p(s^{\\prime}|s,a)\\, v_{\\pi_k}(s^{\\prime}) \\,]$',
        '#eaf2f8', '#1f618d', fs=9.0)
    # 判断（菱形）
    dia = Polygon([(2.5, 1.9), (4.2, 2.95), (5.9, 1.9), (4.2, 0.85)],
                  closed=True, facecolor='#fef9e7', edgecolor='#b7950b', lw=1.8, zorder=2)
    ax.add_patch(dia)
    ax.text(4.2, 1.9, '④ 判断：$\\pi_{k+1}(s) = \\pi_k(s)$\n对一切 $s$ 成立？',
            ha='center', va='center', fontsize=9.3, zorder=3, linespacing=1.4)
    # 输出（终止）
    box(ax, 8.7, 1.9, 3.0, 1.05, '是 → 输出最优策略 $\\pi_k$\n（终止）', '#d5f5e3', '#1e8449', fs=9.3)

    # 主箭头
    arrow(ax, (4.2, 9.05), (4.2, 8.05))
    arrow(ax, (4.2, 6.25), (4.2, 5.2))
    arrow(ax, (4.2, 3.4), (4.2, 2.95))
    # 判断 -> 输出（是）
    arrow(ax, (5.9, 1.9), (7.2, 1.9), color='#1e8449', lw=2.2)
    ax.text(6.55, 2.12, '是', ha='center', fontsize=9.5, color='#1e8449', fontweight='bold')
    # 判断 -> 策略评估（否，回环）
    arrow(ax, (3.5, 0.85), (1.9, 6.4), color='#c0392b', lw=2.0, rad=0.62)
    ax.text(1.15, 3.85, '否：回到策略评估\n（评估到底再改进）', ha='center', fontsize=8.4,
            color='#c0392b', linespacing=1.4)

    # 右侧性质徽章
    badges = [
        (9.0, '定理5.2：策略改进后价值单调不降（$v_{\\pi_{k+1}}$ ≥ $v_{\\pi_k}$）'),
        (7.95, '定理5.3：有限步终止（确定性策略总数 ≤ $|A|^{|S|}$）'),
        (6.9, '评估也可用迭代法：截断策略迭代（评估 j 步，j=1 即价值迭代）'),
        (5.6, '临床对照：医师交付的是"见什么证、用什么方"的决策规则——\n策略是迭代的主角，疗效估计只是支撑规则的账本'),
    ]
    for y, t in badges:
        box(ax, 9.4, y, 4.7, 0.9, t, '#f4f6f7', '#85929e', fs=8.2)

    fig.text(0.5, 0.012,
             '与价值迭代对照：价值迭代"评估一步一改进"（5.4 节），策略迭代"评估到底再改进"（5.5 节）；'
             '两算法在小规模问题上解出同一最优价值与最优策略，结果一致性可作实现正确性的交叉验证（5.4.3）',
             ha='center', fontsize=8.6, color='#566573')
    fig.subplots_adjust(bottom=0.05, top=0.90)
    fig.savefig(os.path.join(OUT, 'fig5-3.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('fig5-3 done')


# =====================================================================
# 图 5-4 贪婪策略示意（当前最优选择 vs 全局最优，局部最优陷阱）
# =====================================================================
def fig5_4():
    fig, ax = plt.subplots(figsize=(12.4, 7.8))
    ax.set_xlim(0, 12.4)
    ax.set_ylim(0, 8.3)
    ax.set_aspect('equal')
    ax.axis('off')
    fig.suptitle('图 5-4 贪婪策略示意：贪的是长期价值，不婪的是眼前甜头\n'
                 '同一状态 s2 的两种选择——只看即时（眼前甜头）会落入局部最优陷阱；'
                 '看长期价值（对 $q^*$ 贪婪）才达全局最优',
                 fontsize=12, y=0.975)

    # 状态框
    box(ax, 6.2, 7.25, 3.8, 0.95, '状态 s2：心脾两虚证', '#d6eaf8', '#1f618d', fs=11)

    # 左栏：见利忘义（局部最优陷阱）
    box(ax, 3.1, 5.35, 3.6, 1.7, '动作：黄连解毒汤\n即时缓解（眼前甜头大）\nr = 0',
        '#f2f3f4', '#7f8c8d', fs=9.2)
    box(ax, 3.1, 3.45, 3.6, 1.35, '后继：s4 迁延难愈\n$v^*(s_4) = 0$（每步 0）',
        '#fdebd0', '#c0392b', fs=9.5)
    ax.text(3.1, 2.28, '$q^*(s_2,$黄连解毒汤$) = 0 + 0.9\\times0 = 0$',
            ha='center', va='center', fontsize=9, color='#c0392b', fontweight='bold', zorder=3)
    box(ax, 3.1, 1.35, 4.0, 0.85, '见利忘义：即时最大 ≠ 价值最大\n（局部最优陷阱）',
        '#fdebd0', '#c0392b', fs=8.6)
    arrow(ax, (6.2, 6.75), (3.1, 6.25), color='#7f8c8d', lw=2.0)
    arrow(ax, (3.1, 4.5), (3.1, 4.15), color='#7f8c8d', lw=2.0)

    # 右栏：贪而不婪（全局最优）
    box(ax, 9.3, 5.35, 3.6, 1.7, '动作：归脾汤\n当下平淡（无即时甜头）\nr = 0',
        '#d5f5e3', '#1e8449', fs=9.2)
    box(ax, 9.3, 3.45, 3.6, 1.35, '后继：s3 康复吸收态\n$v^*(s_3) = 10$（每步 +1）',
        '#a9dfbf', '#1e8449', fs=9.5)
    ax.text(9.3, 2.28, '$q^*(s_2,$归脾汤$) = 0 + 0.9\\times10 = 9$',
            ha='center', va='center', fontsize=9, color='#1e8449', fontweight='bold', zorder=3)
    box(ax, 9.3, 1.35, 4.0, 0.85, '贪而不婪：贪婪选择 = 长期最优\n（对 $q^*$ 贪婪 → 全局最优）',
        '#d5f5e3', '#1e8449', fs=8.6)
    arrow(ax, (6.2, 6.75), (9.3, 6.25), color='#1e8449', lw=2.0)
    arrow(ax, (9.3, 4.5), (9.3, 4.15), color='#1e8449', lw=2.0)

    # 底部定理条
    box(ax, 6.2, 0.42, 11.6, 0.82,
        '定理5.1：对 $v^*$ 贪婪的 $\\pi$ 是最优策略，且 $v_\\pi = v^*$ —— 先有账本，后有选择；'
        '价值错一分，贪婪偏一里（5.3.2）。数值与正文 5.1.2 一致：$v^* = (8.1, 9, 10, 0)$，'
        '两动作即时奖励皆为 0，差别全在远期。',
        '#fef9e7', '#b7950b', fs=9.0)

    fig.subplots_adjust(top=0.90, bottom=0.03)
    fig.savefig(os.path.join(OUT, 'fig5-4.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('fig5-4 done')


if __name__ == '__main__':
    fig5_1()
    fig5_2()
    fig5_3()
    fig5_4()
    print('ALL DONE ->', OUT)
