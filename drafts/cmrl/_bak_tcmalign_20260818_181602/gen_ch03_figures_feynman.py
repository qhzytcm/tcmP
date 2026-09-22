# -*- coding: utf-8 -*-
"""《中医场景强化学习》第3章 核心图生成脚本（v3 费曼图标准重构版，图表工程师 2026-08-18）

费曼图重构标准落地（7 条，与第1/2章一致）：
  ① 节点（方块/圆/数据点）+ 连线（曲线/直线/虚线/点线/箭头）为主体结构；
  ② 黑白灰线稿为主，低饱和点缀色按图注颜色词对齐（v4 颜色对齐批次）：
       灰蓝 #5b7d9e = 蓝色（样本均值曲线/回合1/蓝方块）；深蓝 #3f6490 = 1/k 深蓝实线；
       灰红 #a35555 = 红色（n=5 圆点）；低饱和橙 #c07a3f = 橙色（回合2/1√k/C级5000例）；
       低饱和绿 #6f9e6f = 绿色（回合3/1k²/归脾汤）；低饱和黄 #c9b458 = 黄色（A级5例）；
       浅蓝 #a9c2d6/边界 #8faec6 = 95% 带宽（浅蓝带，alpha 低、彩度近灰）；
  ③ 极简：去圆角/渐变/阴影/背景网格/大面积色块；
  ④ 方向明确：时间轴/迭代方向由曲线走向与坐标轴表达，关键转移用箭头；
  ⑤ 信息密度高：数值点、公式、概率直接标注在节点与线上；
  ⑥ 聚焦图段延续：继承 v2 聚焦坐标（fig3-2 x 0-150 y ±0.62；fig3-8 x 0-400 y -2~6.2）；
  ⑦ 中医场景语义保留：回合=诊疗过程、估计=疗效统计、证据=文献质量。

数值口径与正文 3.2–3.6 节严格一致：
  - 图3-2：例3.1 前 5 次 +1,-1,+1,+1,-1 → x̄=0.2；σ=1；带宽 1.96σ/√n
  - 图3-5：例3.3 q̂=(−1+1−1)/3=−1/3；真值 0；γ=1
  - 图3-8：例3.5/例3.6 真值 w*=3；1/√k 违反②、1/k² 违反①（聚焦 0-400 步）
  - 图3-9：例3.7 归脾汤 x̄≈0.873、95% 区间 [0.79,0.96]；A/B/C 权重 1.0/0.7/0.4

生成：fig3-2 / fig3-5 / fig3-8 / fig3-9（覆盖 figures/ch03/*.png，SimHei + unicode_minus=False + dpi=200；
v4 批次：图注颜色词→图体元素对齐，未提元素保持黑白灰，彩色像素占比 <5%）
"""
import os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Patch
from matplotlib.lines import Line2D

plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ch03')
os.makedirs(OUT, exist_ok=True)

# ---- 费曼色板 ----
K   = '#111111'
DK  = '#333333'
MG  = '#666666'
LG  = '#999999'
B   = '#5b7d9e'   # 灰蓝：样本均值曲线/回合1/蓝方块（图注"蓝色"）
DB  = '#3f6490'   # 深蓝：a_k=1/k 曲线（图注"深蓝"）
R   = '#a35555'   # 灰红：n=5 红色圆点（图注"红色"）
O   = '#c07a3f'   # 低饱和橙：回合2/1√k/C级5000例（图注"橙色"）
G   = '#6f9e6f'   # 低饱和绿：回合3/1k²/归脾汤（图注"绿色"）
Y   = '#c9b458'   # 低饱和黄：A级5例（图注"黄色"）
FILL_B = '#a9c2d6'  # 浅蓝带填充（alpha 0.20，彩度≈灰）
LG_B   = '#8faec6'  # 浅蓝带边界线
G0  = '#efefef'
G1  = '#f4f4f4'


