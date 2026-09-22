# -*- coding: utf-8 -*-
"""《中医场景强化学习》第5章 费曼图标准重构版（图表工程师 v5：文字精简与字号规范）

本版执行【图内文字精简与字号规范】（第5章）：
  ① 文字分层精简：每幅图只保留核心标注（节点名 + 1~2 个关键数值，每幅 ≤10 个标注条目）；
     长描述 / 公式细节 / 次要数值一律移入图注（忠实语义不丢）；
  ② 字号规范：核心标注 ≥11、节点名 ≥10、任何文字禁 <9pt（含图例、坐标轴刻度）；
  ③ 背景降噪：白底、无网格、无渐变、无阴影，框线细（房间 lw≤1.6、目标/禁区 2.0）；
  ④ 忠实语义：关键数值锚点保留在图体（v*=(8.1,9,10,0) 中的 q*=0/9、v*=0/10、例5.4 的
     1/0.9/0.81 扩散值、γ=0.9），其余细节（公式、路径说明、定理完整表述）移入图注；
  ⑤ 图注配套：正文 md 与 Excel 图注行同步追加『e. 阅读引导』句。

输出：figures/ch05/fig5-1.png ~ fig5-5.png（覆盖 v4 版）。
风格：SimHei / axes.unicode_minus=False / dpi=200。
数值：失眠链 v*=(8.1,9,10,0)、q*(s2,归脾汤)=9、q*(s2,黄连解毒汤)=0、γ=0.9；
      3×3 网格：s9 目标(到达后每步+1)、s6 禁区(进入得-1)、越界弹回-1、其余 0；
      例5.4：v1(s9)=1；v2(s8)=v2(s6)=0.9；v3(s5)=v3(s7)=0.81。

【移入图注清单】
- fig5-1：楼层标签（1层/2层/3层）、"乘电梯↑"、"右手侧第2窗口"、"敲门进入/候诊叫号"、
          "患者不可进入"、越界弹回 r=-1、最优策略可唯一性说明、s9 标"终"。
- fig5-2：房间名（大厅·挂号处/内科诊室/针灸科/检验科）、s6 手术区/s9 专家门诊语义、
          扩散圈说明、v3 子图沿用值（s8/s6=0.9、s9=1 的继续存在）、"每外扩一圈乘 γ"。
- fig5-3：线性方程组与逆矩阵公式（vπk=(I−γPπk)^{-1}rπk）、argmax 改进式、
          可逆性说明（γ<1 且 Pπk 随机矩阵）、临床对照"策略是迭代的主角"、
          "与价值迭代对照：火候不同殊途同归"。
- fig5-4：走廊文字（沿走廊行走不穿房）、候诊叫号/敲门进入、定理5.1 完整表述
          （对 v* 贪婪的 π 是最优策略且 vπ=v*）、"价值错一分贪婪偏一里"。
- fig5-5：三实例卡公式（v_{k+1}=max_a q_k、v_π=(I−γP_π)^{-1}r_π、v←v+αδ）、
          判据式（max_s|Δv|<ε 或 π_{k+1}=π_k）、三种"火候"配方语、PDCA 对照。
"""
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyBboxPatch, Circle, Polygon, Patch
from matplotlib.lines import Line2D

plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.facecolor'] = 'white'
plt.rcParams['savefig.facecolor'] = 'white'

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ch05')
os.makedirs(OUT, exist_ok=True)

# ---------- 费曼风格常量 ----------
K   = '#111111'
MG  = '#666666'
LG  = '#999999'
B   = '#5b7d9e'
R   = '#a35555'
G   = '#6b8e6b'
O   = '#b07a4f'

# ---------- 字号规范（v5）：核心标注 ≥11、节点名 ≥10、任何文字禁 <9 ----------
FS_NODE = 11.0      # 房间/流程节点（节点名）
FS_NODE_SMALL = 10.0  # 次节点（电梯核小字等）
FS_CORE = 12.0      # 核心数值/标题
FS_LABEL = 11.0     # 箭头旁注释
FS_HELP = 9.5       # 辅助文字
FS_LEGEND = 9.5     # 图例
FS_TICK = 9.0       # 坐标轴刻度


