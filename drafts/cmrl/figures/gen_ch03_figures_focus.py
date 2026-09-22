# -*- coding: utf-8 -*-
"""《中医场景强化学习》第3章 核心图生成脚本（v2 聚焦版，图表工程师）

聚焦原则（用户要求）：
  - 图体只保留'能代表含义的图段'——收紧 figsize 与 xlim/ylim/xticks/yticks，
    聚焦关键区域（如 fig3-2 只保留真值 0 附近 ±0.6 的收敛带）；
  - 图题由 Excel sheet 图题行承担（居中黑体），图内不再重复大标题；
  - 图注由 Excel sheet 图注行承担（左顶格），四要素：a.对接正文提示语 /
    b.线的注释 / c.符号的注释 / d.代表含义的指针图段；
  - 图内底部临床对照行移除（信息并入图注四要素 d）。

生成：fig3-2 / fig3-5 / fig3-8 / fig3-9（覆盖 figures/ch03/*.png）
数值口径与正文 3.2–3.6 节严格一致：
  - 图3-2：例3.1 前 5 次 +1,-1,+1,+1,-1 → x̄ = 0.2；σ = 1；带宽 1.96σ/√n
  - 图3-5：例3.3 q̂ = (−1+1−1)/3 = −1/3；真值 0；γ = 1
  - 图3-8：例3.5/例3.6 真值 w* = 3；1/√k 违反②、1/k² 违反①（聚焦 0–400 步）
  - 图3-9：例3.7 归脾汤 x̄ ≈ 0.873、95% 区间 [0.79, 0.96]；A/B/C 权重 1.0/0.7/0.4
"""
import os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyBboxPatch
from matplotlib.lines import Line2D

plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ch03')
os.makedirs(OUT, exist_ok=True)


