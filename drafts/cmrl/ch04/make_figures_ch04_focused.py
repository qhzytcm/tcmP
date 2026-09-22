# -*- coding: utf-8 -*-
"""
《中医场景强化学习》第4章 图表生成脚本（v2 聚焦版）
生成 4 幅核心图（fig4-1 ~ fig4-4）到 ../figures/ch04/，覆盖旧图。

聚焦原则（用户新要求）：图体只保留"能代表含义的图段"——
  调节数轴起止刻度与步长，聚焦关键区域，使图段紧凑。
  fig4-1 聚焦三状态主链价值段（9/10/10 + 红圈 +1 不可漏写）；
  fig4-2 聚焦"今日收入 + 明日账 = 今日价值"三栏汇聚段与递归箭头；
  fig4-3 聚焦"打包 → 求逆回代"两步核心（I-γPπ 下三角块 → v=[9,10,10,10]T）；
  fig4-4 聚焦误差每步 ×γ=0.9 的收缩段（k=0..6，不再画 0..25 全范围）。

风格：SimHei，unicode_minus=False，dpi=200。
数值口径：一律采用例4.2 修正值（vπ(s1)=9, vπ(s2)=10, vπ(s3)=10）。
字形坑：U+2081-2084 下标、U+00B2/U+2070 上标、U+2212 减号、ᵀ 一律用 mathtext 或 ASCII。
"""
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle

plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.facecolor'] = 'white'

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'figures', 'ch04')
os.makedirs(OUT, exist_ok=True)

# ---------- 配色（与配图说明一致） ----------
C_BLUE   = '#2E86AB'   # 即时/主体（蓝）
C_ORANGE = '#E67E22'   # 价值/警示（橙）
C_GREEN  = '#27AE60'   # 康复/目标（绿）
C_PURPLE = '#8E44AD'   # 策略/矩阵（紫）
C_RED    = '#C0392B'   # 折扣/警示（红）
C_GRAY   = '#7F8C8D'   # 对照/次要（灰）
C_LBLUE  = '#D6EAF8'
C_LGREEN = '#D5F5E3'
C_LORANGE= '#FDEBD0'
C_LGRAY  = '#ECF0F1'
C_LPURPLE= '#E8DAEF'


def box(ax, cx, cy, w, h, text, fc='white', ec='#2C3E50', fs=13, tc='black',
        lw=1.8, ls='-', weight='normal'):
    """圆角矩形 + 居中多行文本；返回中心坐标"""
    ax.add_patch(FancyBboxPatch((cx - w / 2, cy - h / 2), w, h,
                                boxstyle='round,pad=0.006,rounding_size=0.012',
                                fc=fc, ec=ec, lw=lw, linestyle=ls))
    ax.text(cx, cy, text, ha='center', va='center', fontsize=fs, color=tc,
            weight=weight, linespacing=1.5)
    return cx, cy


def arrow(ax, x0, y0, x1, y1, color='#2C3E50', lw=2.0, ls='-', style='-|>',
          mut=0.015, rad=0.0):
    a = FancyArrowPatch((x0, y0), (x1, y1), arrowstyle=style, mutation_scale=mut * 1000,
                        lw=lw, color=color, linestyle=ls,
                        connectionstyle=f'arc3,rad={rad}')
    ax.add_patch(a)


def draw_matrix(ax, cx, cy, w, h, rows, fc='white', ec=C_PURPLE, fs=12, lw=1.8):
    n, m = len(rows), len(rows[0])
    x0, x1 = cx - w / 2, cx + w / 2
    y0, y1 = cy - h / 2, cy + h / 2
    ax.add_patch(FancyBboxPatch((x0, y0), w, h, boxstyle='square,pad=0',
                                fc=fc, ec=ec, lw=lw))
    for i in range(1, n):
        ax.plot([x0, x1], [y0 + h * i / n, y0 + h * i / n], color=ec, lw=0.7)
    for j in range(1, m):
        ax.plot([x0 + w * j / m, x0 + w * j / m], [y0, y1], color=ec, lw=0.7)
    for i in range(n):
        for j in range(m):
            v = rows[i][j]
            ax.text(x0 + w * (j + 0.5) / m, y1 - h * (i + 0.5) / n, str(v),
                    ha='center', va='center', fontsize=fs, color='black')
    return (x0, y0, x1, y1)