def state_xy(s):
    """行优先编号 s1-s9 -> 格心坐标 (col, row)，row 0 在顶端"""
    i = int(s[1:]) - 1
    return (i % 3, i // 3)


def box(ax, cx, cy, w, h, text, ec=K, fc='white', fs=FS_NODE, lw=1.4, tc=K,
        ls='-', style='square,pad=0', weight='normal'):
    ax.add_patch(FancyBboxPatch((cx - w / 2, cy - h / 2), w, h,
                                boxstyle=style, facecolor=fc, edgecolor=ec, lw=lw,
                                linestyle=ls, zorder=2))
    ax.text(cx, cy, text, ha='center', va='center', fontsize=fs,
            color=tc, zorder=3, linespacing=1.45, fontweight=weight)


def arrow(ax, xy1, xy2, color=K, lw=1.9, ls='-', rad=0.0, zorder=3):
    ax.annotate('', xy=xy2, xytext=xy1,
                arrowprops=dict(arrowstyle='-|>', color=color, lw=lw,
                                linestyle=ls, connectionstyle='arc3,rad={}'.format(rad)),
                zorder=zorder)


def count_texts(fig):
    n = 0
    for ax in fig.axes:
        for t in ax.texts:
            if t.get_text().strip():
                n += 1
        if ax.get_legend() is not None:
            n += 1
    return n


# =====================================================================
# 医院垂直切面共用绘制（fig5-1 / fig5-2 共用；白底黑框，细线稿）
# =====================================================================
ROOMS = {
    's1': '大厅·挂号处', 's3': '内科诊室', 's4': '针灸科',
    's6': '手术区', 's7': '检验科', 's9': '专家门诊',
}


def hospital_shell(ax, floor_labels=False):
    """医院外轮廓 + 两道楼板（细线稿；楼层标签移图注）"""
    for (x0, y0, x1, y1) in [(-0.5, -0.5, 2.5, -0.5), (-0.5, 2.5, 2.5, 2.5),
                             (-0.5, -0.5, -0.5, 2.5), (2.5, -0.5, 2.5, 2.5)]:
        ax.plot([x0, x1], [y0, y1], color=K, lw=2.2,
                solid_capstyle='butt', zorder=2)
    for y in [0.5, 1.5]:
        ax.plot([-0.5, 2.5], [y, y], color=MG, lw=1.4,
                solid_capstyle='butt', zorder=2)


def hospital_elevator_core(ax, elev_label=True):
    """中间列垂直交通核 s2/s5/s8：白底 + 灰色虚线井道 + 电梯↑（无填充色块）"""
    for s in ['s2', 's5', 's8']:
        col, row = state_xy(s)
        ax.add_patch(Rectangle((col - 0.5, row - 0.5), 1, 1, facecolor='white',
                               edgecolor=MG, lw=1.0, zorder=1))
        if elev_label:
            ax.text(col, row - 0.22, '电梯↑', ha='center', va='center',
                    fontsize=FS_NODE_SMALL, color=K, fontweight='bold', zorder=3)
    for x in [0.5, 1.5]:
        ax.plot([x, x], [-0.5, 2.5], color=LG, lw=1.0,
                linestyle=(0, (3, 2)), zorder=2)


def hospital_rooms(ax, with_name=True, with_r=True):
    """左右两列诊室房间：白底黑框；s6 禁区=斜纹线稿；s9 目标=粗框。
    房间标签 = 节点名（编号+房间名），s6/s9 附带关键数值 r=-1 / r=+1。"""
    for s in ['s1', 's3', 's4', 's6', 's7', 's9']:
        col, row = state_xy(s)
        if s == 's6':
            ec, lw, hatch = K, 1.6, '///'
        elif s == 's9':
            ec, lw, hatch = K, 2.0, ''
        else:
            ec, lw, hatch = K, 1.0, ''
        ax.add_patch(Rectangle((col - 0.5, row - 0.5), 1, 1, facecolor='white',
                               edgecolor=ec, lw=lw, hatch=hatch, zorder=1))
        if with_name:
            name = ROOMS[s]
            if with_r and s == 's6':
                name = name + '\nr = -1'
            elif with_r and s == 's9':
                name = name + '\nr = +1'
            ax.text(col, row + 0.04, name, ha='center', va='center',
                    fontsize=FS_NODE_SMALL, color=K, zorder=3, linespacing=1.35)


# =====================================================================
# 图 5-1 最优策略（医院垂直切面；10 个标注）
# 保留：6 房间节点（节点名+禁区/目标 r 值）、3×"电梯↑"、图例。
# 移图注：楼层标签、乘电梯↑、窗口指针标注、越界弹回、最优路径细节。
# =====================================================================
def fig5_1():
    fig, ax = plt.subplots(figsize=(7.4, 6.7))
    ax.set_xlim(-1.55, 3.55)
    ax.set_ylim(2.95, -0.95)
    ax.set_aspect('equal')
    ax.axis('off')

    hospital_shell(ax)
    hospital_elevator_core(ax, elev_label=True)
    hospital_rooms(ax, with_name=True, with_r=True)

    # 最优动作（绿色箭头）与示例路径（蓝色虚线）——线不计数
    OPT_H = {
        's1': (1, 0), 's2': (0, 1), 's3': (-1, 0), 's4': (1, 0),
        's5': (0, 1), 's6': (-1, 0), 's7': (1, 0), 's8': (1, 0),
    }
    for s, (dx, dy) in OPT_H.items():
        col, row = state_xy(s)
        ax.annotate('', xy=(col + 0.30 * dx, row + 0.30 * dy),
                    xytext=(col - 0.22 * dx, row - 0.22 * dy),
                    arrowprops=dict(arrowstyle='-|>', color=G,
                                    lw=2.2, mutation_scale=18), zorder=4)
    for (a, b) in [('s1', 's2'), ('s2', 's5'), ('s5', 's8'), ('s8', 's9')]:
        x1, y1 = state_xy(a)
        x2, y2 = state_xy(b)
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle='-|>', color=B, lw=1.8,
                                    linestyle=(0, (4, 2))), zorder=4)

    # 图例（精简 5 项）
    handles = [
        Patch(facecolor='white', edgecolor=K, label='诊室房间：可进入，r = 0'),
        Patch(facecolor='white', edgecolor=K, hatch='///', label='禁区（手术区）：r = -1'),
        Patch(facecolor='white', edgecolor=K, label='目标（专家门诊）：r = +1'),
        Line2D([0], [0], color=G, lw=2.2, label='最优动作（按最好方案）'),
        Line2D([0], [0], color=B, lw=1.8, linestyle=(0, (4, 2)),
               label='示例最优路径：沿走廊+乘电梯'),
    ]
    leg = ax.legend(handles=handles, loc='lower center', bbox_to_anchor=(0.5, -0.13),
                    ncol=2, fontsize=FS_LEGEND, frameon=True, edgecolor=K,
                    handlelength=1.5)
    leg.get_frame().set_facecolor('white')
    leg.get_frame().set_linewidth(0.8)
    fig.subplots_adjust(bottom=0.10)
    print('fig5-1 done  标注数 =', count_texts(fig))
    fig.savefig(os.path.join(OUT, 'fig5-1.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)


# =====================================================================
# 图 5-2 价值如水波扩散（4 子图；10 个标注）
# 保留：4 子图标题、关键数值锚点（s9=1、s8/s6=0.9、s5/s7=0.81）、电梯↑×1。
# 移图注：房间名、扩散圈说明、v3 沿用值、"每外扩一圈乘 γ"。
# =====================================================================
def fig5_2():
    rounds = [
        ('v0 初值', None, {}),
        ('第1轮 v1', '$v_1(s_9) = 1$', {'s9': 1}),
        ('第2轮 v2', '$v_2(s_8) = 0.9$, $v_2(s_6) = 0.9$', {'s8': 0.9, 's6': 0.9}),
        ('第3轮 v3', '$v_3(s_5) = 0.81$, $v_3(s_7) = 0.81$', {'s5': 0.81, 's7': 0.81}),
    ]
    fig, axes = plt.subplots(1, 4, figsize=(13.8, 4.7))
    for idx, (ax, (title, note, vals)) in enumerate(zip(axes, rounds)):
        ax.set_xlim(-1.25, 2.85)
        ax.set_ylim(3.05, -0.85)
        ax.set_aspect('equal')
        ax.axis('off')
        ax.set_title(title, fontsize=FS_NODE, color=K)
        # 扩散圈（灰色虚线，几何不计数）
        if idx > 0:
            for r, al in [(1.0, 0.45), (2.0, 0.25)]:
                ax.add_patch(Circle((2, 2), r, fill=False, ls=(0, (4, 3)),
                                    ec=MG, lw=1.0, alpha=al, zorder=2))
        # 电梯核（几何；s5/s8 属中间列，其价值数值在此绘制）
        for s in ['s2', 's5', 's8']:
            col, row = state_xy(s)
            ax.add_patch(Rectangle((col - 0.5, row - 0.5), 1, 1, facecolor='white',
                                   edgecolor=MG, lw=1.0, zorder=1))
            v = vals.get(s)
            if v is not None:
                txt = ('1' if v == 1.0 else ('%.2f' % v).rstrip('0').rstrip('.'))
                ax.text(col, row + 0.06, txt, ha='center', va='center',
                        fontsize=FS_CORE, fontweight='bold', color=K, zorder=3)
        if idx == 0:
            ax.text(1.0, 2.5, '电梯↑', ha='center', va='center',
                    fontsize=FS_NODE_SMALL, color=K, fontweight='bold', zorder=3)
        # 房间（白底黑框；禁区斜纹、目标粗框）
        for s in ['s1', 's3', 's4', 's6', 's7', 's9']:
            col, row = state_xy(s)
            hatch = '///' if s == 's6' else ''
            ax.add_patch(Rectangle((col - 0.5, row - 0.5), 1, 1, facecolor='white',
                                   edgecolor=K, lw=2.0 if s == 's9' else (1.5 if s == 's6' else 0.9),
                                   hatch=hatch, zorder=1))
            v = vals.get(s)
            if v is not None:
                txt = ('1' if v == 1.0 else ('%.2f' % v).rstrip('0').rstrip('.'))
                ax.text(col, row + 0.06, txt, ha='center', va='center',
                        fontsize=FS_CORE, fontweight='bold', color=K, zorder=3)
    fig.subplots_adjust(left=0.015, right=0.985, top=0.90, bottom=0.04, wspace=0.10)
    print('fig5-2 done  标注数 =', count_texts(fig))
    fig.savefig(os.path.join(OUT, 'fig5-2.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)


# =====================================================================
# 图 5-3 策略迭代循环（7 个标注）
# 保留：四流程节点（①~④）、"是→输出最优"/"否：回到②"、定理5.2/5.3 徽章。
# 移图注：线性方程组公式、argmax 改进式、可逆性说明、临床对照。
# =====================================================================
def fig5_3():
    fig, ax = plt.subplots(figsize=(9.8, 7.6))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 11)
    ax.set_aspect('equal')
    ax.axis('off')

    box(ax, 4.2, 9.75, 4.2, 0.95, '① 初始化：任取策略 π0', ec=K, fs=FS_NODE)
    box(ax, 4.2, 7.35, 4.7, 1.8, '② 策略评估：评估到底\n（解线性方程组得当前价值）',
        ec=K, fs=FS_NODE)
    box(ax, 4.2, 4.5, 4.7, 1.8, '③ 策略改进：贪婪更新\n（按前景最大者更新选方）',
        ec=K, fs=FS_NODE)
    dia = Polygon([(2.5, 1.85), (4.2, 2.9), (5.9, 1.85), (4.2, 0.8)],
                  closed=True, facecolor='white', edgecolor=K, lw=1.5, zorder=2)
    ax.add_patch(dia)
    ax.text(4.2, 1.85, '④ 判断：πk+1(s) = πk(s)\n对一切 s 成立？',
            ha='center', va='center', fontsize=FS_NODE, zorder=3, linespacing=1.4)
    box(ax, 8.7, 1.85, 3.1, 1.05, '是 → 输出最优策略 πk\n（终止）',
        ec=K, lw=1.8, fs=FS_NODE, weight='bold')

    arrow(ax, (4.2, 9.25), (4.2, 8.25))
    arrow(ax, (4.2, 6.45), (4.2, 5.4))
    arrow(ax, (4.2, 3.6), (4.2, 2.9))
    arrow(ax, (5.9, 1.85), (7.1, 1.85), color=G, lw=1.9)
    ax.text(6.5, 2.08, '是', ha='center', fontsize=FS_LABEL, color=G, fontweight='bold')
    arrow(ax, (3.5, 0.8), (1.85, 6.4), color=R, lw=1.8, rad=0.62)
    ax.text(1.05, 3.6, '否：回到②再评估', ha='center', fontsize=FS_LABEL,
            color=R, linespacing=1.4)

    # 徽章：定理5.2 / 5.3 合并一条
    box(ax, 9.6, 6.1, 4.5, 1.15,
        '定理5.2：策略改进后价值单调不降\n定理5.3：有限步终止（策略总数 ≤ |A|^|S|）',
        ec=MG, fs=FS_HELP)

    print('fig5-3 done  标注数 =', count_texts(fig))
    fig.subplots_adjust(top=0.98, bottom=0.02)
    fig.savefig(os.path.join(OUT, 'fig5-3.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)


# =====================================================================
# 图 5-4 贪婪策略（医院走廊版；9 个标注）
# 保留：s2 节点、两动作框、两结果窗口（节点名+关键数值 v*=0/10）、
#       q* 数值（0 / 9）、见利忘义/贪而不婪 标题。
# 移图注：走廊文字、候诊/敲门、定理5.1 完整表述。
# =====================================================================
def fig5_4():
    fig, ax = plt.subplots(figsize=(11.2, 6.4))
    ax.set_xlim(0, 12.4)
    ax.set_ylim(0, 7.6)
    ax.set_aspect('equal')
    ax.axis('off')

    box(ax, 6.2, 6.6, 3.6, 0.95, 's2 心脾两虚证（诊室）\n患者在此选择下一步走向',
        ec=K, fs=FS_NODE, weight='bold')
    ax.plot([0.6, 11.8], [4.6, 4.6], color=K, lw=2.2, solid_capstyle='butt', zorder=1)

    # 左栏：见利忘义（局部最优陷阱）
    box(ax, 3.1, 3.55, 3.7, 1.15, '动作：黄连解毒汤\n即时缓解（眼前甜头大）', ec=MG, fs=FS_NODE)
    ax.add_patch(Rectangle((1.3, 0.7), 3.6, 1.5, facecolor='white',
                           edgecolor=MG, lw=1.3, ls=(0, (4, 3)), hatch='///', zorder=2))
    ax.text(3.1, 1.75, 's4 迁延难愈（左手侧窗口）\nv* = 0', ha='center', va='center',
            fontsize=FS_NODE, color=MG, zorder=3, linespacing=1.4)
    ax.text(3.1, 0.22, 'q*(s2, 黄连解毒汤) = 0', ha='center', va='center',
            fontsize=FS_LABEL, color=MG, fontweight='bold', zorder=3)
    ax.text(3.1, 5.5, '见利忘义：即时最大 ≠ 前景最大', ha='center', va='center',
            fontsize=FS_LABEL, color=K, zorder=3, linespacing=1.4)
    arrow(ax, (5.2, 6.2), (3.1, 4.75), color=MG, lw=1.9, rad=0.12)
    arrow(ax, (3.1, 4.1), (3.1, 2.3), color=MG, lw=1.9)

    # 右栏：贪而不婪（全局最优）
    box(ax, 9.3, 3.55, 3.7, 1.15, '动作：归脾汤\n当下平淡（无即时甜头）', ec=K, lw=1.4, fs=FS_NODE)
    ax.add_patch(Rectangle((7.5, 0.7), 3.6, 1.5, facecolor='white',
                           edgecolor=K, lw=1.8, zorder=2))
    ax.text(9.3, 1.75, 's3 康复吸收态（右手侧窗口）\nv* = 10（每步 +1）', ha='center', va='center',
            fontsize=FS_NODE, color=K, zorder=3, linespacing=1.4)
    ax.text(9.3, 0.22, 'q*(s2, 归脾汤) = 9', ha='center', va='center',
            fontsize=FS_LABEL, color=K, fontweight='bold', zorder=3)
    ax.text(9.3, 5.5, '贪而不婪：贪婪选择 = 长期最优', ha='center', va='center',
            fontsize=FS_LABEL, color=G, zorder=3, linespacing=1.4)
    arrow(ax, (7.2, 6.2), (9.3, 4.75), color=G, lw=1.9, rad=-0.12)
    arrow(ax, (9.3, 4.1), (9.3, 2.3), color=G, lw=1.9)

    print('fig5-4 done  标注数 =', count_texts(fig))
    fig.subplots_adjust(top=0.97, bottom=0.06)
    fig.savefig(os.path.join(OUT, 'fig5-4.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)


# =====================================================================
# 图 5-5 统一算法循环（9 个标注）
# 保留：三角主循环 ①评估/②改进/③再评估 + 中央圆、收敛出口（判据成立）、
#       三实例卡标题（价值迭代/策略迭代/时序差分）。
# 移图注：各实例公式、判据式、"火候"配方语、PDCA 对照。
# =====================================================================
def fig5_5():
    fig, ax = plt.subplots(figsize=(11.4, 7.6))
    ax.set_xlim(0, 12.4)
    ax.set_ylim(0, 8.6)
    ax.set_aspect('equal')
    ax.axis('off')

    box(ax, 2.9, 7.1, 3.5, 1.15, '① 评估\n算出当前方案下每个证候的长期疗效', ec=K, fs=FS_NODE)
    box(ax, 7.3, 7.1, 3.6, 1.15, '② 改进\n按疗效最优方向更新方案', ec=K, fs=FS_NODE)
    box(ax, 5.1, 4.55, 3.9, 1.15, '③ 再评估\n检查是否达到稳定判据', ec=K, fs=FS_NODE)
    arrow(ax, (4.65, 7.1), (5.5, 7.1), rad=-0.25)
    arrow(ax, (6.7, 6.53), (6.25, 5.2), rad=-0.35)
    arrow(ax, (4.05, 5.2), (3.55, 6.53), rad=-0.35)
    ax.text(3.62, 5.85, '否（未达标）：回到①', ha='center', va='center',
            fontsize=FS_LABEL, color=K)
    ax.add_patch(Circle((5.1, 5.85), 0.78, fc='white', ec=K, lw=1.8, zorder=4))
    ax.text(5.1, 5.85, '统一算法循环\n评估—改进—再评估', ha='center', va='center',
            fontsize=FS_NODE, color=K, fontweight='bold', zorder=5, linespacing=1.4)

    box(ax, 9.9, 5.6, 3.7, 1.5, '收敛出口\n判据成立（Δv 小于阈值 或 πk+1 = πk）\n→ 输出最优策略 / 价值',
        ec=K, lw=1.8, fs=FS_NODE_SMALL)
    arrow(ax, (7.05, 5.0), (8.05, 5.45), color=G, lw=1.9, rad=0.1)
    ax.text(7.5, 5.05, '判据成立', ha='center', va='center', fontsize=FS_LABEL,
            color=G, fontweight='bold')

    box(ax, 2.0, 2.05, 3.85, 2.5, '价值迭代（5.4 节）\n评估一步即改进\n（v_{k+1} = max_a q_k）',
        ec=K, fs=FS_NODE_SMALL)
    box(ax, 6.2, 2.05, 3.85, 2.5, '策略迭代（5.5 节）\n评估到底再改进\n（解线性方程组）',
        ec=K, fs=FS_NODE_SMALL)
    box(ax, 10.4, 2.05, 3.85, 2.5, '时序差分（第 6 章）\n无模型：从轨迹数据直接学习\n（v ← v + α·δ）',
        ec=K, fs=FS_NODE_SMALL)

    print('fig5-5 done  标注数 =', count_texts(fig))
    fig.subplots_adjust(top=0.98, bottom=0.06)
    fig.savefig(os.path.join(OUT, 'fig5-5.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)


if __name__ == '__main__':
    fig5_1()
    fig5_2()
    fig5_3()
    fig5_4()
    fig5_5()
    print('ALL DONE ->', OUT)
