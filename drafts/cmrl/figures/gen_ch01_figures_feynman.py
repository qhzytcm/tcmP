# -*- coding: utf-8 -*-
"""《中医场景强化学习》第1章 核心图生成脚本（v4 图内文字精简与字号规范版，图表工程师 2026-08-20）

【图内文字精简与字号规范】批次落地（第1-3章统一）：
  ① 文字分层精简：每幅图图内只保留核心标注（节点名 + 1-2 个关键数值），每幅 ≤10 个标注；
     长描述、公式细节、次要数值（房间名、证候名、方剂名、楼层、矩阵、公式等）全部移入图注
     （图注为文字排版可大字号，忠实原文语义不丢）；
  ② 字号规范：核心标注 fontsize≥11、节点名 ≥10、任何文字禁 <9pt；
  ③ 背景降噪：白底（去浅灰填充 G0/G1）、无网格线、去装饰框、框线细（lw≤1）、
     图例并入节点标注（图上 1 行短文本代替图例框）；
  ④ 忠实语义：状态/方剂/疗效/传变等关键语义保留，数值锚点（r=-1/r=+1/G=1/v=9 等）保留在图注；
  ⑤ 图注（md 与 Excel）补『e. 阅读引导』句。

生成：fig1-1 / fig1-2 / fig1-3 / fig1-5 / fig1-6（覆盖 figures/ch01/*.png，SimHei + unicode_minus=False + dpi=200）
"""
import os
import math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle

plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ch01')
os.makedirs(OUT, exist_ok=True)

# ---- 色板（黑白灰 + 低饱和点缀）----
K   = '#111111'   # 主黑
DK  = '#333333'   # 深灰
MG  = '#666666'   # 中灰
LG  = '#999999'   # 浅灰
B   = '#5b7d9e'   # 灰蓝：示例路径/主链/映射
R   = '#a35555'   # 灰红：禁区/反哺/警示
O   = '#c07a3f'   # 低饱和橙：回路/示误轨迹
G   = '#6f9e6f'   # 低饱和绿：轨迹/汇总
P_GREEN = '#ffffff'  # 白底（原极淡绿）
P_BLUE  = '#ffffff'  # 白底（原极淡蓝）

# 字号规范
FS_NODE  = 10   # 节点名
FS_KEY   = 11   # 核心标注（关键数值）
FS_MAIN  = 12   # 主节点名/强调数值
LW_BOX   = 1.0  # 框线细