def draw_colvector(ax, cx, cy, w, h, vals, ec, fs=13, label='v', show_label=True):
    n = len(vals)
    x0, x1 = cx - w / 2, cx + w / 2
    y0, y1 = cy - h / 2, cy + h / 2
    ax.add_patch(FancyBboxPatch((x0, y0), w, h, boxstyle='square,pad=0',
                                fc='white', ec=ec, lw=1.8))
    for i, v in enumerate(vals):
        ax.text(cx, y1 - h * (i + 0.5) / n, str(v), ha='center', va='center', fontsize=fs)
    if show_label:
        ax.text(x1 + 0.008, y1, r'$^{\top}$', fontsize=fs - 2, color=ec)
    return x0, y0, x1, y1


# ============================================================
# 图 4-1 状态价值示意：失眠病程链（聚焦三状态主链价值段 9/10/10）
# ============================================================
def fig_4_1():
    fig = plt.figure(figsize=(9.5, 4.8))
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis('off')

    ax.text(0.03, 0.955, r'$\gamma$ = 0.9（折扣率）', fontsize=13, color='#2C3E50', weight='bold')

    # 主链三状态（聚焦段：s1 → s2 → s3 的价值 9/10/10）
    box(ax, 0.15, 0.62, 0.24, 0.30, 's1\n失眠初起\nvπ(s1) = 9', fc=C_LBLUE, ec=C_BLUE, fs=13, weight='bold')
    box(ax, 0.49, 0.62, 0.24, 0.30, 's2\n心脾两虚证\nvπ(s2) = 10', fc=C_LBLUE, ec=C_BLUE, fs=13, weight='bold')
    box(ax, 0.84, 0.62, 0.24, 0.30, 's3\n康复（吸收态）\nvπ(s3) = 10', fc=C_LGREEN, ec=C_GREEN, fs=13, weight='bold')

    # 转移箭头与奖励
    arrow(ax, 0.27, 0.62, 0.37, 0.62, color='#2C3E50', lw=2.2)
    ax.text(0.32, 0.665, 'r = 0', ha='center', fontsize=12)
    arrow(ax, 0.61, 0.62, 0.72, 0.62, color=C_RED, lw=2.6)
    ax.text(0.665, 0.665, 'r = +1（到达康复）', ha='center', fontsize=12, color=C_RED, weight='bold')
    # 红圈：不可漏写（指针图段标记）
    ax.add_patch(Circle((0.665, 0.575), 0.013, fc='none', ec=C_RED, lw=2.2))
    ax.text(0.665, 0.53, '不可漏写', ha='center', fontsize=9.5, color=C_RED)

    # s3 自环（吸收态每步 +1）
    arrow(ax, 0.78, 0.765, 0.90, 0.765, color=C_GREEN, lw=2.0, rad=-0.35)
    ax.text(0.84, 0.805, '停留每步 +1', ha='center', fontsize=11, color=C_GREEN)

    # s4 迁延难愈（例4.1 定义；停留无奖励 ⇒ v=0）——紧凑放置
    box(ax, 0.84, 0.24, 0.24, 0.24, 's4\n迁延难愈\nvπ(s4) = 0', fc=C_LGRAY, ec=C_GRAY, fs=12)
    arrow(ax, 0.78, 0.355, 0.90, 0.355, color=C_GRAY, lw=1.8, rad=-0.35)
    ax.text(0.84, 0.395, '停留每步 0', ha='center', fontsize=10, color=C_GRAY)
    ax.text(0.84, 0.075, '（正文例4.1 定义的状态，按停留无奖励计）',
            ha='center', fontsize=8.5, color=C_GRAY)

    # 错误记法对照（例4.2 插曲）——一行小字
    ax.text(0.5, 0.03, '错误记法：若把 s2→s3 的 +1 奖励漏记为 0，则 vπ(s2)=9、vπ(s1)=8.1（错）——与枚举轨迹矛盾，见 4.2.2 例4.2 插曲',
            ha='center', fontsize=10, color=C_GRAY, style='italic')

    fig.savefig(os.path.join(OUT, 'fig4-1.png'), dpi=200, bbox_inches='tight', pad_inches=0.05)
    plt.close(fig)
    print('fig4-1 OK')