def state_xy(s):
    """行优先编号 → 格心坐标 (col, row)"""
    i = int(s[1:]) - 1
    return (i % 3, i // 3)


def draw_grid(ax):
    """绘制 3×3 九宫格（与第1章图 1-1 同布局）：s6 禁区橙、s9 目标绿"""
    for s in ['s1', 's2', 's3', 's4', 's5', 's6', 's7', 's8', 's9']:
        col, row = state_xy(s)
        fc = '#f5b041' if s == 's6' else ('#82e0aa' if s == 's9' else 'white')
        ax.add_patch(Rectangle((col - 0.5, row - 0.5), 1, 1, facecolor=fc,
                               edgecolor='#999999', lw=1.2, zorder=1))
        ax.text(col, row - 0.12, s, ha='center', va='center',
                fontsize=13, fontweight='bold', zorder=3)
        if s == 's6':
            ax.text(col, row + 0.32, '禁区\nr=-1', ha='center', va='center',
                    fontsize=7.5, color='#b03a2e', zorder=3)
        if s == 's9':
            ax.text(col, row + 0.32, '目标\nr=+1', ha='center', va='center',
                    fontsize=7.5, color='#1e8449', zorder=3)
    for (x0, y0, x1, y1) in [(-0.5, -0.5, 2.5, -0.5), (-0.5, 2.5, 2.5, 2.5),
                             (-0.5, -0.5, -0.5, 2.5), (2.5, -0.5, 2.5, 2.5)]:
        ax.plot([x0, x1], [y0, y1], color='#333333', lw=3.2,
                solid_capstyle='butt', zorder=2)


def fig3_2():
    """图 3-2 大数定律：样本均值收敛曲线（聚焦：只保留真值 0 附近 ±0.6 收敛带）"""
    fig, ax = plt.subplots(figsize=(9.2, 4.8))
    n_max = 150                       # 聚焦：缩短到 150 次（正文 n=100 标注点保留）
    ns = np.arange(1, n_max + 1)

    rng = np.random.default_rng(2026)
    x1 = rng.choice([-1, 1], size=n_max)
    x1[:5] = [1, -1, 1, 1, -1]        # 前 5 次 +1,-1,+1,+1,-1（正文例3.1）
    m1 = np.cumsum(x1) / ns

    # 95% 带宽 μ ± 1.96σ/√n（σ = 1）
    band = 1.96 * 1.0 / np.sqrt(ns)
    ax.fill_between(ns, -band, band, color='#1a5276', alpha=0.08, zorder=1,
                    label=r'95% 带宽 $\mu \pm 1.96\sigma/\sqrt{n}$（σ = 1）')

    ax.plot(ns, m1, color='#2e86c1', lw=2.2, zorder=4, label='样本均值曲线')

    # 真值线
    ax.axhline(0, color='#333333', lw=1.6, ls='--', zorder=2)
    ax.text(146, 0.09, r'$E[X] = 0$（真值）', ha='right', fontsize=10.5,
            color='#333333')

    # n = 5 处 x̄ = 0.2
    ax.plot(5, m1[4], 'o', color='#c0392b', ms=8, zorder=5)
    ax.annotate(r'n = 5：$\bar{x}$ = 0.2（正文例3.1）', xy=(5, m1[4]),
                xytext=(26, 0.42), fontsize=10, color='#c0392b',
                arrowprops=dict(arrowstyle='->', color='#c0392b', lw=1.2))

    # n = 100 处标注
    ax.plot(100, m1[99], 's', color='#1a5276', ms=6, zorder=5)
    ax.annotate('n = 100：均值明显向 0 靠拢', xy=(100, m1[99]),
                xytext=(102, 0.32), fontsize=10, color='#1a5276',
                arrowprops=dict(arrowstyle='->', color='#1a5276', lw=1.2))

    # 聚焦坐标：x 0-150，y 真值附近 ±0.6（初始 ±1 级波动裁出图外）
    ax.set_xlim(-3, 158)
    ax.set_ylim(-0.62, 0.62)
    ax.set_xticks([0, 50, 100, 150])
    ax.set_yticks([-0.5, -0.25, 0, 0.25, 0.5])
    ax.set_xlabel('抛掷次数 n（聚焦 0-150）', fontsize=11)
    ax.set_ylabel(r'样本均值 $\bar{x}_n$', fontsize=11)
    ax.grid(alpha=0.25)
    ax.legend(loc='upper right', fontsize=9, frameon=True)

    fig.savefig(os.path.join(OUT, 'fig3-2.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('fig3-2 done')


def fig3_5():
    """图 3-5 例3.3：三条回合、三个回报（聚焦：缩小版式、删除图内子标题与底注）"""
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

    # 共享段 s1→s2→s3（灰色细线）
    arrow('s1', 's2', '#99a3a4', 1.6, z=3)
    arrow('s2', 's3', '#99a3a4', 1.6, z=3)
    # 回合1（蓝实线）：s3→s6 落入禁区
    arrow('s3', 's6', '#2e86c1', 3.2, rad=0.18)
    # 回合2（橙虚线）：s3→s6 同路径不同次
    arrow('s3', 's6', '#e67e22', 2.6, ls=(0, (5, 3)), rad=-0.18)
    # 回合3（绿实线）：s3→s9 到达目标（跨过 s6 上方）
    arrow('s3', 's9', '#229954', 3.2, rad=0.42)
    axL.text(0.5, 2.10, '策略“总是向右”', fontsize=9.5, color='#566573')
    axL.text(0.5, 1.86, '（例3.3，γ = 1）', fontsize=9.5, color='#566573')

    handles = [
        Line2D([0], [0], color='#2e86c1', lw=3, label=r'回合1：s1→s2→s3→s6（回报 $G_1 = -1$）'),
        Line2D([0], [0], color='#e67e22', lw=2.4, ls=(0, (5, 3)),
               label=r'回合2：s1→s2→s3→s6（回报 $G_2 = -1$）'),
        Line2D([0], [0], color='#229954', lw=3, label=r'回合3：s1→s2→s3→s9（回报 $G_3 = +1$）'),
    ]
    axL.legend(handles=handles, loc='lower center', bbox_to_anchor=(0.5, -0.12),
               ncol=1, fontsize=8.8, frameon=True, handlelength=2.2)

    # ---- 右：回报汇总（聚焦：卡片间距压缩、右边界收紧） ----
    axR.set_xlim(0, 9.4)
    axR.set_ylim(0, 10)
    axR.axis('off')
    cards = [
        ('回合1：s1→s2→s3→s6', r'$G_1 = -1$', '#d6eaf8', '#2e86c1'),
        ('回合2：s1→s2→s3→s6', r'$G_2 = -1$', '#d6eaf8', '#2e86c1'),
        ('回合3：s1→s2→s3→s9', r'$G_3 = +1$', '#d5f5e3', '#229954'),
    ]
    y0 = 8.2
    for i, (name, g, fc, ec) in enumerate(cards):
        y = y0 - i * 1.75
        axR.add_patch(FancyBboxPatch((0.6, y - 0.60), 5.4, 1.05,
                                     boxstyle='round,pad=0.06', facecolor=fc,
                                     edgecolor=ec, lw=1.6, zorder=2))
        axR.text(1.0, y, name, ha='left', va='center', fontsize=10, zorder=3)
        axR.text(5.7, y, g, ha='center', va='center', fontsize=12.5,
                 fontweight='bold', color=('#1e8449' if '+' in g else '#b03a2e'),
                 zorder=3)
    # 大括号（三条回报 → 平均）
    axR.plot([6.35, 6.35], [y0 - 0.35, y0 - 3.25], color='#1b2631', lw=2.2, zorder=3)
    axR.annotate('', xy=(6.35, y0 - 3.7), xytext=(6.35, y0 - 3.35),
                 arrowprops=dict(arrowstyle='-|>', color='#1b2631', lw=2.2), zorder=3)
    axR.text(6.85, 3.35, r'$\hat{q}_\pi(s_1,\ a_2) = \frac{(-1+1-1)}{3} = -\frac{1}{3}$',
             fontsize=12.5, fontweight='bold', color='#1b2631', zorder=3)
    axR.text(6.85, 2.78, '真值 q = 0（s3 向右落 s6 与 s9 各 0.5）',
             fontsize=9.5, color='#566573', zorder=3)
    axR.text(6.85, 2.40, '差距 = 噪声（数据版给出的是噪声值）',
             fontsize=9.5, color='#b03a2e', zorder=3)
    axR.text(6.85, 1.98, '有限样本下，策略可能被噪声误导',
             fontsize=9.5, color='#b03a2e', zorder=3)

    fig.savefig(os.path.join(OUT, 'fig3-5.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('fig3-5 done')


def fig3_8():
    """图 3-8 RM 定理的两个步长条件（聚焦：0-400 步、y 收窄到 -2~6.2，噪声 ×2）"""
    fig, ax = plt.subplots(figsize=(10.2, 5.6))
    n_max = 400                       # 聚焦：缩短模拟步数（行为在 400 步内已充分展现）
    ks = np.arange(1, n_max + 1)
    rng = np.random.default_rng(2026)
    eta = rng.normal(0, 1, n_max)

    def simulate(a, eta):
        w = np.zeros(n_max)
        w[0] = 0.0                    # w_1 = 0（正文例3.5）
        for k in range(1, n_max):
            w[k] = w[k - 1] - a(k) * (w[k - 1] - 3 + eta[k - 1])
        return w

    w_1k = simulate(lambda k: 1.0 / k, eta)                 # 1/k：满足①②，平稳收敛
    eta_loud = eta * 2.0                                     # 1/√k：违反②（×2 便于聚焦收窄）
    w_1sk = simulate(lambda k: 1.0 / np.sqrt(k), eta=eta_loud)
    eta_k2 = eta.copy()
    eta_k2[0] = 0.5                                          # 首噪声 η₁=0.5（呼应例3.5 w₂=2.5）
    w_1k2 = simulate(lambda k: 1.0 / (k ** 2), eta=eta_k2)
    w_const = simulate(lambda k: 0.1, eta)                   # 常数步长：跟随但抖动

    ax.axhline(3, color='#333333', lw=1.6, ls='--', zorder=2)
    ax.text(386, 3.10, r'真值 $w^* = 3$', fontsize=11, color='#333333')

    ax.plot(ks, w_1k, color='#1f618d', lw=2.4, zorder=5, label=r'$a_k = 1/k$：平稳收敛（满足①+②）')
    ax.plot(ks, w_1sk, color='#e67e22', lw=1.6, ls=(0, (6, 3)), zorder=4,
            label=r'$a_k = 1/\sqrt{k}$：抖动渐大（违反②）')
    ax.plot(ks, w_1k2, color='#229954', lw=1.8, ls=(0, (2, 2)), zorder=4,
            label=r'$a_k = 1/k^2$：停在半路（违反①）')
    ax.plot(ks, w_const, color='#7f8c8d', lw=1.2, alpha=0.9, zorder=3,
            label=r'常数步长 $\alpha = 0.1$：跟随但持续抖动（对比）')

    # 右上部条件框
    ax.text(0.985, 0.97,
            r'RM 定理两个条件：' + '\n' +
            r'① $\Sigma_{k=1}^{\infty} a_k = \infty$　能走远' + '\n' +
            r'② $\Sigma_{k=1}^{\infty} a_k^2 < \infty$　能平噪',
            transform=ax.transAxes, ha='right', va='top', fontsize=10.5,
            color='#1a5276', linespacing=1.6,
            bbox=dict(boxstyle='round,pad=0.5', facecolor='#eaf2f8',
                      edgecolor='#1a5276', lw=1.4))

    # 聚焦坐标：x 0-400，y -2~6.2（1/k² 停半路、1/√k 发散抖动均可见）
    ax.set_xlim(-10, 420)
    ax.set_ylim(-2.0, 6.2)
    ax.set_xticks([0, 100, 200, 300, 400])
    ax.set_yticks([-2, 0, 2, 4, 6])
    ax.set_xlabel('迭代次数 k（聚焦 0-400）', fontsize=11)
    ax.set_ylabel(r'估计 $w_k$', fontsize=11)
    ax.grid(alpha=0.25)
    ax.legend(loc='lower right', fontsize=9, frameon=True)

    fig.savefig(os.path.join(OUT, 'fig3-8.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('fig3-8 done')


def fig3_9():
    """图 3-9 证据等级 × 把握程度：二维框架与四象限（聚焦：紧凑版式、删除图内标题）"""
    fig, ax = plt.subplots(figsize=(8.8, 6.2))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)

    # 四象限着色
    ax.add_patch(Rectangle((5, 5), 5, 5, facecolor='#d5f5e3', alpha=0.55, zorder=0))
    ax.add_patch(Rectangle((0, 5), 5, 5, facecolor='#fef9e7', alpha=0.6, zorder=0))
    ax.add_patch(Rectangle((5, 0), 5, 5, facecolor='#fdebd0', alpha=0.6, zorder=0))
    ax.add_patch(Rectangle((0, 0), 5, 5, facecolor='#f2f3f4', alpha=0.6, zorder=0))
    ax.axvline(5, color='#566573', lw=1.4, zorder=1)
    ax.axhline(5, color='#566573', lw=1.4, zorder=1)

    # 象限含义
    ax.text(7.5, 8.6, '高等级高把握\n= 强推荐依据', ha='center', fontsize=11,
            fontweight='bold', color='#1e8449', zorder=3)
    ax.text(2.5, 8.6, '高等级低把握\n= 可信但不够精确', ha='center', fontsize=11,
            color='#7d6608', zorder=3)
    ax.text(7.5, 3.6, '低等级高把握\n= 精确但源头可疑', ha='center', fontsize=11,
            color='#b9770e', zorder=3)
    ax.text(2.5, 3.6, '低等级低把握\n= 弱参考', ha='center', fontsize=11,
            color='#566573', zorder=3)

    # 数据点
    pts = [
        (7.7, 8.0, r'归脾汤·失眠·心脾两虚', '#1e8449', 10.5,
         r'A 级、n = 30、$\bar{x}$ ≈ 0.873' + '\n' + r'95% 区间 [0.79, 0.96]（半宽 ≈ 0.086）'),
        (2.3, 8.0, 'A 级仅 5 例', '#7d6608', 9.5, '可信但不够精确'),
        (7.7, 1.8, 'C 级 5000 例', '#b9770e', 9.5, '精确但源头可疑'),
    ]
    for x, y, name, c, fs, sub in pts:
        ax.plot(x, y, 'o', color=c, ms=12, zorder=5)
        ax.text(x, y - 1.05, name, ha='center', fontsize=fs, fontweight='bold',
                color=c, zorder=5)
        ax.text(x, y - 1.75, sub, ha='center', fontsize=8.8, color='#444444',
                zorder=5)

    # 权重小表（图右下角）
    tbl_data = [['A', '1.0'], ['B', '0.7'], ['C', '0.4']]
    tbl = ax.table(cellText=tbl_data, colLabels=['等级', '权重'], loc='lower right',
                   cellLoc='center', bbox=[0.745, 0.06, 0.22, 0.20])
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(8.5)
    for j in range(2):
        c = tbl[0, j]
        c.set_facecolor('#1f4e79')
        c.set_text_props(color='white', fontweight='bold')

    ax.set_xlabel('把握程度（标准误 / 区间宽度，向右越大）', fontsize=11)
    ax.set_ylabel('证据等级（A/B/C，向上越高）', fontsize=11)
    ax.set_xticks([0, 5, 10])
    ax.set_xticklabels(['低把握', '中', '高把握'], fontsize=10)
    ax.set_yticks([0, 5, 10])
    ax.set_yticklabels(['C 级', 'B 级', 'A 级'], fontsize=10)

    fig.savefig(os.path.join(OUT, 'fig3-9.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('fig3-9 done')


if __name__ == '__main__':
    fig3_2()
    fig3_5()
    fig3_8()
    fig3_9()
    print('ALL DONE ->', OUT)
