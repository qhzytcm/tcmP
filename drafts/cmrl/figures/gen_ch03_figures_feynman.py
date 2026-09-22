# -*- coding: utf-8 -*-
"""《中医场景强化学习》第3章 核心图生成脚本（v4 图内文字精简与字号规范版，图表工程师 2026-08-20）

【图内文字精简与字号规范】批次落地（与第1/2章统一）：
  ① 文字分层精简：每幅图图内只保留核心标注（节点名 + 1-2 个关键数值），每幅 ≤10 个标注；
     长描述、公式细节、次要数值（95% 带宽公式、卡片路径、区间、权重表等）全部移入图注；
  ② 字号规范：核心标注 fontsize≥11、节点名 ≥10、任何文字禁 <9pt；
  ③ 背景降噪：白底（去浅灰填充）、无网格线、去装饰框、框线细（lw≤1）、图例并入节点标注；
  ④ 忠实语义：回合/疗效/把握/证据等关键语义保留，数值锚点（0.2、-1/3、0.873、1.9 等）保留在图注；
  ⑤ 图注（md 与 Excel）补『e. 阅读引导』句。

数值口径与正文 3.2–3.6 节严格一致：
  - 图3-2：例3.1 前 5 次 +1,-1,+1,+1,-1 → x̄=0.2；σ=1；带宽 1.96σ/√n
  - 图3-5：例3.3 q̂=(−1+1−1)/3=−1/3；真值 0；γ=1
  - 图3-8：例3.5/例3.6 真值 w*=3；1/√k 违反②、1/k² 违反①（聚焦 0-400 步）
  - 图3-9：例3.7 归脾汤 x̄≈0.873、95% 区间 [0.79,0.96]；A/B/C 权重 1.0/0.7/0.4

生成：fig3-2 / fig3-5 / fig3-8 / fig3-9（覆盖 figures/ch03/*.png，SimHei + unicode_minus=False + dpi=200）
"""
import os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ch03')
os.makedirs(OUT, exist_ok=True)

# ---- 色板 ----
K   = '#111111'
DK  = '#333333'
MG  = '#666666'
LG  = '#999999'
B   = '#5b7d9e'   # 灰蓝：样本均值曲线/疗程1（图注"蓝色"）
DB  = '#3f6490'   # 深蓝：a_k=1/k 曲线（图注"深蓝"）
R   = '#a35555'   # 灰红：n=5 红色圆点（图注"红色"）
O   = '#c07a3f'   # 低饱和橙：疗程2/1√k/C级5000例（图注"橙色"）
G   = '#6f9e6f'   # 低饱和绿：疗程3/1k²/归脾汤（图注"绿色"）
Y   = '#c9b458'   # 低饱和黄：A级5例（图注"黄色"）
FILL_B = '#a9c2d6'  # 浅蓝带填充（alpha 0.20，彩度≈灰）
LG_B   = '#8faec6'  # 浅蓝带边界线

FS_NODE  = 10   # 节点名
FS_KEY   = 11   # 核心标注（关键数值）
FS_MAIN  = 12   # 强调数值
LW_BOX   = 1.0  # 框线细