# ============================================================
# 图 4-2 价值估计方程递归图（聚焦三栏汇聚段 + 递归箭头）
# ============================================================
def fig_4_2():
    fig = plt.figure(figsize=(10, 5.2))
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis('off')

    # 顶部方程（完整形式，与正文 4.2.1 一致）
    eq = (r'$v_\pi(s) = \sum_a \pi(a|s)\left[\sum_r p(r|s,a)\, r '
          r'+ \gamma \sum_{s^\prime} p(s^\prime|s,a)\, v_\pi(s^\prime)\right]$')
    ax.text(0.5, 0.93, eq, ha='center', va='center', fontsize=19)

    # 五部分颜色图例
    items = [('策略 π(a|s)', C_PURPLE), ('期望即时奖励', C_BLUE), ('折扣 γ', C_RED),
             ('后继状态价值', C_GREEN), ('转移概率 p(s′|s,a)', C_GRAY)]
    x = 0.04
    for label, c in items:
        ax.add_patch(FancyBboxPatch((x, 0.845), 0.024, 0.024, boxstyle='round,pad=0',
                                    fc=c, ec='none'))
        ax.text(x + 0.031, 0.857, label, fontsize=10, va='center', color='#2C3E50')
        x += 0.136

    # 三栏（指针图段：①今日收入 + ②明日账 = 今日价值）
    box(ax, 0.185, 0.52, 0.29, 0.30, '① 今日收入\n期望即时奖励\nΣr p(r|s,a) · r',
        fc=C_LORANGE, ec=C_ORANGE, fs=13)
    box(ax, 0.545, 0.52, 0.29, 0.30, '② 明日账\n折扣 × 后继价值\nγ · Σs′ p(s′|s,a) · vπ(s′)',
        fc=C_LBLUE, ec=C_BLUE, fs=13)
    box(ax, 0.865, 0.52, 0.22, 0.30, '今日价值\nvπ(s)\n= ① + ②', fc=C_LGREEN, ec=C_GREEN, fs=13)

    # 汇聚箭头
    arrow(ax, 0.33, 0.60, 0.755, 0.60, color=C_ORANGE, lw=2.0, rad=0.12)
    ax.text(0.52, 0.635, '+', fontsize=16, ha='center', color='#2C3E50')
    arrow(ax, 0.69, 0.52, 0.755, 0.52, color=C_BLUE, lw=2.0, rad=0.12)

    # 递归弯箭头：今日价值 → 明日账
    arrow(ax, 0.865, 0.675, 0.545, 0.675, color=C_RED, lw=2.4, rad=0.42)
    ax.text(0.705, 0.765, '明日的账，明天再记——递归（bootstrap）', ha='center', fontsize=12,
            color=C_RED, weight='bold')

    # 底部账本隐喻 + 例4.2 数值
    box(ax, 0.5, 0.13, 0.94, 0.19, '', fc=C_LGRAY, ec=C_GRAY, lw=1.5)
    ax.text(0.5, 0.175, '账本隐喻：今天的账 = 今天的收入 + 折扣 × 明天的账',
            ha='center', fontsize=14, weight='bold', color='#2C3E50')
    ax.text(0.5, 0.11, '老医师："这个证候我见过，将来会这样转"——就是在做递归记账',
            ha='center', fontsize=12, color='#2C3E50')
    ax.text(0.5, 0.045, '例4.2 代入（γ=0.9）：vπ(s3)=1+0.9×10=10；vπ(s2)=1+0.9×10=10；vπ(s1)=0+0.9×10=9',
            ha='center', fontsize=11.5, color=C_GREEN)

    fig.savefig(os.path.join(OUT, 'fig4-2.png'), dpi=200, bbox_inches='tight', pad_inches=0.05)
    plt.close(fig)
    print('fig4-2 OK')


