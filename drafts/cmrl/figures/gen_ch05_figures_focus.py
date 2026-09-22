# -*- coding: utf-8 -*-
"""《中医场景强化学习》第5章 核心图生成脚本（v2 聚焦重绘版，图表工程师交付）

聚焦原则（与 ch01 图 1-1 v3 / gen_ch01_figures_focus.py 同一范式）：
  · 图体只保留'能代表含义的图段'：收紧 figsize 与 xlim/ylim，突出关键区域；
  · 图题由 Excel 图题行承担（居中黑体），图内不再重复"图 5-X"大标题；
  · 图注四要素（对接正文提示语 / 线的注释 / 符号的注释 / 代表含义的指针图段）
    由 Excel 图注行 + 正文 md 图注段承担。
  · SimHei / axes.unicode_minus=False / dpi=200。

真实世界映射（用户新要求，仅含网格/路径的 3 幅必须映射）：
  fig5-1 最优策略、fig5-2 价值水波扩散、fig5-4 贪婪策略 →
  医院垂直切面范式（同 ch01 图 1-1 v3）：
    中间列 s2/s5/s8 = 垂直交通核（电梯/楼梯），上下楼在此移动；
    左右两列 = 左手侧/右手侧诊室房间，从走廊进入；每层一条水平走廊；
    s6 = 2 层右手侧禁区（手术区/设备间，患者不可进入，进入得 -1）；
    s9 = 3 层右手侧第 2 个窗口（专家门诊：敲门进入或候诊叫号，到达后每步 +1）；
    患者沿走廊行走 + 电梯/楼梯上下楼 + 左手侧或右手侧第 N 个诊室窗口，
    绝不穿越科室房间。

数值一致性（与正文 5.1-5.6 及 chapter-05-figures.md 完全一致）：
  失眠链：v* = (8.1, 9, 10, 0)；q*(s2, 归脾汤)=9；q*(s2, 黄连解毒汤)=0；γ=0.9
  3x3 网格：s9 目标（到达后每步 +1）、s6 禁区（进入得 -1）、越界弹回 -1、其余 0、γ=0.9
    例5.4：v1(s9)=1；v2(s8)=0.9；v2(s6)=0.9（向下到 s9）；v3(s5)=0.81；v3(s7)=0.81
  输出：drafts/cmrl/figures/ch05/fig5-1.png ~ fig5-5.png（覆盖既有文件）
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
# 医院垂直切面共用绘制（fig5-1 / fig5-2 共用；范式同 ch01 图 1-1 v3）
# 中间列 s2/s5/s8 = 电梯核；左右两列 = 诊室房间；s6 禁区（手术区）；s9 目标（专家门诊）
# =====================================================================
ROOMS = {
    's1': '大厅·挂号处', 's3': '内科诊室', 's4': '针灸科',
    's6': '手术区', 's7': '检验科', 's9': '专家门诊',
}
SIDES = {'s1': '左手侧', 's3': '右手侧', 's4': '左手侧',
         's6': '右手侧', 's7': '左手侧', 's9': '右手侧'}


def hospital_shell(ax, floor_labels=True):
    """医院外轮廓 + 两道楼板 + 楼层标签（1层/2层/3层 于左侧）"""
    for (x0, y0, x1, y1) in [(-0.5, -0.5, 2.5, -0.5), (-0.5, 2.5, 2.5, 2.5),
                             (-0.5, -0.5, -0.5, 2.5), (2.5, -0.5, 2.5, 2.5)]:
        ax.plot([x0, x1], [y0, y1], color='#333333', lw=3.0,
                solid_capstyle='butt', zorder=2)
    for y in [0.5, 1.5]:   # 中间两道楼板
        ax.plot([-0.5, 2.5], [y, y], color='#5d6d7e', lw=2.2,
                solid_capstyle='butt', zorder=2)
    if floor_labels:
        for row, name in {0: '1层', 1: '2层', 2: '3层'}.items():
            ax.text(-1.00, row, name, ha='center', va='center',
                    fontsize=10.5, fontweight='bold', color='#34495e', zorder=5)


def hospital_elevator_core(ax, s_label=True, small=False):
    """中间列垂直交通核 s2/s5/s8（浅灰底 + 电梯井虚线边界 + 电梯↑）"""
    for s in ['s2', 's5', 's8']:
        col, row = state_xy(s)
        ax.add_patch(Rectangle((col - 0.5, row - 0.5), 1, 1, facecolor='#eaecee',
                               edgecolor='#85929e', lw=1.5, zorder=1))
        if s_label:
            ax.text(col - 0.34, row + 0.33, s, ha='center', va='center',
                    fontsize=8 if not small else 6.5, fontweight='bold',
                    color='#566573', zorder=3)
        ax.text(col, row + 0.12, '走廊', ha='center', va='center',
                fontsize=8.2 if not small else 5.8, color='#7f8c8d', zorder=3)
        ax.text(col, row - 0.24, '电梯↑', ha='center', va='center',
                fontsize=9 if not small else 6.5, color='#1a5276',
                fontweight='bold', zorder=3)
    for x in [0.5, 1.5]:
        ax.plot([x, x], [-0.5, 2.5], color='#85929e', lw=1.3,
                linestyle=(0, (3, 2)), zorder=2)


def hospital_rooms(ax, small=False, room_shift=0.0):
    """左右两列诊室房间（s6 禁区橙 / s9 目标绿），门朝走廊"""
    for s in ['s1', 's3', 's4', 's6', 's7', 's9']:
        col, row = state_xy(s)
        if s == 's6':
            fc = '#f5b041'
        elif s == 's9':
            fc = '#82e0aa'
        else:
            fc = 'white'
        ax.add_patch(Rectangle((col - 0.5, row - 0.5), 1, 1, facecolor=fc,
                               edgecolor='#999999', lw=1.1, zorder=1))
        fs_id = 9.5 if not small else 7.0
        fs_rm = 8.6 if not small else 6.0
        ax.text(col - 0.33, row + 0.33, s, ha='center', va='center',
                fontsize=fs_id, fontweight='bold', color='#2c3e50', zorder=3)
        ax.text(col, row + room_shift, ROOMS[s], ha='center', va='center',
                fontsize=fs_rm, color='#444444', zorder=3)
        if s in ('s6', 's9'):
            label = '禁区 r = -1' if s == 's6' else '目标 r = +1'
            color = '#b03a2e' if s == 's6' else '#1e8449'
            ax.text(col, row - 0.36, label, ha='center', va='center',
                    fontsize=7.2 if not small else 5.4, color=color,
                    fontweight='bold', zorder=3)
        else:
            ax.text(col, row - 0.36, SIDES[s], ha='center', va='center',
                    fontsize=6.8 if not small else 5.2, color='#7f8c8d', zorder=3)
        # 门：朝走廊（中间列）一边
        dx = 0.5 if col == 0 else -0.5
        ax.plot([col + dx, col + dx], [row - 0.10, row + 0.10],
                color='#5d6d7e', lw=1.8, zorder=3)


# =====================================================================
# 图 5-1 最优策略（医院垂直切面版：沿走廊+电梯，不穿科室；对 v* 贪婪）
# 最优动作（医院移动语义）：s1→s2 走廊 / s2↓乘电梯 / s3←走廊 / s4→s5 走廊 /
#   s5↓乘电梯 / s6←绕开手术区 / s7→s8 走廊 / s8→s9 走廊（右手侧第2窗口）/ s9 终
# 抽象网格中 s1、s4 处"向下"与"向右"并列最优（正文图示取"向下"）；
# 医院映射下"向右"=沿走廊到电梯核、"向下"=乘电梯上行，二者等价（图注说明）。
# =====================================================================
def fig5_1():
    fig, ax = plt.subplots(figsize=(7.4, 6.7))
    ax.set_xlim(-1.55, 3.55)     # 聚焦：网格 + 左侧楼层标签 + 右侧指针标注
    ax.set_ylim(2.95, -0.95)
    ax.set_aspect('equal')
    ax.axis('off')

    hospital_shell(ax)
    hospital_elevator_core(ax)
    hospital_rooms(ax)

    # 最优策略箭头（对 v* 贪婪；医院移动语义，绿）
    OPT_H = {
        's1': (1, 0), 's2': (0, 1), 's3': (-1, 0), 's4': (1, 0),
        's5': (0, 1), 's6': (-1, 0), 's7': (1, 0), 's8': (1, 0),
    }
    for s, (dx, dy) in OPT_H.items():
        col, row = state_xy(s)
        ax.annotate('', xy=(col + 0.30 * dx, row + 0.30 * dy),
                    xytext=(col - 0.22 * dx, row - 0.22 * dy),
                    arrowprops=dict(arrowstyle='-|>', color='#1e8449',
                                    lw=2.8, mutation_scale=20), zorder=4)
    # s9 目标终点
    ax.text(2, 1.9, '终', ha='center', va='center', fontsize=19,
            fontweight='bold', color='#1e8449', zorder=4)

    # 指针图段：示例最优路径（蓝色虚线，沿走廊+电梯：s1→s2→s5→s8→s9）
    for (a, b) in [('s1', 's2'), ('s2', 's5'), ('s5', 's8'), ('s8', 's9')]:
        x1, y1 = state_xy(a)
        x2, y2 = state_xy(b)
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle='-|>', color='#1a5276', lw=2.2,
                                    linestyle=(0, (4, 2))), zorder=4)
    for yy in [0.30, 1.30]:
        ax.text(1.42, yy, '乘电梯↑', ha='left', va='center',
                fontsize=7.2, color='#1a5276', fontweight='bold', zorder=5)

    # 指针标注（右侧）：右手侧第2窗口 / 敲门进入或候诊叫号 / 患者不可进入
    ax.annotate('右手侧第2窗口', xy=(2.44, 2.08), xytext=(2.62, 2.40),
                arrowprops=dict(arrowstyle='->', color='#1e8449', lw=1.2),
                ha='center', va='center', fontsize=7.8, color='#1e8449',
                fontweight='bold', zorder=4)
    ax.text(2.05, 1.52, '敲门进入/\n候诊叫号', ha='center', va='center',
            fontsize=6.6, color='#145a32', linespacing=1.3, zorder=4)
    ax.annotate('患者不可进入', xy=(2, 0.56), xytext=(2.15, 0.36),
                arrowprops=dict(arrowstyle='->', color='#b03a2e', lw=1.2),
                ha='center', va='center', fontsize=7.2, color='#b03a2e', zorder=4)

    handles = [
        Patch(facecolor='white', edgecolor='#999999', label='诊室房间：可进入，r = 0'),
        Patch(facecolor='#eaecee', edgecolor='#85929e', label='电梯核（走廊+电梯）'),
        Patch(facecolor='#f5b041', edgecolor='#999999', label='禁区（手术区）：r = -1'),
        Patch(facecolor='#82e0aa', edgecolor='#999999', label='目标（专家门诊）：r = +1'),
        Line2D([0], [0], color='#1e8449', lw=2.8, label='最优动作（对 $v^*$ 贪婪）'),
        Line2D([0], [0], color='#1a5276', lw=2.2, linestyle=(0, (4, 2)),
               label='示例最优路径：沿走廊+乘电梯'),
        Line2D([0], [0], color='#333333', lw=3.0, label='越界弹回：r = -1'),
    ]
    ax.legend(handles=handles, loc='lower center', bbox_to_anchor=(0.5, -0.13),
              ncol=2, fontsize=7.4, frameon=True, handlelength=1.6)
    fig.subplots_adjust(bottom=0.10)
    fig.savefig(os.path.join(OUT, 'fig5-1.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('fig5-1 done')


# =====================================================================
# 图 5-2 价值如水波扩散（医院垂直切面版：价值从专家门诊沿走廊+电梯逐圈外扩）
# 例5.4 配套：v0=0 -> v1(s9)=1 -> v2(s8)=0.9, v2(s6)=0.9 -> v3(s5)=0.81, v3(s7)=0.81
# 同心虚线弧 = 价值扩散圈（以目标格 s9 为中心的抽象示意）；走廊/电梯为可通行通路。
# =====================================================================
def fig5_2():
    rounds = [
        ('v0 初值（全 0）', '初值 $v_0 = 0$', {}),
        ('第 1 轮 v1', '$v_1(s_9) = 1$（到达目标）', {'s9': 1}),
        ('第 2 轮 v2', '$v_2(s_8) = 0.9$（沿走廊到 s9）\n$v_2(s_6) = 0.9$（乘电梯向下到 s9）',
         {'s8': 0.9, 's6': 0.9, 's9': 1}),
        ('第 3 轮 v3', '$v_3(s_5) = 0.81$（乘电梯向下到 s8）\n$v_3(s_7) = 0.81$（沿走廊到 s8）',
         {'s5': 0.81, 's7': 0.81, 's8': 0.9, 's6': 0.9, 's9': 1}),
    ]
    fig, axes = plt.subplots(1, 4, figsize=(13.8, 4.7))
    for ax, (title, note, vals) in zip(axes, rounds):
        ax.set_xlim(-1.25, 2.85)   # 聚焦：网格 + 左侧楼层标签 + 顶部注释
        ax.set_ylim(3.05, -0.85)
        ax.set_aspect('equal')
        ax.axis('off')
        ax.set_title(title, fontsize=10.0)
        # 同心弧线：以目标格 s9 为中心的扩散圈（抽象示意，价值传播可沿走廊+电梯）
        if title != 'v0 初值（全 0）':
            for r, al in [(1.0, 0.5), (2.0, 0.28)]:
                ax.add_patch(Circle((2, 2), r, fill=False, ls='--',
                                    ec='#2874a6', lw=1.0, alpha=al, zorder=2))
        # 医院切面（小字号版：只标电梯核与目标/禁区，价值数字为主角）
        for s in ['s2', 's5', 's8']:
            col, row = state_xy(s)
            ax.add_patch(Rectangle((col - 0.5, row - 0.5), 1, 1, facecolor='#eaecee',
                                   edgecolor='#85929e', lw=1.2, zorder=1))
            ax.text(col, row + 0.14, '电梯↑', ha='center', va='center',
                    fontsize=6.0, color='#1a5276', fontweight='bold', zorder=3)
        for s in ['s1', 's3', 's4', 's6', 's7', 's9']:
            col, row = state_xy(s)
            if s == 's6':
                fc = '#fdebd0'
            elif s == 's9':
                fc = '#82e0aa'
            else:
                fc = '#eafaf1' if vals.get(s, 0) > 0 else 'white'
            ax.add_patch(Rectangle((col - 0.5, row - 0.5), 1, 1, facecolor=fc,
                                   edgecolor='#999999', lw=1.0, zorder=1))
            if s == 's6':
                ax.text(col, row - 0.30, '手术区', ha='center', va='center',
                        fontsize=5.4, color='#b03a2e', zorder=3)
            elif s == 's9':
                ax.text(col, row - 0.30, '专家门诊', ha='center', va='center',
                        fontsize=5.4, color='#1e8449', zorder=3)
            v = vals.get(s, 0.0)
            txt = ('1' if v == 1.0 else ('%.2f' % v).rstrip('0').rstrip('.') if v else '0')
            ax.text(col, row + 0.06, txt, ha='center', va='center',
                    fontsize=12.5 if v > 0 else 10.5,
                    fontweight='bold' if v > 0 else 'normal',
                    color='#1e8449' if v > 0 else '#b3b6b7', zorder=3)
        ax.text(0.8, 2.94, note, ha='center', va='center', fontsize=7.4,
                color='#1a5276', zorder=3, linespacing=1.4)
    fig.subplots_adjust(left=0.015, right=0.985, top=0.88, bottom=0.04, wspace=0.10)
    fig.savefig(os.path.join(OUT, 'fig5-2.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('fig5-2 done')


# =====================================================================
# 图 5-3 策略迭代循环（聚焦：主循环 + 两条性质徽章；PDCA 对照移入图注）
# ① 初始化 π0 -> ② 策略评估（解方程组，评估到底）-> ③ 策略改进（贪婪更新）
# -> ④ 判断 πk+1=πk：是 -> 输出最优策略；否 -> 回到②
# =====================================================================
def fig5_3():
    fig, ax = plt.subplots(figsize=(9.8, 7.6))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 11)
    ax.set_aspect('equal')
    ax.axis('off')

    # 主循环
    box(ax, 4.2, 9.75, 4.2, 0.95, '① 初始化：任取策略 $\\pi_0$\n（如全部取第一个动作）',
        '#eaf2f8', '#1f618d', fs=9.2)
    box(ax, 4.2, 7.35, 4.7, 1.8,
        '② 策略评估：评估到底\n解线性方程组 $v_{\\pi_k} = (I - \\gamma P_{\\pi_k})^{-1} r_{\\pi_k}$\n'
        '（$\\gamma < 1$ 且 $P_{\\pi_k}$ 为随机矩阵，故 $I - \\gamma P_{\\pi_k}$ 可逆）',
        '#eaf2f8', '#1f618d', fs=9.0)
    box(ax, 4.2, 4.5, 4.7, 1.8,
        '③ 策略改进：贪婪更新\n$\\pi_{k+1}(s) = \\mathrm{arg\\,max}_a [\\, r(s,a) + \\gamma \\sum_{s^{\\prime}} p(s^{\\prime}|s,a)\\, v_{\\pi_k}(s^{\\prime}) \\,]$',
        '#eaf2f8', '#1f618d', fs=9.0)
    # 判断（菱形）
    dia = Polygon([(2.5, 1.85), (4.2, 2.9), (5.9, 1.85), (4.2, 0.8)],
                  closed=True, facecolor='#fef9e7', edgecolor='#b7950b', lw=1.8, zorder=2)
    ax.add_patch(dia)
    ax.text(4.2, 1.85, '④ 判断：$\\pi_{k+1}(s) = \\pi_k(s)$\n对一切 $s$ 成立？',
            ha='center', va='center', fontsize=9.3, zorder=3, linespacing=1.4)
    # 输出（终止）
    box(ax, 8.7, 1.85, 3.1, 1.05, '是 → 输出最优策略 $\\pi_k$\n（终止）',
        '#d5f5e3', '#1e8449', fs=9.3)

    # 主箭头
    arrow(ax, (4.2, 9.25), (4.2, 8.25))
    arrow(ax, (4.2, 6.45), (4.2, 5.4))
    arrow(ax, (4.2, 3.6), (4.2, 2.9))
    # 判断 -> 输出（是）
    arrow(ax, (5.9, 1.85), (7.1, 1.85), color='#1e8449', lw=2.2)
    ax.text(6.5, 2.08, '是', ha='center', fontsize=9.5, color='#1e8449', fontweight='bold')
    # 判断 -> 策略评估（否，回环）
    arrow(ax, (3.5, 0.8), (1.85, 6.4), color='#c0392b', lw=2.0, rad=0.62)
    ax.text(1.05, 3.6, '否：回到②再评估\n（评估到底再改进）', ha='center', fontsize=8.4,
            color='#c0392b', linespacing=1.4)

    # 右侧性质徽章（聚焦：两条定理 + 一句临床对照）
    badges = [
        (8.6, '定理5.2：策略改进后价值单调不降\n（$v_{\\pi_{k+1}} \\geq v_{\\pi_k}$，改进不倒退）'),
        (7.0, '定理5.3：有限步终止\n（确定性策略总数 $\\leq |A|^{|S|}$）'),
        (5.2, '临床对照：医师交付的是"见什么证、用什么方"的\n决策规则——策略是迭代的主角，疗效估计只是账本'),
    ]
    for y, t in badges:
        box(ax, 9.6, y, 4.5, 1.15, t, '#f4f6f7', '#85929e', fs=8.2)

    # 底部一行对照（聚焦核心差异）
    box(ax, 4.6, 0.35, 8.6, 0.62,
        '与价值迭代对照：价值迭代"评估一步一改进"（5.4 节）vs 策略迭代"评估到底再改进"（5.5 节）——火候不同，殊途同归',
        '#fef9e7', '#b7950b', fs=8.4)

    fig.subplots_adjust(top=0.98, bottom=0.02)
    fig.savefig(os.path.join(OUT, 'fig5-3.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('fig5-3 done')


# =====================================================================
# 图 5-4 贪婪策略（医院走廊版：s2 诊室出发，走廊分岔到两个窗口）
# 左栏见利忘义：黄连解毒汤 -> 左手侧窗口 s4（迁延随访，v*=0）-> q* = 0（局部最优陷阱）
# 右栏贪而不婪：归脾汤 -> 右手侧窗口 s3（康复窗口，v*=10）-> q* = 9（全局最优）
# 患者沿走廊行走、敲门进入/候诊叫号，绝不穿越科室房间。
# =====================================================================
def fig5_4():
    fig, ax = plt.subplots(figsize=(11.2, 6.4))
    ax.set_xlim(0, 12.4)
    ax.set_ylim(0, 7.6)
    ax.set_aspect('equal')
    ax.axis('off')

    # 中央：s2 诊室（患者当前位置）
    box(ax, 6.2, 6.6, 3.6, 0.95, 's2 心脾两虚证（诊室）\n患者在此选择下一步走向', '#d6eaf8', '#1f618d', fs=9.8)

    # 走廊（水平通道：从诊室通向两侧窗口）
    ax.plot([0.6, 11.8], [4.6, 4.6], color='#5d6d7e', lw=3.0,
            solid_capstyle='butt', zorder=1)
    ax.text(6.2, 5.05, '走廊：患者沿走廊行走，绝不穿越科室房间', ha='center', va='center',
            fontsize=8.6, color='#34495e', zorder=3)

    # 左栏：见利忘义（局部最优陷阱）
    box(ax, 3.1, 3.55, 3.7, 1.15, '动作：黄连解毒汤\n即时缓解（眼前甜头大）', '#f2f3f4', '#7f8c8d', fs=9.0)
    ax.add_patch(Rectangle((1.3, 0.7), 3.6, 1.5, facecolor='#fdebd0',
                           edgecolor='#c0392b', lw=1.8, zorder=2))
    ax.text(3.1, 1.75, 's4 迁延难愈（左手侧窗口）\n$v^*(s_4) = 0$（每步 0）', ha='center', va='center',
            fontsize=9.0, color='#7b241c', zorder=3, linespacing=1.4)
    ax.text(1.9, 2.6, '左手侧第1窗口', ha='center', va='center', fontsize=7.0,
            color='#7f8c8d', zorder=3)
    ax.text(3.1, 0.28, '$q^*(s_2,$黄连解毒汤$) = 0 + 0.9\\times 0 = 0$',
            ha='center', va='center', fontsize=9.0, color='#c0392b', fontweight='bold', zorder=3)
    ax.text(3.1, 5.5, '见利忘义：即时最大 ≠ 价值最大\n（局部最优陷阱）', ha='center', va='center',
            fontsize=8.6, color='#c0392b', zorder=3, linespacing=1.4)
    # 左箭头：s2 -> 走廊 -> 黄连解毒汤
    arrow(ax, (5.2, 6.2), (3.1, 4.75), color='#7f8c8d', lw=2.2, rad=0.12)
    arrow(ax, (3.1, 4.1), (3.1, 2.3), color='#7f8c8d', lw=2.2)
    ax.text(4.6, 5.75, '选黄连解毒汤', ha='center', va='center', fontsize=7.6, color='#7f8c8d', zorder=3)
    ax.text(3.35, 3.2, '候诊叫号', ha='center', va='center', fontsize=7.0,
            color='#7f8c8d', zorder=3)

    # 右栏：贪而不婪（全局最优）
    box(ax, 9.3, 3.55, 3.7, 1.15, '动作：归脾汤\n当下平淡（无即时甜头）', '#d5f5e3', '#1e8449', fs=9.0)
    ax.add_patch(Rectangle((7.5, 0.7), 3.6, 1.5, facecolor='#a9dfbf',
                           edgecolor='#1e8449', lw=1.8, zorder=2))
    ax.text(9.3, 1.75, 's3 康复吸收态（右手侧窗口）\n$v^*(s_3) = 10$（每步 +1）', ha='center', va='center',
            fontsize=9.0, color='#145a32', zorder=3, linespacing=1.4)
    ax.text(10.7, 2.6, '右手侧第1窗口·敲门进入', ha='center', va='center', fontsize=7.0,
            color='#1e8449', zorder=3)
    ax.text(9.3, 0.28, '$q^*(s_2,$归脾汤$) = 0 + 0.9\\times 10 = 9$',
            ha='center', va='center', fontsize=9.0, color='#1e8449', fontweight='bold', zorder=3)
    ax.text(9.3, 5.5, '贪而不婪：贪婪选择 = 长期最优\n（对 $q^*$ 贪婪 → 全局最优）', ha='center', va='center',
            fontsize=8.6, color='#1e8449', zorder=3, linespacing=1.4)
    # 右箭头：s2 -> 走廊 -> 归脾汤
    arrow(ax, (7.2, 6.2), (9.3, 4.75), color='#1e8449', lw=2.2, rad=-0.12)
    arrow(ax, (9.3, 4.1), (9.3, 2.3), color='#1e8449', lw=2.2)
    ax.text(7.8, 5.75, '选归脾汤', ha='center', va='center', fontsize=7.6, color='#1e8449', zorder=3)
    ax.text(9.05, 3.2, '敲门进入', ha='center', va='center', fontsize=7.0,
            color='#1e8449', zorder=3)

    # 底部定理条（聚焦）
    fig.text(0.5, 0.02,
             '定理5.1：对 $v^*$ 贪婪的 $\\pi$ 是最优策略，且 $v_\\pi = v^*$。数值与正文 5.1.2 一致：'
             '$v^* = (8.1, 9, 10, 0)$，两动作即时奖励皆为 0，差别全在远期——先有账本，后有选择；价值错一分，贪婪偏一里（5.3.2）。',
             ha='center', va='center', fontsize=8.6, color='#7d6608', zorder=3)
    fig.subplots_adjust(top=0.97, bottom=0.06)
    fig.savefig(os.path.join(OUT, 'fig5-4.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('fig5-4 done')


# =====================================================================
# 图 5-5 统一算法循环（聚焦：主循环三角形 + 收敛出口 + 三实例卡片；γ<1 收缩性）
# 价值迭代 / 策略迭代 / 时序差分共用"评估→改进→再评估"循环骨架
# =====================================================================
def fig5_5():
    fig, ax = plt.subplots(figsize=(11.4, 7.6))
    ax.set_xlim(0, 12.4)
    ax.set_ylim(0, 8.6)
    ax.set_aspect('equal')
    ax.axis('off')

    # 主循环三角形
    box(ax, 2.9, 7.1, 3.5, 1.15, '① 评估（价值估计）\n算出当前策略下每个状态的价值',
        '#eaf2f8', '#1f618d', fs=9.4)
    box(ax, 7.3, 7.1, 3.6, 1.15, '② 改进（策略更新）\n按价值最优方向更新策略',
        '#eaf2f8', '#1f618d', fs=9.4)
    box(ax, 5.1, 4.55, 3.9, 1.15, '③ 再评估（检验收敛）\n检查是否达到收敛判据',
        '#fdebd0', '#a04000', fs=9.4)
    # 循环箭头
    arrow(ax, (4.65, 7.1), (5.5, 7.1), rad=-0.25)
    arrow(ax, (6.7, 6.53), (6.25, 5.2), rad=-0.35)
    arrow(ax, (4.05, 5.2), (3.55, 6.53), rad=-0.35)
    ax.text(3.62, 5.85, '否（未收敛）：回到①再评估', ha='center', va='center',
            fontsize=8.2, color='#c0392b')
    # 循环中心徽章
    ax.add_patch(Circle((5.1, 5.85), 0.78, fc='#fef9e7', ec='#b7950b', lw=1.8, zorder=4))
    ax.text(5.1, 5.85, '统一算法循环\n评估—改进—再评估', ha='center', va='center',
            fontsize=8.4, color='#7d6608', fontweight='bold', zorder=5, linespacing=1.4)

    # 收敛出口（绿色）
    box(ax, 9.9, 5.6, 3.7, 1.5, '收敛出口\n满足判据（$\\max_s|\\Delta v| < \\varepsilon$ 或 $\\pi_{k+1} = \\pi_k$）\n→ 输出最优策略 / 价值',
        '#d5f5e3', '#1e8449', fs=8.8)
    arrow(ax, (7.05, 5.0), (8.05, 5.45), color='#1e8449', lw=2.2, rad=0.1)
    ax.text(7.5, 5.05, '判据成立', ha='center', va='center', fontsize=8.4,
            color='#1e8449', fontweight='bold')
    ax.text(9.9, 4.28, '收敛性由 γ < 1 的收缩性保证（5.2.2、5.6.2）', ha='center',
            va='center', fontsize=8.2, color='#515a5a')

    # 三个实例卡片（聚焦：压缩高度）
    box(ax, 2.0, 2.05, 3.85, 2.5,
        '价值迭代（5.4 节）\n评估一步：$v_{k+1} = \\max_a q_k$\n判据：$\\max_s |v_{k+1} - v_k| < \\varepsilon$\n例5.4：γ = 0.9 约 44 轮达 1% 精度',
        '#eaf2f8', '#1f618d', fs=8.8)
    box(ax, 6.2, 2.05, 3.85, 2.5,
        '策略迭代（5.5 节）\n评估到底：解 $v_\\pi = (I - \\gamma P_\\pi)^{-1} r_\\pi$\n改进：$\\pi \\leftarrow \\arg\\max_a q$（贪婪）\n判据：$\\pi_{k+1} = \\pi_k$ 对一切 $s$ 成立',
        '#d5f5e3', '#1e8449', fs=8.8)
    box(ax, 10.4, 2.05, 3.85, 2.5,
        '时序差分（第 6 章）\n评估一步：$v \\leftarrow v + \\alpha \\delta$（样本替代期望）\n无模型：从轨迹数据直接学习\n判据：更新量 < $\\varepsilon$ 或轮数上限',
        '#f4f6f7', '#85929e', fs=8.8)
    ax.text(2.0, 0.62, '“每尝一口就改配方”', ha='center', va='center', fontsize=8.0, color='#566573')
    ax.text(6.2, 0.62, '“整锅尝明白再改配方”', ha='center', va='center', fontsize=8.0, color='#566573')
    ax.text(10.4, 0.62, '“尝一口、改一口、再尝一口”', ha='center', va='center', fontsize=8.0, color='#566573')

    # 底部一句共性（聚焦）
    fig.text(0.5, 0.012,
             '差异仅在"评估到什么程度、如何判断收敛"——价值迭代评估一步即改进、策略迭代评估到底再改进、'
             '时序差分以样本平均替代期望（5.6.2 模型边界）；火候不同，殊途同归（PDCA：计划—执行—检查—改进，5.5.3）',
             ha='center', va='center', fontsize=8.6, color='#515a5a')
    fig.subplots_adjust(top=0.98, bottom=0.06)
    fig.savefig(os.path.join(OUT, 'fig5-5.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('fig5-5 done')


if __name__ == '__main__':
    fig5_1()
    fig5_2()
    fig5_3()
    fig5_4()
    fig5_5()
    print('ALL DONE ->', OUT)