def state_xy(s):
    """行优先编号 → 格心坐标 (col, row)"""
    i = int(s[1:]) - 1
    return (i % 3, i // 3)


# ================================================================ 图 1-1
def fig1_1():
    """图 1-1 医院垂直切面网格寻路（精简版）
    图内 10 个标注：s1-s9 节点名（s6 禁区 r=-1 / s9 目标 r=+1 为核心数值）+ 1 行图例并入标注；
    房间名/楼层/越界弹回等细节全部移入图注。
    """
    fig, ax = plt.subplots(figsize=(6.6, 7.0))
    ax.set_xlim(-1.65, 3.60)
    ax.set_ylim(2.95, -0.95)
    ax.set_aspect('equal')
    ax.axis('off')

    # ---- 医院外轮廓 + 两道楼板（细线 lw<=1）----
    for (x0, y0, x1, y1) in [(-0.5, -0.5, 2.5, -0.5), (-0.5, 2.5, 2.5, 2.5),
                             (-0.5, -0.5, -0.5, 2.5), (2.5, -0.5, 2.5, 2.5)]:
        ax.plot([x0, x1], [y0, y1], color=K, lw=LW_BOX, solid_capstyle='butt', zorder=2)
    for y in [0.5, 1.5]:
        ax.plot([-0.5, 2.5], [y, y], color=DK, lw=LW_BOX, solid_capstyle='butt', zorder=2)

    # ---- 中间列：垂直交通核 s2/s5/s8（白底 + 电梯井虚线边界）----
    for s in ['s2', 's5', 's8']:
        col, row = state_xy(s)
        ax.add_patch(Rectangle((col - 0.5, row - 0.5), 1, 1, facecolor='white',
                               edgecolor=MG, lw=LW_BOX, zorder=1))
    for x in [0.5, 1.5]:
        ax.plot([x, x], [-0.5, 2.5], color=LG, lw=0.8, linestyle=(0, (3, 2)), zorder=2)

    # ---- 左右两列：诊室房间（白底黑细边；s6 禁区斜纹；s9 目标双线）----
    for s in ['s1', 's3', 's4', 's6', 's7', 's9']:
        col, row = state_xy(s)
        if s == 's6':
            ax.add_patch(Rectangle((col - 0.5, row - 0.5), 1, 1, facecolor='white',
                                   edgecolor=K, lw=LW_BOX, hatch='///', zorder=1))
        elif s == 's9':
            # 目标格：双细线形成视觉强调（每根 lw<=1）
            ax.add_patch(Rectangle((col - 0.53, row - 0.53), 1.06, 1.06, facecolor='none',
                                   edgecolor=K, lw=LW_BOX, zorder=1))
            ax.add_patch(Rectangle((col - 0.5, row - 0.5), 1, 1, facecolor='white',
                                   edgecolor=K, lw=LW_BOX, zorder=1))
        else:
            ax.add_patch(Rectangle((col - 0.5, row - 0.5), 1, 1, facecolor='white',
                                   edgecolor=K, lw=LW_BOX, zorder=1))

    # ---- 示例路径：灰蓝虚线箭头 s1→s2→s5→s8→s9（沿走廊+电梯）----
    for (a, b) in [('s1', 's2'), ('s2', 's5'), ('s5', 's8'), ('s8', 's9')]:
        x1, y1 = state_xy(a)
        x2, y2 = state_xy(b)
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle='-|>', color=B, lw=1.5,
                                    linestyle=(0, (4, 2))), zorder=4)

    # ---- 图内 10 个标注：9 个格子（节点名/核心数值）+ 1 行图例并入标注 ----
    for s in ['s1', 's2', 's3', 's4', 's5', 's6', 's7', 's8', 's9']:
        col, row = state_xy(s)
        if s == 's6':
            ax.text(col, row, 's6 禁区\nr = -1', ha='center', va='center',
                    fontsize=FS_KEY, fontweight='bold', color=K, zorder=3)
        elif s == 's9':
            ax.text(col, row, 's9 目标\nr = +1', ha='center', va='center',
                    fontsize=FS_KEY, fontweight='bold', color=K, zorder=3)
        else:
            ax.text(col, row, s, ha='center', va='center',
                    fontsize=FS_NODE, fontweight='bold', color=K, zorder=3)
    ax.text(1.0, -0.72, '蓝虚线 = 示例就医路径（沿走廊 + 乘电梯）',
            ha='center', va='center', fontsize=FS_NODE, color=B, zorder=5)

    fig.savefig(os.path.join(OUT, 'fig1-1.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('fig1-1 done')


# ================================================================ 图 1-2
def fig1_2():
    """图 1-2 从四诊到疗效：状态—动作—奖励的临床映射（精简版）
    图内 6 个标注：S/A/R 三个主节点名 + 3 处箭头标注；框内细节全部移入图注。
    """
    fig, ax = plt.subplots(figsize=(9.6, 4.6))
    ax.set_xlim(-0.35, 11.75)
    ax.set_ylim(-0.45, 4.95)
    ax.set_aspect('equal')
    ax.axis('off')

    boxes = [
        (0.2, 1.0, 3.0, 3.4, 'S 四诊所见\n"此刻我在哪"'),
        (4.2, 1.0, 3.0, 3.4, 'A 治法方剂\n"可以怎么改变"'),
        (8.2, 1.0, 3.0, 3.4, 'R 疗效反馈\n"做得如何"'),
    ]
    for x, y, w, h, txt in boxes:
        ax.add_patch(Rectangle((x, y), w, h, facecolor='white', edgecolor=K,
                               lw=LW_BOX, zorder=2))
        ax.text(x + w / 2, y + h / 2, txt, ha='center', va='center',
                fontsize=FS_MAIN, fontweight='bold', color=K, zorder=3, linespacing=1.5)

    # 主箭头 S→A 与 A→R（黑色细实线）
    ax.annotate('', xy=(4.05, 2.7), xytext=(3.35, 2.7),
                arrowprops=dict(arrowstyle='-|>', color=K, lw=1.6), zorder=3)
    ax.annotate('', xy=(8.05, 2.7), xytext=(7.35, 2.7),
                arrowprops=dict(arrowstyle='-|>', color=K, lw=1.6), zorder=3)
    # 反馈回路：右框底 → 左框底（橙色虚线）
    ax.annotate('', xy=(1.7, 0.72), xytext=(9.7, 0.72),
                arrowprops=dict(arrowstyle='-|>', color=O, lw=1.4,
                                linestyle=(0, (5, 3))), zorder=3)

    # 图内标注（6 个）
    ax.text(3.7, 3.10, '辨证 → 论治', ha='center', fontsize=FS_KEY,
            color=K, fontweight='bold')
    ax.text(7.7, 3.10, '用方 → 复诊反馈 Rt+1', ha='center', fontsize=FS_KEY, color=K)
    ax.text(5.7, 0.18, '复诊转归 → 新状态 St+1', ha='center',
            fontsize=FS_KEY, color=O, fontweight='bold')

    fig.savefig(os.path.join(OUT, 'fig1-2.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('fig1-2 done')


# ================================================================ 图 1-3
ACT = {
    's1': ('a3', '↓'), 's2': ('a3', '↓'), 's3': ('a4', '←'),
    's4': ('a3', '↓'), 's5': ('a3', '↓'), 's6': ('a4', '←'),
    's7': ('a2', '→'), 's8': ('a2', '→'), 's9': ('a5', '·'),
}

def draw_grid_policy(ax):
    """九宫格（图1-3 右图）：白底黑细边；s6 禁区斜纹；s9 目标双线。
    格内标注：编号 + 选定走法（= 方剂动作），每格 1 个文本块。"""
    for s in ['s1', 's2', 's3', 's4', 's5', 's6', 's7', 's8', 's9']:
        col, row = state_xy(s)
        if s == 's6':
            ax.add_patch(Rectangle((col - 0.5, row - 0.5), 1, 1, facecolor='white',
                                   edgecolor=K, lw=LW_BOX, hatch='///', zorder=1))
        elif s == 's9':
            ax.add_patch(Rectangle((col - 0.53, row - 0.53), 1.06, 1.06, facecolor='none',
                                   edgecolor=K, lw=LW_BOX, zorder=1))
            ax.add_patch(Rectangle((col - 0.5, row - 0.5), 1, 1, facecolor='white',
                                   edgecolor=K, lw=LW_BOX, zorder=1))
        else:
            ax.add_patch(Rectangle((col - 0.5, row - 0.5), 1, 1, facecolor='white',
                                   edgecolor=K, lw=LW_BOX, zorder=1))
        act, arrow = ACT[s]
        ax.text(col, row, f'{s}  {act}{arrow}', ha='center', va='center',
                fontsize=FS_KEY, fontweight='bold', color=K, zorder=3)
    for (x0, y0, x1, y1) in [(-0.5, -0.5, 2.5, -0.5), (-0.5, 2.5, 2.5, 2.5),
                             (-0.5, -0.5, -0.5, 2.5), (2.5, -0.5, 2.5, 2.5)]:
        ax.plot([x0, x1], [y0, y1], color=K, lw=LW_BOX, solid_capstyle='butt', zorder=2)


def fig1_3():
    """图 1-3 辨证论治策略：每一证候一个方剂，处处有决策（精简版）
    图内 10 个标注：九宫格 9 格（节点名+走法）+ 1 行图例并入标注；
    左表（临证选方表 9 行）全部移入图注。
    """
    fig, axR = plt.subplots(figsize=(8.6, 5.6))
    axR.set_xlim(-0.7, 3.4)
    axR.set_ylim(2.7, -0.7)
    axR.set_aspect('equal')
    axR.axis('off')
    draw_grid_policy(axR)

    # 三条轨迹：蓝实线 / 绿虚线 / 橙点线（橙色穿禁区示误）
    paths = [
        (['s1', 's4', 's7', 's8', 's9'], B, 'solid', 1.5),
        (['s2', 's5', 's8', 's9'], G, (0, (4, 2)), 1.4),
        (['s3', 's6', 's9'], O, (0, (2, 2)), 1.4),
    ]
    for p, c, ls, lw in paths:
        for i in range(len(p) - 1):
            x1, y1 = state_xy(p[i])
            x2, y2 = state_xy(p[i + 1])
            axR.annotate('', xy=(x2, y2), xytext=(x1, y1),
                         arrowprops=dict(arrowstyle='-|>', color=c, lw=lw,
                                         linestyle=ls), zorder=2)
    # 灰红圈提示：改一格、看全局（s5 改走 a2 进禁区）
    axR.add_patch(Circle((0.66, 1.42), 0.15, facecolor='none',
                         edgecolor=K, lw=1.0, zorder=4))

    # 图例并入节点标注（1 行）
    axR.text(1.35, -0.62,
             '蓝 = 从 s1 出发 · 绿 = 从 s2 出发 · 橙 = 从 s3 出发（示误穿禁区）',
             ha='center', va='center', fontsize=FS_NODE, color=DK, zorder=5)

    fig.savefig(os.path.join(OUT, 'fig1-3.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('fig1-3 done')


# ================================================================ 图 1-5
def fig1_5():
    """图 1-5 诊疗全过程：状态—动作—奖励链与回报时间线（精简版）
    图内 10 个标注：5 状态方块（节点名，s9 含 r=+1）+ 4 个走法 + 1 个回报 G=1；
    各步奖励 r=0/0/0/+1 移入图注。
    """
    fig, ax = plt.subplots(figsize=(10.0, 3.2))
    ax.set_xlim(-0.2, 13.9)
    ax.set_ylim(3.45, 6.0)
    ax.set_aspect('equal')
    ax.axis('off')

    y = 4.6
    xs = [0.8, 3.2, 5.6, 8.0, 10.4]
    main = [('s1', '初诊'), ('s2', '风寒表证'), ('s5', '麻黄汤'),
            ('s8', '表证渐解'), ('s9', '痊愈')]
    acts = ['a2', 'a3', 'a3', 'a2']
    for k, (s, txt) in enumerate(main):
        fc = 'white'
        if s == 's9':
            ax.add_patch(Rectangle((xs[k] - 0.03, y - 0.53), 1.76, 1.06, facecolor='none',
                                   edgecolor=K, lw=LW_BOX, zorder=1))
            ax.add_patch(Rectangle((xs[k], y - 0.5), 1.7, 1.0, facecolor=fc,
                                   edgecolor=K, lw=LW_BOX, zorder=2))
        else:
            ax.add_patch(Rectangle((xs[k], y - 0.5), 1.7, 1.0, facecolor=fc,
                                   edgecolor=K, lw=LW_BOX, zorder=2))
        if s == 's9':
            ax.text(xs[k] + 0.85, y, f'{s} {txt}\nr = +1', ha='center', va='center',
                    fontsize=FS_KEY, fontweight='bold', color=K, zorder=3, linespacing=1.3)
        else:
            ax.text(xs[k] + 0.85, y, f'{s} {txt}', ha='center', va='center',
                    fontsize=FS_NODE, fontweight='bold', color=K, zorder=3)
        if k < 4:
            xa1, xa2 = xs[k] + 1.7, xs[k + 1]
            ax.annotate('', xy=(xa2, y), xytext=(xa1, y),
                        arrowprops=dict(arrowstyle='-|>', color=B, lw=1.5), zorder=3)
            ax.text((xa1 + xa2) / 2, y + 0.38, acts[k], ha='center',
                    fontsize=FS_KEY, color=K, fontweight='bold')
    # 回报框（白底绿细边）
    ax.add_patch(Rectangle((12.25, 4.15), 1.3, 0.85, facecolor='white',
                           edgecolor=G, lw=LW_BOX, zorder=2))
    ax.text(12.9, 4.55, 'G = 1', ha='center', va='center',
            fontsize=FS_KEY, color=K, zorder=3, fontweight='bold')

    fig.savefig(os.path.join(OUT, 'fig1-5.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('fig1-5 done')


# ================================================================ 图 1-6
def fig1_6():
    """图 1-6 中医临床元素与强化学习概念：双向映射环（精简版）
    图内 10 个标注：外环 5 个中医临床元素 + 内环 5 个临床实践环节（节点名）；
    中央圆内不写字（双向箭头表达映射⇄反哺），流程环向说明移入图注。
    """
    fig, ax = plt.subplots(figsize=(9.6, 9.2))
    ax.set_xlim(-6.6, 6.6)
    ax.set_ylim(-6.5, 6.5)
    ax.set_aspect('equal')
    ax.axis('off')

    pairs = [
        (90, '四诊症状', '审证求因'),
        (18, '辨证论治', '辨证立法'),
        (-54, '治法方剂', '处方用药'),
        (-126, '疗效反馈', '疗效评价'),
        (162, '病邪传变', '病程传变'),
    ]
    R_RL, R_TCM = 2.45, 5.05
    for deg, tcm, rl in pairs:
        a = math.radians(deg)
        # 内环：临床实践环节（白底蓝细边）
        cx_rl, cy_rl = R_RL * math.cos(a), R_RL * math.sin(a)
        ax.add_patch(Rectangle((cx_rl - 1.0, cy_rl - 0.475), 2.0, 0.95,
                               facecolor='white', edgecolor=B, lw=LW_BOX, zorder=3))
        ax.text(cx_rl, cy_rl, rl, ha='center', va='center', fontsize=FS_NODE,
                fontweight='bold', color=K, zorder=4)
        # 外环：中医临床元素（白底绿细边）
        cx_tm, cy_tm = R_TCM * math.cos(a), R_TCM * math.sin(a)
        ax.add_patch(Rectangle((cx_tm - 1.05, cy_tm - 0.425), 2.1, 0.85,
                               facecolor='white', edgecolor=G, lw=LW_BOX, zorder=3))
        ax.text(cx_tm, cy_tm, tcm, ha='center', va='center', fontsize=FS_NODE,
                fontweight='bold', color=K, zorder=4)
        # 双向箭头微错开：反哺 RL→TCM 灰红虚线；映射 TCM→RL 蓝实线
        a1, a2 = a + 0.14, a - 0.14
        x1, y1 = 3.62 * math.cos(a1), 3.62 * math.sin(a1)
        x2, y2 = 3.82 * math.cos(a1), 3.82 * math.sin(a1)
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle='-|>', color=R, lw=1.2,
                                    linestyle=(0, (3, 2))), zorder=3)
        x3, y3 = 3.82 * math.cos(a2), 3.82 * math.sin(a2)
        x4, y4 = 3.62 * math.cos(a2), 3.62 * math.sin(a2)
        ax.annotate('', xy=(x4, y4), xytext=(x3, y3),
                    arrowprops=dict(arrowstyle='-|>', color=B, lw=1.3), zorder=3)

    # 中央：映射 ⇄ 反哺（白底黑细边 + 两条反向箭头，不写字）
    ax.add_patch(Circle((0, 0), 1.18, fc='white', ec=K, lw=LW_BOX, zorder=4))
    ax.annotate('', xy=(0.52, 0.12), xytext=(0.52, -0.12),
                arrowprops=dict(arrowstyle='-|>', color=B, lw=1.4), zorder=5)
    ax.annotate('', xy=(-0.52, -0.12), xytext=(-0.52, 0.12),
                arrowprops=dict(arrowstyle='-|>', color=R, lw=1.2,
                                linestyle=(0, (3, 2))), zorder=5)

    fig.savefig(os.path.join(OUT, 'fig1-6.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('fig1-6 done')


if __name__ == '__main__':
    fig1_1()
    fig1_2()
    fig1_3()
    fig1_5()
    fig1_6()
    print('ALL DONE ->', OUT)