# ============================================================
# 图 4-3 矩阵求解示意（聚焦"打包 → 求逆回代"两步核心）
# ============================================================
def fig_4_3():
    fig = plt.figure(figsize=(11, 6.2))
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis('off')

    # ---- 行1：四状态图（紧凑）----
    ax.text(0.02, 0.975, '① 状态图（γ=0.9，策略确定）', fontsize=12.5, color='#2C3E50', weight='bold')
    box(ax, 0.10, 0.91, 0.12, 0.09, 's1\n失眠初起', fc=C_LBLUE, ec=C_BLUE, fs=11)
    box(ax, 0.26, 0.91, 0.12, 0.09, 's2\n心脾两虚证', fc=C_LBLUE, ec=C_BLUE, fs=11)
    box(ax, 0.68, 0.91, 0.12, 0.11, 's4\n吸收目标态\n（停留每步 +1）', fc=C_LGREEN, ec=C_GREEN, fs=10)
    box(ax, 0.68, 0.77, 0.12, 0.09, 's3', fc=C_LBLUE, ec=C_BLUE, fs=11)
    arrow(ax, 0.16, 0.91, 0.20, 0.91, color='#2C3E50', lw=2.0)
    ax.text(0.18, 0.945, 'r=0', ha='center', fontsize=10)
    arrow(ax, 0.32, 0.91, 0.62, 0.91, color=C_RED, lw=2.2)
    ax.text(0.47, 0.945, 'r=+1', ha='center', fontsize=10, color=C_RED)
    arrow(ax, 0.68, 0.815, 0.68, 0.865, color=C_RED, lw=2.2)
    ax.text(0.72, 0.84, 'r=+1', ha='left', fontsize=10, color=C_RED)
    arrow(ax, 0.74, 0.965, 0.80, 0.965, color=C_GREEN, lw=1.8, rad=-0.4)
    ax.text(0.77, 0.985, '+1', ha='center', fontsize=10, color=C_GREEN)

    # ---- 行2：打包（指针图段之一）----
    ax.text(0.02, 0.665, '② 打包：v = rπ + γPπv', fontsize=12.5, color='#2C3E50', weight='bold')
    draw_colvector(ax, 0.095, 0.50, 0.045, 0.20, [r'$v_1$', r'$v_2$', r'$v_3$', r'$v_4$'], C_GREEN, fs=11, label='')
    ax.text(0.115, 0.615, 'v', fontsize=15, color=C_GREEN, weight='bold', ha='center')
    ax.text(0.135, 0.50, '=', fontsize=18, color='#2C3E50', ha='center', va='center')
    draw_colvector(ax, 0.19, 0.50, 0.05, 0.20, ['0', '1', '1', '1'], C_BLUE, fs=11)
    ax.text(0.19, 0.615, 'rπ', fontsize=12, color=C_BLUE, weight='bold', ha='center')
    ax.text(0.245, 0.50, '+ γ ×', fontsize=15, color=C_RED, ha='center', va='center')
    P = [[0, 1, 0, 0], [0, 0, 0, 1], [0, 0, 0, 1], [0, 0, 0, 1]]
    draw_matrix(ax, 0.42, 0.50, 0.22, 0.20, P, fc=C_LPURPLE, ec=C_PURPLE, fs=10.5)
    ax.text(0.42, 0.615, 'Pπ', fontsize=13, color=C_PURPLE, weight='bold', ha='center')
    ax.text(0.56, 0.50, '×', fontsize=15, color='#2C3E50', ha='center', va='center')
    draw_colvector(ax, 0.615, 0.50, 0.045, 0.20, [r'$v_1$', r'$v_2$', r'$v_3$', r'$v_4$'], C_GREEN, fs=11, label='')
    ax.text(0.635, 0.615, 'v', fontsize=15, color=C_GREEN, weight='bold', ha='center')
    # 一行小注（符号注释）
    ax.text(0.5, 0.375, 'Pπ 第 i 行第 j 列 = 从 si 一步到 sj 的概率（随机矩阵：行非负、行和 1）；'
                        'rπ 第 i 分量 = 从 si 出发的期望即时奖励——一行矩阵式 ≡ n 个分量方程',
            ha='center', fontsize=11, color='#2C3E50', weight='bold')

    # ---- 行3：求逆 + 回代（指针图段之二）----
    ax.text(0.02, 0.32, '③ 求逆并回代：(I - γPπ)v = rπ', fontsize=12.5, color='#2C3E50', weight='bold')
    M = [[1, -0.9, 0, 0], [0, 1, 0, -0.9], [0, 0, 1, -0.9], [0, 0, 0, 0.1]]
    draw_matrix(ax, 0.155, 0.19, 0.24, 0.15, M, fc='white', ec='#2C3E50', fs=10)
    ax.text(0.155, 0.285, 'I - γPπ', fontsize=12, color='#2C3E50', weight='bold', ha='center')
    ax.text(0.155, 0.07, '下三角块：从最后一行解起', ha='center', fontsize=10, color=C_GRAY)
    # 回代链 v4→v3→v2→v1
    vals = [('v4 = 10', C_GREEN), ('v3 = 10', '#2ECC71'), ('v2 = 10', C_ORANGE), ('v1 = 9', C_RED)]
    xc = 0.385
    for i, (t, c) in enumerate(vals):
        box(ax, xc, 0.19, 0.10, 0.07, t, fc='white', ec=c, fs=11.5, tc=c, lw=2.0, weight='bold')
        if i < 3:
            arrow(ax, xc + 0.055, 0.19, xc + 0.098, 0.19, color='#2C3E50', lw=1.8)
        xc += 0.128
    ax.text(0.577, 0.27, '回代顺序：v4 → v3 → v2 → v1', ha='center', fontsize=10, color=C_GRAY)
    # 结果
    draw_colvector(ax, 0.905, 0.19, 0.05, 0.15, ['9', '10', '10', '10'], C_GREEN, fs=11)
    ax.text(0.905, 0.285, 'v', fontsize=14, color=C_GREEN, weight='bold', ha='center')
    ax.text(0.905, 0.10, '最终价值', ha='center', fontsize=10.5, color=C_GREEN)
    # 底注
    ax.text(0.5, 0.03, '目标态价值最高（10），一步可达目标者次之（10），距目标两步的 s1 最低（9）'
                       '——价值随"距离目标的步数"衰减，正是折扣的直观体现',
            ha='center', fontsize=11, color='#2C3E50', style='italic')

    fig.savefig(os.path.join(OUT, 'fig4-3.png'), dpi=200, bbox_inches='tight', pad_inches=0.05)
    plt.close(fig)
    print('fig4-3 OK')