def state_xy(s):
    """行优先编号 → 格心坐标 (col, row)"""
    i = int(s[1:]) - 1
    return (i % 3, i // 3)


def draw_grid(ax):
    """3×3 九宫格（费曼版，与第1章图1-1同布局）：s6 禁区斜纹灰红边、s9 目标黑粗边。"""
    for s in ['s1', 's2', 's3', 's4', 's5', 's6', 's7', 's8', 's9']:
        col, row = state_xy(s)
        if s == 's6':
            fc, ec, lw, ht = G1, K, 2.0, '///'
        elif s == 's9':
            fc, ec, lw, ht = G0, K, 2.6, None
        else:
            fc, ec, lw, ht = 'white', K, 1.2, None
        ax.add_patch(Rectangle((col - 0.5, row - 0.5), 1, 1, facecolor=fc,
                               edgecolor=ec, lw=lw, hatch=ht, zorder=1))
        ax.text(col, row - 0.12, s, ha='center', va='center',
                fontsize=13, fontweight='bold', zorder=3)
        if s == 's6':
            ax.text(col, row + 0.32, '禁区\nr=-1', ha='center', va='center',
                    fontsize=7.5, color=K, zorder=3)
        if s == 's9':
            ax.text(col, row + 0.32, '目标\nr=+1', ha='center', va='center',
                    fontsize=7.5, color=K, zorder=3)
    for (x0, y0, x1, y1) in [(-0.5, -0.5, 2.5, -0.5), (-0.5, 2.5, 2.5, 2.5),
                             (-0.5, -0.5, -0.5, 2.5), (2.5, -0.5, 2.5, 2.5)]:
        ax.plot([x0, x1], [y0, y1], color=K, lw=3.2, solid_capstyle='butt', zorder=2)


# ---------------------------------------------------------------- 图 3-2
def fig3_2():
    """图 3-2 大数定律：样本均值收敛曲线（费曼版）
    连线 = 蓝色样本均值曲线 + 黑色虚线真值 E[X]=0 + 浅蓝 95% 带宽（浅蓝带+浅蓝细线边界）；
    节点 = n=5 红色圆点（x̄=0.2）、n=100 蓝色方块（向 0 靠拢）；
    聚焦 = x 0-150、y ±0.62（延续 v2）；去背景网格。
    """
    fig, ax = plt.subplots(figsize=(9.2, 4.8))
    n_max = 150
    ns = np.arange(1, n_max + 1)

    rng = np.random.default_rng(2026)
    x1 = rng.choice([-1, 1], size=n_max)
    x1[:5] = [1, -1, 1, 1, -1]
    m1 = np.cumsum(x1) / ns

    band = 1.96 * 1.0 / np.sqrt(ns)
    ax.fill_between(ns, -band, band, color=FILL_B, alpha=0.20, zorder=1,
                    label=r'$95\%$ 带宽 $\mu \pm 1.96\sigma/\sqrt{n}$（σ = 1）')
    ax.plot(ns, band, color=LG_B, lw=0.8, ls=(0, (3, 3)), zorder=1)
    ax.plot(ns, -band, color=LG_B, lw=0.8, ls=(0, (3, 3)), zorder=1)

    ax.plot(ns, m1, color=B, lw=2.4, zorder=4, label='样本均值曲线（蓝色）')
    ax.axhline(0, color=K, lw=1.6, ls='--', zorder=2)
    ax.text(146, 0.09, r'$E[X] = 0$（真值）', ha='right', fontsize=10.5, color=K)

    # n=5 红色圆点；n=100 蓝色方块
    ax.plot(5, m1[4], 'o', color=R, ms=8, zorder=5)
    ax.annotate(r'n = 5：$\bar{x}$ = 0.2（正文例3.1）', xy=(5, m1[4]),
                xytext=(26, 0.42), fontsize=10, color=R,
                arrowprops=dict(arrowstyle='->', color=R, lw=1.2))
    ax.plot(100, m1[99], 's', color=B, ms=6, zorder=5)
    ax.annotate('n = 100：均值明显向 0 靠拢', xy=(100, m1[99]),
                xytext=(102, 0.32), fontsize=10, color=K,
                arrowprops=dict(arrowstyle='->', color=K, lw=1.2))

    ax.set_xlim(-3, 158)
    ax.set_ylim(-0.62, 0.62)
    ax.set_xticks([0, 50, 100, 150])
    ax.set_yticks([-0.5, -0.25, 0, 0.25, 0.5])
    ax.set_xlabel('抛掷次数 n（聚焦 0-150）', fontsize=11)
    ax.set_ylabel(r'样本均值 $\bar{x}_n$', fontsize=11)
    for sp in ax.spines.values():
        sp.set_color(K)
        sp.set_linewidth(1.2)
    ax.tick_params(colors=K)
    ax.legend(loc='upper right', fontsize=9, frameon=True)

    fig.savefig(os.path.join(OUT, 'fig3-2.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('fig3-2 done')


# ---------------------------------------------------------------- 图 3-5
def fig3_5():
    """图 3-5 三条回合、三个回报：有限样本下估计带着噪声（费曼版）
    左：节点 = 九宫格；连线 = 共享段灰色细线 + 回合1 蓝色实线 + 回合2 橙色虚线
        + 回合3 绿色实线（正回报），方向箭头；
    右：回报卡片黑白化，大括号 + q̂=(−1+1−1)/3=−1/3 公式 + 真值 q=0 + 噪声警示。
    """
    fig, (axL, axR) = plt.subplots(1, 2, figsize=(11.0, 5.4),
                                   gridspec_kw={'width_ratios': [1.05, 1.0]})

    # ---- 左：九宫格 + 三条回合 ----
    axL.set_xlim(-0.6, 2.6)
    axL.set_ylim(2.6, -0.6)
    axL.set_aspect('equal')
    axL.axis('off')
    draw_grid(axL)

    def arrow(p, q, color, lw, ls='-', z=4, rad=0.0):
        x1, y1 = state_xy(p)
        x2, y2 = state_xy(q)
        axL.annotate('', xy=(x2, y2), xytext=(x1, y1),
                     arrowprops=dict(arrowstyle='-|>', color=color, lw=lw,
                                     linestyle=ls, connectionstyle=f'arc3,rad={rad}'),
                     zorder=z)

    # 共享段 s1→s2→s3（浅灰细线）
    arrow('s1', 's2', LG, 1.6, z=3)
    arrow('s2', 's3', LG, 1.6, z=3)
    # 回合1（蓝色实线）：s3→s6 落入禁区
    arrow('s3', 's6', B, 3.2, rad=0.18)
    # 回合2（橙色虚线）：s3→s6 同路径不同次
    arrow('s3', 's6', O, 2.6, ls=(0, (5, 3)), rad=-0.18)
    # 回合3（绿色实线）：s3→s9 到达目标
    arrow('s3', 's9', G, 3.2, rad=0.42)
    axL.text(0.5, 2.10, '策略"总是向右"', fontsize=9.5, color=DK)
    axL.text(0.5, 1.86, '（例3.3，γ = 1）', fontsize=9.5, color=DK)

    handles = [
        Line2D([0], [0], color=B, lw=3, label=r'回合1：s1→s2→s3→s6（回报 $G_1 = -1$）'),
        Line2D([0], [0], color=O, lw=2.4, ls=(0, (5, 3)),
               label=r'回合2：s1→s2→s3→s6（回报 $G_2 = -1$）'),
        Line2D([0], [0], color=G, lw=3, label=r'回合3：s1→s2→s3→s9（回报 $G_3 = +1$）'),
    ]
    axL.legend(handles=handles, loc='lower center', bbox_to_anchor=(0.5, -0.12),
               ncol=1, fontsize=8.8, frameon=True, handlelength=2.2)

    # ---- 右：回报汇总（黑白卡片） ----
    axR.set_xlim(0, 9.4)
    axR.set_ylim(0, 10)
    axR.axis('off')
    cards = [
        ('回合1：s1→s2→s3→s6', r'$G_1 = -1$', K),
        ('回合2：s1→s2→s3→s6', r'$G_2 = -1$', K),
        ('回合3：s1→s2→s3→s9', r'$G_3 = +1$', K),
    ]
    y0 = 8.2
    for i, (name, g, gc) in enumerate(cards):
        y = y0 - i * 1.75
        axR.add_patch(Rectangle((0.6, y - 0.60), 5.4, 1.05, facecolor='white',
                                edgecolor=K, lw=1.6, zorder=2))
        axR.text(1.0, y, name, ha='left', va='center', fontsize=10, zorder=3, color=K)
        axR.text(5.7, y, g, ha='center', va='center', fontsize=12.5,
                 fontweight='bold', color=gc, zorder=3)
    # 大括号（三条回报 → 平均）
    axR.plot([6.35, 6.35], [y0 - 0.35, y0 - 3.25], color=K, lw=2.2, zorder=3)
    axR.annotate('', xy=(6.35, y0 - 3.7), xytext=(6.35, y0 - 3.35),
                 arrowprops=dict(arrowstyle='-|>', color=K, lw=2.2), zorder=3)
    axR.text(6.85, 3.35, r'$\hat{q}_\pi(s_1,\ a_2) = \frac{(-1+1-1)}{3} = -\frac{1}{3}$',
             fontsize=12.5, fontweight='bold', color=K, zorder=3)
    axR.text(6.85, 2.78, '真值 q = 0（s3 向右落 s6 与 s9 各 0.5）',
             fontsize=9.5, color=K, zorder=3)
    axR.text(6.85, 2.40, '差距 = 噪声（数据版给出的是噪声值）',
             fontsize=9.5, color=K, zorder=3, fontweight='bold')
    axR.text(6.85, 1.98, '有限样本下，策略可能被噪声误导',
             fontsize=9.5, color=K, zorder=3)

    fig.savefig(os.path.join(OUT, 'fig3-5.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('fig3-5 done')


# ---------------------------------------------------------------- 图 3-8
def fig3_8():
    """图 3-8 RM 定理的两个步长条件（费曼版）
    连线 = 4 条曲线按颜色+线型区分：1/k 深蓝实线（满足①②）、1/√k 橙色虚线（违反②）、
           1/k² 绿色点线（违反①）、常数步长灰色细线（对比）；黑色虚线真值 w*=3；
    节点 = 右上黑边条件框（RM 两条件）；
    聚焦 = x 0-400、y -2~6.2；去背景网格。
    """
    fig, ax = plt.subplots(figsize=(10.2, 5.6))
    n_max = 400
    ks = np.arange(1, n_max + 1)
    rng = np.random.default_rng(2026)
    eta = rng.normal(0, 1, n_max)

    def simulate(a, eta):
        w = np.zeros(n_max)
        w[0] = 0.0
        for k in range(1, n_max):
            w[k] = w[k - 1] - a(k) * (w[k - 1] - 3 + eta[k - 1])
        return w

    w_1k = simulate(lambda k: 1.0 / k, eta)
    eta_loud = eta * 2.0
    w_1sk = simulate(lambda k: 1.0 / np.sqrt(k), eta=eta_loud)
    eta_k2 = eta.copy()
    eta_k2[0] = 0.5
    w_1k2 = simulate(lambda k: 1.0 / (k ** 2), eta=eta_k2)
    w_const = simulate(lambda k: 0.1, eta)

    ax.axhline(3, color=K, lw=1.6, ls='--', zorder=2)
    ax.text(386, 3.10, r'真值 $w^* = 3$', fontsize=11, color=K)

    ax.plot(ks, w_1k, color=DB, lw=2.6, zorder=5, label=r'$a_k = 1/k$：平稳收敛（满足①+②）')
    ax.plot(ks, w_1sk, color=O, lw=1.8, ls=(0, (6, 3)), zorder=4,
            label=r'$a_k = 1/\sqrt{k}$：抖动渐大（违反②）')
    ax.plot(ks, w_1k2, color=G, lw=1.8, ls=(0, (2, 2)), zorder=4,
            label=r'$a_k = 1/k^2$：停在半路（违反①）')
    ax.plot(ks, w_const, color=LG, lw=1.2, zorder=3,
            label=r'常数步长 $\alpha = 0.1$：跟随但持续抖动（对比）')

    # 右上部条件框（白底黑边直角框）
    ax.text(0.985, 0.97,
            r'RM 定理两个条件：' + '\n' +
            r'① $\sum_{k=1}^{\infty} a_k = \infty$　能走远' + '\n' +
            r'② $\sum_{k=1}^{\infty} a_k^2 < \infty$　能平噪',
            transform=ax.transAxes, ha='right', va='top', fontsize=10.5,
            color=K, linespacing=1.6,
            bbox=dict(boxstyle='square,pad=0.6', facecolor='white',
                      edgecolor=K, lw=1.6))

    ax.set_xlim(-10, 420)
    ax.set_ylim(-2.0, 6.2)
    ax.set_xticks([0, 100, 200, 300, 400])
    ax.set_yticks([-2, 0, 2, 4, 6])
    ax.set_xlabel('迭代次数 k（聚焦 0-400）', fontsize=11)
    ax.set_ylabel(r'估计 $w_k$', fontsize=11)
    for sp in ax.spines.values():
        sp.set_color(K)
        sp.set_linewidth(1.2)
    ax.tick_params(colors=K)
    ax.legend(loc='lower right', fontsize=9, frameon=True)

    fig.savefig(os.path.join(OUT, 'fig3-8.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('fig3-8 done')


# ---------------------------------------------------------------- 图 3-9
def fig3_9():
    """图 3-9 质量 × 数量：疗效证据的二维评价坐标系（费曼版）
    节点 = 三个数据点（绿色实心圆=归脾汤、黄色空心圆=A级5例、橙色空心圆=C级5000例）
          + 右下角黑白权重表；
    连线 = 黑色十字中轴（四象限），右上"高等级高把握"为指针图段；
    灰阶象限底：右上白（重点）、左上/左下/右下浅灰递增。
    """
    fig, ax = plt.subplots(figsize=(8.8, 6.2))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)

    # 四象限（浅灰阶，右上重点留白）
    ax.add_patch(Rectangle((5, 5), 5, 5, facecolor='white', edgecolor='none', zorder=0))
    ax.add_patch(Rectangle((0, 5), 5, 5, facecolor=G1, edgecolor='none', zorder=0))
    ax.add_patch(Rectangle((5, 0), 5, 5, facecolor='#ececec', edgecolor='none', zorder=0))
    ax.add_patch(Rectangle((0, 0), 5, 5, facecolor='#f7f7f7', edgecolor='none', zorder=0))
    ax.axvline(5, color=K, lw=1.6, zorder=1)
    ax.axhline(5, color=K, lw=1.6, zorder=1)

    # 象限含义（右上黑粗=指针图段）
    ax.text(7.5, 8.6, '高等级高把握\n= 强推荐依据', ha='center', fontsize=11,
            fontweight='bold', color=K, zorder=3)
    ax.text(2.5, 8.6, '高等级低把握\n= 可信但不够精确', ha='center', fontsize=11,
            color=DK, zorder=3)
    ax.text(7.5, 3.6, '低等级高把握\n= 精确但源头可疑', ha='center', fontsize=11,
            color=DK, zorder=3)
    ax.text(2.5, 3.6, '低等级低把握\n= 弱参考', ha='center', fontsize=11,
            color=MG, zorder=3)

    # 数据点：黑实心圆 / 空心圆 / 灰红空心三角
    pts = [
        (7.7, 8.0, r'归脾汤·失眠·心脾两虚', G, 10.5,
         'o', G, 15,
         r'A 级、n = 30、$\bar{x}$ ≈ 0.873' + '\n' + r'95% 区间 [0.79, 0.96]（半宽 ≈ 0.086）'),
        (2.3, 8.0, 'A 级仅 5 例', Y, 9.5,
         'o', 'white', 13,
         '可信但不够精确'),
        (7.7, 1.8, 'C 级 5000 例', O, 9.5,
         'o', 'white', 13,
         '精确但源头可疑'),
    ]
    for x, y, name, c, fs, mk, mfc, ms, sub in pts:
        ax.plot(x, y, mk, color=c, ms=ms, zorder=5,
                markerfacecolor=mfc, markeredgewidth=1.8)
        ax.text(x, y - 1.05, name, ha='center', fontsize=fs, fontweight='bold',
                color=DK, zorder=5)
        ax.text(x, y - 1.75, sub, ha='center', fontsize=8.8, color=DK, zorder=5)

    # 权重小表（黑白）
    tbl_data = [['A', '1.0'], ['B', '0.7'], ['C', '0.4']]
    tbl = ax.table(cellText=tbl_data, colLabels=['等级', '权重'], loc='lower right',
                   cellLoc='center', bbox=[0.745, 0.06, 0.22, 0.20])
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(8.5)
    for j in range(2):
        c = tbl[0, j]
        c.set_facecolor(DK)
        c.set_text_props(color='white', fontweight='bold')
        c.set_edgecolor(K)

    ax.set_xlabel('把握程度（标准误 / 区间宽度，向右越大）', fontsize=11)
    ax.set_ylabel('证据等级（A/B/C，向上越高）', fontsize=11)
    ax.set_xticks([0, 5, 10])
    ax.set_xticklabels(['低把握', '中', '高把握'], fontsize=10)
    ax.set_yticks([0, 5, 10])
    ax.set_yticklabels(['C 级', 'B 级', 'A 级'], fontsize=10)
    for sp in ax.spines.values():
        sp.set_color(K)
        sp.set_linewidth(1.4)
    ax.tick_params(colors=K)

    fig.savefig(os.path.join(OUT, 'fig3-9.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('fig3-9 done')


if __name__ == '__main__':
    fig3_2()
    fig3_5()
    fig3_8()
    fig3_9()
    print('ALL DONE ->', OUT)