def state_xy(s):
    """行优先编号 → 格心坐标 (col, row)"""
    i = int(s[1:]) - 1
    return (i % 3, i // 3)


def draw_grid_lite(ax):
    """3×3 九宫格轮廓（图3-5 左图）：白底黑细边；s6 禁区斜纹；s9 目标双线。
    格内不写编号（编号与科室语义移入图注），仅 s6/s9 两个核心标注。"""
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
    for (x0, y0, x1, y1) in [(-0.5, -0.5, 2.5, -0.5), (-0.5, 2.5, 2.5, 2.5),
                             (-0.5, -0.5, -0.5, 2.5), (2.5, -0.5, 2.5, 2.5)]:
        ax.plot([x0, x1], [y0, y1], color=K, lw=LW_BOX, solid_capstyle='butt', zorder=2)


# ---------------------------------------------------------------- 图 3-2
def fig3_2():
    """图 3-2 大数定律：样本均值收敛曲线（精简版）
    图内 5 个标注：真值 E[X]=0、n=5（x̄=0.2）、n=100 + 2 行图例并入标注；
    95% 带宽公式移入图注；聚焦 x 0-150、y ±0.62。
    """
    fig, ax = plt.subplots(figsize=(9.2, 4.8))
    n_max = 150
    ns = np.arange(1, n_max + 1)

    rng = np.random.default_rng(2026)
    x1 = rng.choice([-1, 1], size=n_max)
    x1[:5] = [1, -1, 1, 1, -1]
    m1 = np.cumsum(x1) / ns

    band = 1.96 * 1.0 / np.sqrt(ns)
    ax.fill_between(ns, -band, band, color=FILL_B, alpha=0.20, zorder=1)
    ax.plot(ns, band, color=LG_B, lw=0.8, ls=(0, (3, 3)), zorder=1)
    ax.plot(ns, -band, color=LG_B, lw=0.8, ls=(0, (3, 3)), zorder=1)

    ax.plot(ns, m1, color=B, lw=1.8, zorder=4)
    ax.axhline(0, color=K, lw=1.2, ls='--', zorder=2)

    # n=5 红色圆点；n=100 蓝色方块
    ax.plot(5, m1[4], 'o', color=R, ms=8, zorder=5)
    ax.plot(100, m1[99], 's', color=B, ms=6, zorder=5)

    # 图内 5 个标注
    ax.text(146, 0.09, r'$E[X] = 0$（真值）', ha='right', fontsize=FS_KEY,
            fontweight='bold', color=K)
    ax.annotate(r'n = 5：$\bar{x}$ = 0.2', xy=(5, m1[4]), xytext=(26, 0.42),
                fontsize=FS_KEY, color=R, fontweight='bold',
                arrowprops=dict(arrowstyle='->', color=R, lw=1.0))
    ax.annotate('n = 100', xy=(100, m1[99]), xytext=(102, 0.32),
                fontsize=FS_NODE, color=K,
                arrowprops=dict(arrowstyle='->', color=K, lw=1.0))
    ax.text(60, 0.52, '蓝线 = 样本均值', ha='left', fontsize=FS_NODE, color=B)
    ax.text(60, 0.30, '浅蓝带 = 95% 带宽', ha='left', fontsize=FS_NODE, color=LG_B)

    ax.set_xlim(-3, 158)
    ax.set_ylim(-0.62, 0.62)
    ax.set_xticks([0, 50, 100, 150])
    ax.set_yticks([-0.5, -0.25, 0, 0.25, 0.5])
    ax.set_xlabel('抛掷次数 n（聚焦 0-150）', fontsize=FS_KEY)
    ax.set_ylabel(r'样本均值 $\bar{x}_n$', fontsize=FS_KEY)
    for sp in ax.spines.values():
        sp.set_color(K)
        sp.set_linewidth(0.8)
    ax.tick_params(colors=K, labelsize=9)

    fig.savefig(os.path.join(OUT, 'fig3-2.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('fig3-2 done')


# ---------------------------------------------------------------- 图 3-5
def fig3_5():
    """图 3-5 三条回合、三个回报：有限样本下估计带着噪声（精简版）
    图内 10 个标注：左图 s6/s9 核心标注 2 + 三条疗程线标签 3 + 走法 1；
    右图三张疗效卡片 3 + q̂ 公式 1；卡片路径、把握值、噪声说明移入图注。
    """
    fig, (axL, axR) = plt.subplots(1, 2, figsize=(11.0, 5.4),
                                   gridspec_kw={'width_ratios': [1.05, 1.0]})

    # ---- 左：九宫格轮廓 + 三条疗程 ----
    axL.set_xlim(-0.6, 2.6)
    axL.set_ylim(2.6, -0.6)
    axL.set_aspect('equal')
    axL.axis('off')
    draw_grid_lite(axL)

    def arrow(p, q, color, lw, ls='-', z=4, rad=0.0):
        x1, y1 = state_xy(p)
        x2, y2 = state_xy(q)
        axL.annotate('', xy=(x2, y2), xytext=(x1, y1),
                     arrowprops=dict(arrowstyle='-|>', color=color, lw=lw,
                                     linestyle=ls, connectionstyle=f'arc3,rad={rad}'),
                     zorder=z)

    # 共享段 s1→s2→s3（浅灰细线）
    arrow('s1', 's2', LG, 1.2, z=3)
    arrow('s2', 's3', LG, 1.2, z=3)
    # 疗程1（蓝色实线）：s3→s6 落入禁区
    arrow('s3', 's6', B, 1.8, rad=0.18)
    # 疗程2（橙色虚线）：s3→s6 同路径不同次
    arrow('s3', 's6', O, 1.5, ls=(0, (5, 3)), rad=-0.18)
    # 疗程3（绿色实线）：s3→s9 到达目标
    arrow('s3', 's9', G, 1.8, rad=0.42)

    # 左图 6 个标注
    axL.text(1.0, 0.12, '禁区 r = -1', ha='center', fontsize=FS_KEY, color=K,
             fontweight='bold')
    axL.text(2.0, 2.62, '目标 r = +1', ha='center', fontsize=FS_KEY, color=K,
             fontweight='bold')
    axL.text(1.75, 0.72, '疗程1 G = -1', ha='center', fontsize=FS_NODE, color=B,
             fontweight='bold')
    axL.text(1.62, 1.05, '疗程2 G = -1', ha='center', fontsize=FS_NODE, color=O,
             fontweight='bold')
    axL.text(2.35, 1.45, '疗程3 G = +1', ha='center', fontsize=FS_NODE, color=G,
             fontweight='bold')
    axL.text(0.5, 2.10, '走法"总是向右"', fontsize=FS_NODE, color=DK, fontweight='bold')

    # ---- 右：回报汇总卡片（白底黑细边）----
    axR.set_xlim(0, 9.4)
    axR.set_ylim(0, 10)
    axR.axis('off')
    cards = [('疗程1  G1 = -1', r''), ('疗程2  G2 = -1', r''), ('疗程3  G3 = +1', r'')]
    y0 = 8.2
    for i, (name, _g) in enumerate(cards):
        y = y0 - i * 1.75
        axR.add_patch(Rectangle((0.6, y - 0.60), 5.4, 1.05, facecolor='white',
                                edgecolor=K, lw=LW_BOX, zorder=2))
        axR.text(3.3, y, name, ha='center', va='center', fontsize=FS_KEY,
                 zorder=3, color=K, fontweight='bold')
    # 大括号（三条回报 → 平均）
    axR.plot([6.35, 6.35], [y0 - 0.35, y0 - 3.25], color=K, lw=1.2, zorder=3)
    axR.annotate('', xy=(6.35, y0 - 3.7), xytext=(6.35, y0 - 3.35),
                 arrowprops=dict(arrowstyle='-|>', color=K, lw=1.2), zorder=3)
    axR.text(6.85, 3.35, r'$\hat{q}_\pi(s_1, a_2) = -1/3$',
             fontsize=FS_MAIN, fontweight='bold', color=K, zorder=3)

    fig.savefig(os.path.join(OUT, 'fig3-5.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('fig3-5 done')


# ---------------------------------------------------------------- 图 3-8
def fig3_8():
    """图 3-8 RM 定理的两个步长条件（精简版）
    图内 7 个标注：真值 w*=3、条件框、四条曲线末端标签、结论 1 行；
    图例删除（标签直接标曲线末端），聚焦 0-400 步、y -2~6.2。
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

    ax.axhline(3, color=K, lw=1.2, ls='--', zorder=2)
    ax.plot(ks, w_1k, color=DB, lw=1.8, zorder=5)
    ax.plot(ks, w_1sk, color=O, lw=1.4, ls=(0, (6, 3)), zorder=4)
    ax.plot(ks, w_1k2, color=G, lw=1.4, ls=(0, (2, 2)), zorder=4)
    ax.plot(ks, w_const, color=LG, lw=1.0, zorder=3)

    # 图内 7 个标注
    ax.text(386, 3.10, r'真值 $w^* = 3$', fontsize=FS_KEY, color=K, fontweight='bold')
    ax.text(0.985, 0.97,
            r'① $\sum_{k=1}^{\infty} a_k = \infty$　能走远' + '\n' +
            r'② $\sum_{k=1}^{\infty} a_k^2 < \infty$　能平噪',
            transform=ax.transAxes, ha='right', va='top', fontsize=FS_KEY,
            color=K, linespacing=1.6,
            bbox=dict(boxstyle='square,pad=0.6', facecolor='white',
                      edgecolor=K, lw=LW_BOX))
    ax.text(400, w_1k[-1], r'$a_k=1/k$', ha='left', va='center',
            fontsize=FS_NODE, color=DB, fontweight='bold')
    ax.text(400, w_1sk[-1], r'$a_k=1/\sqrt{k}$', ha='left', va='center',
            fontsize=FS_NODE, color=O, fontweight='bold')
    ax.text(400, w_1k2[-1], r'$a_k=1/k^2$', ha='left', va='center',
            fontsize=FS_NODE, color=G, fontweight='bold')
    ax.text(400, w_const[-1], '常数 0.1', ha='left', va='center',
            fontsize=FS_NODE, color=LG, fontweight='bold')
    ax.text(205, -1.75, '步长必须"慢到能走远，快到能平噪"，缺一不可',
            ha='center', fontsize=FS_NODE, color=DK, fontweight='bold')

    ax.set_xlim(-10, 420)
    ax.set_ylim(-2.0, 6.2)
    ax.set_xticks([0, 100, 200, 300, 400])
    ax.set_yticks([-2, 0, 2, 4, 6])
    ax.set_xlabel('迭代次数 k（聚焦 0-400）', fontsize=FS_KEY)
    ax.set_ylabel(r'疗效把握参数 $w_k$', fontsize=FS_KEY)
    for sp in ax.spines.values():
        sp.set_color(K)
        sp.set_linewidth(0.8)
    ax.tick_params(colors=K, labelsize=9)

    fig.savefig(os.path.join(OUT, 'fig3-8.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('fig3-8 done')


# ---------------------------------------------------------------- 图 3-9
def fig3_9():
    """图 3-9 质量 × 数量：疗效证据的二维评价坐标系（精简版）
    图内 8 个标注：四象限含义 4 + 三个数据点名称（归脾汤含 x̄≈0.873）+ 权重 1 行；
    95% 区间、副标注移入图注；权重表压缩为 1 行文本（图例并入节点标注）。
    """
    fig, ax = plt.subplots(figsize=(8.8, 6.2))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)

    # 四象限（白底，无浅灰填充）
    ax.axvline(5, color=K, lw=1.0, zorder=1)
    ax.axhline(5, color=K, lw=1.0, zorder=1)

    # 象限含义（4 个标注）
    ax.text(7.5, 8.6, '高等级高把握\n= 强推荐依据', ha='center', fontsize=FS_KEY,
            fontweight='bold', color=K, zorder=3)
    ax.text(2.5, 8.6, '高等级低把握\n= 可信但不够精确', ha='center', fontsize=FS_NODE,
            color=DK, zorder=3)
    ax.text(7.5, 3.6, '低等级高把握\n= 精确但源头可疑', ha='center', fontsize=FS_NODE,
            color=DK, zorder=3)
    ax.text(2.5, 3.6, '低等级低把握\n= 弱参考', ha='center', fontsize=FS_NODE,
            color=MG, zorder=3)

    # 数据点（3 个标注，含关键数值 0.873）
    pts = [
        (7.7, 8.0, r'归脾汤·失眠·心脾两虚', G, r'$\bar{x}\approx 0.873$', 'o', G, 15),
        (2.3, 8.0, 'A 级仅 5 例', Y, '', 'o', 'white', 13),
        (7.7, 1.8, 'C 级 5000 例', O, '', 'o', 'white', 13),
    ]
    for x, y, name, c, sub, mk, mfc, ms in pts:
        ax.plot(x, y, mk, color=c, ms=ms, zorder=5,
                markerfacecolor=mfc, markeredgewidth=1.0)
        ax.text(x, y - 1.05, name, ha='center', fontsize=FS_NODE, fontweight='bold',
                color=DK, zorder=5)
        if sub:
            ax.text(x, y - 1.75, sub, ha='center', fontsize=FS_KEY, fontweight='bold',
                    color=K, zorder=5)

    # 权重（图例并入节点标注：1 行）
    ax.text(5.0, 0.45, '等级权重：A = 1.0 · B = 0.7 · C = 0.4',
            ha='center', fontsize=FS_NODE, color=DK, zorder=5)

    ax.set_xlabel('把握程度（标准误 / 区间宽度，向右越大）', fontsize=FS_KEY)
    ax.set_ylabel('证据等级（A/B/C，向上越高）', fontsize=FS_KEY)
    ax.set_xticks([0, 5, 10])
    ax.set_xticklabels(['低把握', '中', '高把握'], fontsize=FS_NODE)
    ax.set_yticks([0, 5, 10])
    ax.set_yticklabels(['C 级', 'B 级', 'A 级'], fontsize=FS_NODE)
    for sp in ax.spines.values():
        sp.set_color(K)
        sp.set_linewidth(0.8)
    ax.tick_params(colors=K, labelsize=9)

    fig.savefig(os.path.join(OUT, 'fig3-9.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('fig3-9 done')


if __name__ == '__main__':
    fig3_2()
    fig3_5()
    fig3_8()
    fig3_9()
    print('ALL DONE ->', OUT)