# ============================================================
# 图 4-4 价值迭代收敛（聚焦误差每步 ×γ=0.9 的收缩段，k=0..6）
# ============================================================
def fig_4_4():
    # 迭代递推（例4.4 四状态模型，γ=0.9，v0=[0,0,0,0]）
    gamma = 0.9
    K = 25
    v = [0.0, 0.0, 0.0, 0.0]
    series1 = [v[0]]   # s1 → 9
    series2 = [v[1]]   # s2=s3=s4 → 10
    for k in range(K):
        nv = [0.0, 0.0, 0.0, 0.0]
        nv[0] = 0.0 + gamma * v[1]        # s1→s2
        nv[1] = 1.0 + gamma * v[3]        # s2→s4
        nv[2] = 1.0 + gamma * v[3]        # s3→s4
        nv[3] = 1.0 + gamma * v[3]        # s4→s4
        v = nv
        series1.append(v[0])
        series2.append(v[1])
    # 校验前四步与例4.5 一致
    assert abs(series1[1] - 0.0) < 1e-9 and abs(series2[1] - 1.0) < 1e-9
    assert abs(series1[2] - 0.9) < 1e-9 and abs(series2[2] - 1.9) < 1e-9
    assert abs(series1[3] - 1.71) < 1e-9 and abs(series2[3] - 2.71) < 1e-9
    assert abs(series1[4] - 2.439) < 1e-9 and abs(series2[4] - 3.439) < 1e-9
    # 误差序列（无穷范数）：e_k = ||vπ - vk||∞ = 10 * 0.9^k
    vpi = [9.0, 10.0, 10.0, 10.0]
    v = [0.0, 0.0, 0.0, 0.0]
    errs = [max(abs(vpi[i] - v[i]) for i in range(4))]
    for k in range(K):
        nv = [0.0, 0.0, 0.0, 0.0]
        nv[0] = 0.0 + gamma * v[1]
        nv[1] = 1.0 + gamma * v[3]
        nv[2] = 1.0 + gamma * v[3]
        nv[3] = 1.0 + gamma * v[3]
        v = nv
        errs.append(max(abs(vpi[i] - v[i]) for i in range(4)))
    # 校验：误差每步 ×0.9（聚焦段的依据）
    assert abs(errs[1] - 9.0) < 1e-9 and abs(errs[2] - 8.1) < 1e-9
    assert abs(errs[3] - 7.29) < 1e-9 and abs(errs[4] - 6.561) < 1e-9
    print('  前四步校验通过：', series1[:5], series2[:5])
    print('  误差序列(前8步)：', [round(e, 4) for e in errs[:8]])

    fig = plt.figure(figsize=(12.5, 5.6))

    # ---- ① 主图：分量曲线，聚焦 k=0..6（不再画 0..25 全范围）----
    ax = fig.add_axes([0.055, 0.14, 0.295, 0.78])
    kk = list(range(K + 1))
    FOCUS = 6
    ax.plot(kk[:FOCUS + 1], series2[:FOCUS + 1], color=C_BLUE, lw=2.4, marker='o', markersize=4,
            label='v2 = v3 = v4（s2/s3/s4 → 10）')
    ax.plot(kk[:FOCUS + 1], series1[:FOCUS + 1], color=C_ORANGE, lw=2.4, marker='s', markersize=4,
            label='v1（s1 → 9）')
    ax.axhline(10, color=C_BLUE, ls='--', lw=1.2, alpha=0.6)
    ax.axhline(9, color=C_ORANGE, ls='--', lw=1.2, alpha=0.6)
    # 关键数据点（k=1..4，与例4.5 一致）
    for k, (a, b) in enumerate([(0, 1), (0.9, 1.9), (1.71, 2.71), (2.439, 3.439)], start=1):
        ax.plot(k, b, 'o', color=C_BLUE, markersize=7, zorder=5)
        ax.plot(k, a, 's', color=C_ORANGE, markersize=7, zorder=5)
        if k <= 3:
            ax.text(k, b + 0.7, f'{b:g}', fontsize=9, ha='center', color=C_BLUE)
            ax.text(k, a - 0.9, f'{a:g}', fontsize=9, ha='center', color=C_ORANGE)
        else:
            ax.text(k, b + 0.7, '3.439', fontsize=9, ha='center', color=C_BLUE)
            ax.text(k, a - 0.9, '2.439', fontsize=9, ha='center', color=C_ORANGE)
    ax.set_xlabel('迭代步 k', fontsize=12)
    ax.set_ylabel(r'价值估计 $v_k$', fontsize=12)
    ax.set_xlim(0, FOCUS + 0.3)
    ax.set_ylim(-1.0, 11.3)
    ax.set_xticks(range(0, FOCUS + 1))
    ax.legend(loc='lower right', fontsize=9, framealpha=0.95)
    ax.grid(alpha=0.3)
    ax.set_title('① 分量逼近（聚焦 k=0..6）', fontsize=11, color='#2C3E50')

    # ---- ② 误差聚焦图：误差每步 ×γ=0.9（指针图段）----
    ax2 = fig.add_axes([0.42, 0.14, 0.30, 0.78])
    ax2.plot(kk[:FOCUS + 1], errs[:FOCUS + 1], color=C_RED, lw=2.6, marker='o', markersize=5,
             label=r'$\|v_\pi - v_k\|_\infty = 10 \times 0.9^k$')
    for k in range(FOCUS + 1):
        ax2.text(k, errs[k] + 0.45, f'{errs[k]:.2f}', fontsize=9.5, ha='center', color=C_RED)
    # "每步 ×0.9" 指针箭头（聚焦段标记）
    ax2.annotate('每步 ×0.9', xy=(2.0, errs[2] + 1.2), xytext=(3.6, 8.6),
                 fontsize=12, color=C_RED, weight='bold', ha='center',
                 arrowprops=dict(arrowstyle='->', color=C_RED, lw=2.0))
    ax2.axhline(0, color=C_GRAY, ls=':', lw=1.0)
    ax2.text(0.03, 0.97, r'误差界：$\|v_\pi - v_k\|_\infty \leq \gamma^k \|v_\pi - v_0\|_\infty,\ \gamma=0.9$',
             transform=ax2.transAxes, fontsize=10.5, va='top',
             bbox=dict(boxstyle='round,pad=0.4', fc=C_LGRAY, ec=C_GRAY, lw=1.0))
    ax2.set_xlabel('迭代步 k', fontsize=12)
    ax2.set_ylabel(r'误差 $\|v_\pi - v_k\|_\infty$', fontsize=12)
    ax2.set_xlim(0, FOCUS + 0.3)
    ax2.set_ylim(0, 11)
    ax2.set_xticks(range(0, FOCUS + 1))
    ax2.legend(loc='upper right', fontsize=9, framealpha=0.95)
    ax2.grid(alpha=0.3)
    ax2.set_title('② 误差收缩（聚焦段：每步 ×0.9）', fontsize=11, color='#2C3E50')

    # ---- ③ 右下小图：不同初值趋同 ----
    ax3 = fig.add_axes([0.80, 0.14, 0.175, 0.34])
    for v0, c, ls in [(0.0, C_BLUE, '-'), (8.0, C_ORANGE, '--')]:
        vv = [v0]
        for k in range(20):
            vv.append(1.0 + gamma * vv[-1])
        ax3.plot(range(21), vv, color=c, lw=2.0, ls=ls)
    ax3.axhline(10, color=C_GRAY, ls=':', lw=1.0)
    ax3.set_title('③ 不同初值趋同（0 与 8，20 步）', fontsize=9, color='#2C3E50')
    ax3.set_xlabel('k', fontsize=9)
    ax3.set_ylabel('v(s4)', fontsize=9)
    ax3.tick_params(labelsize=8)
    ax3.set_xlim(0, 20)
    ax3.set_ylim(0, 11)

    fig.savefig(os.path.join(OUT, 'fig4-4.png'), dpi=200, bbox_inches='tight', pad_inches=0.05)
    plt.close(fig)
    print('fig4-4 OK')


if __name__ == '__main__':
    fig_4_1()
    fig_4_2()
    fig_4_3()
    fig_4_4()
    print('ALL DONE ->', OUT)
