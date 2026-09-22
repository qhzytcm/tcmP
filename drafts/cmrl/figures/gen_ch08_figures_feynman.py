# -*- coding: utf-8 -*-
"""《中医场景强化学习》第8章 费曼图标准重构脚本（图表工程师）

重构依据【费曼图标准】：节点(圆圈/小方块)+连线(直线/箭头/虚线)，黑白灰线稿为主，
1-2 种低饱和色点缀(灰蓝#4a6785/灰绿#5d7a5e)，禁止大面积填充色块，极简去装饰，
方向明确(箭头)，信息密度高(数值/符号直接标注)，聚焦图段延续(ch08 沿用 v2 聚焦：
8-1 s∈[1,3] 样本密集段、8-2 前 50 步损失下降段、8-3 两锚点之间)。
输出：figures/ch08/fig8-1.png ~ fig8-4.png（覆盖）
数值口径：例8.1/8.1.2（φ(s)=[s,1]^T、w=[a,b]^T、v̂=0.3s+0.1）；例8.2/8.2.2
  （v̂(s1)=0.4、v̂(s2)=0.7、v̂(s3)=1.0、t=2 误差1 -> w=[0.3,0.1]、t=3 TD目标0.9 误差0.2）；
  8.4.1（10000≈1MB、10^10≈1TB、函数法 m=50≈0.4KB）；8.5.1（r_total=w1·r_生理+…）
"""
import os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from matplotlib.ticker import FuncFormatter

plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ch08')
os.makedirs(OUT, exist_ok=True)

# ---- 费曼调色板：黑白灰 + 图注对齐的低饱和彩色 ----
BLACK = '#1a1a1a'
DARK = '#333333'
GRAY = '#666666'
LGRAY = '#999999'
PALE = '#c9c9c9'
BLUE = '#4a6785'    # 蓝（低饱和灰蓝）
GREEN = '#5d7a5e'   # 绿（低饱和灰绿）
RED = '#a0514e'     # 红（低饱和砖红）
ORANGE = '#a86f3f'  # 橙（低饱和土橙）
GOLD = '#a8833a'    # 金（低饱和金黄）
YELLOW = '#b3a24f'  # 黄（低饱和土黄）
PURPLE = '#7a6787'  # 紫（低饱和灰紫）
CYAN = '#5d8a88'    # 青（低饱和青灰）
# 浅底色（区域/背景带/浅底框，均为低饱和淡色）
BG_GRAY = '#e8e8e8'
BG_BLUE = '#e4e8ee'
BG_GREEN = '#e5eae3'
BG_ORANGE = '#f0e6d8'
BG_YELLOW = '#f0ecd9'
BG_RED = '#f0e5e4'
BG_GOLD = '#f0e8d6'


def nbox(ax, cx, cy, w, h, txt, ec=BLACK, fc='white', fs=10.5, lw=1.3,
         tc=BLACK, ls=1.4, bold=False, z=3):
    """节点：圆角小方块（白底、黑/灰描边，细框线）"""
    ax.add_patch(FancyBboxPatch((cx - w / 2, cy - h / 2), w, h,
                                boxstyle='round,pad=0.04',
                                facecolor=fc, edgecolor=ec, lw=lw, zorder=z))
    ax.text(cx, cy, txt, ha='center', va='center', fontsize=fs, color=tc,
            zorder=z + 1, fontweight='bold' if bold else 'normal', linespacing=ls)


def ar(ax, x1, y1, x2, y2, color=BLACK, lw=1.4, style='-|>', rad=0.0, z=2):
    """连线：箭头（细线）"""
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle=style, color=color, lw=lw,
                                connectionstyle='arc3,rad=%s' % rad), zorder=z)


# ============================================================
# 图 8-1 函数近似拟合曲线（正文 8.1.2，例8.1 直线拟合 + 例8.2 锚点）
# 节点：真实价值数据点(空心圆)、例8.2 锚点(实心圆+数值)、特征/参数框(细线方)
# 连线：拟合直线(灰蓝实线)、残差段(浅灰虚线)
# 文字分层：φ(s)/w 公式框与拟合偏差说明移入图注；去网格
# ============================================================
def fig8_1():
    fig, ax = plt.subplots(figsize=(8.8, 5.2))
    s_all = np.array([1.0, 2.0, 3.0])
    v_true = np.array([0.35, 0.75, 0.95])
    s_fit = np.linspace(0.7, 3.5, 100)
    v_fit = 0.3 * s_fit + 0.1

    for s, v in zip(s_all, v_true):
        ax.plot([s, s], [v, 0.3 * s + 0.1], color=ORANGE, lw=1.0, ls='--',
                zorder=1)
    ax.scatter(s_all, v_true, s=55, facecolors=LGRAY, edgecolors=GRAY,
               linewidths=1.2, zorder=3,
               label='长期疗效把握（灰色散点）')
    ax.plot(s_fit, v_fit, color=BLUE, lw=2.2, zorder=4,
            label=r'拟合线 $\hat{v}(s)=0.3s+0.1$')

    # 例8.2 锚点（红点，关键数值直接标注）
    for s, v in [(1, 0.4), (2, 0.7), (3, 1.0)]:
        ax.plot(s, v, 'o', ms=7, mfc=RED, mec=RED, zorder=5)
        ax.annotate(r'$\hat{v}(s_%d)=%s$' % (s, '%.1f' % v), xy=(s, v),
                    xytext=(s + 0.08, v + 0.06), fontsize=11, color=RED,
                    fontweight='bold', zorder=5)

    ax.set_xlabel('证候 s', fontsize=11)
    ax.set_ylabel(r'疗效把握 $\hat{v}(s,w)$', fontsize=11)
    ax.set_xlim(0.68, 3.55)
    ax.set_ylim(0.08, 1.32)
    ax.set_xticks([1, 2, 3])
    ax.set_yticks([0.2, 0.4, 0.6, 0.8, 1.0])
    ax.legend(loc='lower right', fontsize=10, frameon=True)
    fig.savefig(os.path.join(OUT, 'fig8-1.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('fig8-1 done')


# ============================================================
# 图 8-2 随机梯度下降损失曲线（正文 8.2.1/8.2.2，例8.2 数值演练背景）
# 曲线：梯度下降 GD（灰蓝实线）vs 随机梯度下降 SGD（灰绿虚线）
# 锚点：t=2/t=3 数值标注、谷底波动注释
# ============================================================
def fig8_2():
    gamma, alpha = 0.9, 0.1
    vpi = {1: 0.81, 2: 0.90, 3: 1.00}

    def vhat(i, w):
        return i * w[0] + 1 * w[1]

    def loss(w):
        return float(np.mean([(vpi[i] - vhat(i, w)) ** 2 for i in [1, 2, 3]]))

    seq = [2, 3, 2]
    rng = np.random.default_rng(42)
    for _ in range(197):
        seq.append(int(rng.integers(1, 4)))

    w = np.array([0.0, 0.0])
    losses_sgd = [loss(w)]
    for t, s in enumerate(seq):
        target = 1.0 if s == 3 else gamma * vhat(s + 1, w)
        delta = target - vhat(s, w)
        w = w + alpha * delta * np.array([s, 1.0])
        losses_sgd.append(loss(w))
    losses_sgd = losses_sgd[:151]

    def grad_full(w):
        return np.mean([-2 * (vpi[i] - vhat(i, w)) * np.array([i, 1.0])
                        for i in [1, 2, 3]], axis=0)

    wg = np.array([0.0, 0.0])
    losses_gd = [loss(wg)]
    for _ in range(150):
        wg = wg - alpha * grad_full(wg)
        losses_gd.append(loss(wg))

    fig, ax = plt.subplots(figsize=(10.0, 5.4))
    ts = np.arange(len(losses_sgd))
    ax.plot(ts, losses_gd, color=BLUE, lw=2.2, zorder=3,
            label='逐批调优（全量平均偏差）')
    ax.plot(ts, losses_sgd, color=RED, lw=1.6, ls='--', zorder=3,
            label='边走边调（单条随访记录）')

    # 关键数值锚点（t=2/t=3 修正；w=[0.3,0.1]、目标 0.9 见图注③）
    ax.annotate('t=2 访问 s3：偏差 1',
                xy=(2, losses_sgd[2]), xytext=(10, 0.36),
                fontsize=11, color=RED, fontweight='bold',
                arrowprops=dict(arrowstyle='->', color=RED, lw=1.0), zorder=5)
    ax.annotate('t=3 再访 s2：偏差 0.2',
                xy=(3, losses_sgd[3]), xytext=(24, 0.24),
                fontsize=11, color=GRAY, fontweight='bold',
                arrowprops=dict(arrowstyle='->', color=GRAY, lw=1.0), zorder=5)

    ax.set_xlabel('随访次数 t', fontsize=11)
    ax.set_ylabel(r'平均偏差 $J(w)$', fontsize=11)
    ax.set_xlim(-2, 54)
    ax.set_ylim(0, 0.45)
    ax.set_xticks([0, 10, 20, 30, 40, 50])
    ax.set_yticks([0, 0.1, 0.2, 0.3, 0.4])
    ax.legend(loc='upper right', fontsize=10, frameon=True)
    fig.savefig(os.path.join(OUT, 'fig8-2.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('fig8-2 done')


# ============================================================
# 图 8-3 表格 vs 函数权衡：存储与泛化对比（正文 8.4.1/8.4.2，例8.4 背景）
# (a) loglog 两条线（表格=灰蓝、函数=灰绿）+ 两锚点空心圆数值标注
# (b) 2×2 节点对比（白底黑框）——混合方案与判据三问移入图注④
# ============================================================
def fig8_3():
    fig, (axL, axR) = plt.subplots(1, 2, figsize=(11.2, 5.6),
                                   gridspec_kw={'width_ratios': [1.05, 1.0]})

    # ---- (a) 存储量级 vs 状态数（对数-对数，聚焦两锚点之间）----
    n = np.logspace(3, 10, 200)
    storage_table = n * 100.0 / 1e6
    storage_func = 50 * 8.0 / 1e6 * np.ones_like(n)
    axL.loglog(n, storage_table, color=BLUE, lw=2.2, zorder=3,
               label='逐条记忆：随证候数线性增长')
    axL.loglog(n, storage_func, color=ORANGE, lw=2.2, zorder=3,
               label='提炼规律：m=50 恒定')
    axL.plot(1e4, 1.0, 'o', ms=8, mfc='white', mec=RED, mew=1.4, zorder=5)
    axL.plot(1e10, 1e6, 'o', ms=8, mfc='white', mec=RED, mew=1.4, zorder=5)
    # 关键数值锚点（细节见图注③）
    axL.annotate('10000≈1MB（可行）', xy=(1e4, 1.0),
                 xytext=(1.6e4, 2.6), fontsize=11, color=RED, fontweight='bold',
                 arrowprops=dict(arrowstyle='->', color=RED, lw=1.0))
    axL.annotate('10^10≈1TB（不可行）', xy=(1e10, 1e6),
                 xytext=(3e8, 1e5), fontsize=11, color=RED, fontweight='bold',
                 arrowprops=dict(arrowstyle='->', color=RED, lw=1.0))
    axL.set_xlabel('证候数 n', fontsize=11)
    axL.set_ylabel('存储量级（MB）', fontsize=11)
    axL.set_xlim(3e3, 3e10)
    axL.set_ylim(1e-4, 1e7)
    axL.set_xticks([1e4, 1e6, 1e8, 1e10])
    axL.set_yticks([1e-2, 1e0, 1e2, 1e4, 1e6])
    axL.xaxis.set_major_formatter(FuncFormatter(
        lambda v, p: '1e' + str(int(round(np.log10(v))))))
    axL.yaxis.set_major_formatter(FuncFormatter(
        lambda v, p: '1e' + str(int(round(np.log10(v))))))
    axL.legend(loc='upper left', fontsize=10, frameon=True)
    axL.text(0.015, 0.965, '(a) 存储量级 vs 证候数', transform=axL.transAxes,
             fontsize=11, fontweight='bold', color=BLACK, va='top')

    # ---- (b) 泛化：老状态 vs 新状态（2×2 节点对比）----
    axR.set_xlim(0, 10)
    axR.set_ylim(0, 10)
    axR.axis('off')
    axR.text(0.015, 0.965, '(b) 触类旁通：老证候 vs 新证候', transform=axR.transAxes,
             fontsize=11, fontweight='bold', color=BLACK, va='top')
    nbox(axR, 2.6, 7.5, 4.6, 1.9, '逐条记忆\n老证候：不偏不倚 √', fs=10, lw=1.2)
    nbox(axR, 7.4, 7.5, 4.6, 1.9, '提炼规律\n老证候：略逊 △', fs=10, lw=1.2)
    nbox(axR, 2.6, 4.1, 4.6, 1.9, '逐条记忆\n新证候：无信息 ×', fs=10, lw=1.2)
    nbox(axR, 7.4, 4.1, 4.6, 1.9, '提炼规律\n新证候：可触类旁通 √', fs=10, lw=1.2)

    fig.subplots_adjust(wspace=0.22)
    fig.savefig(os.path.join(OUT, 'fig8-3.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('fig8-3 done')


# ============================================================
# 图 8-4 个性化健康推荐示意（正文 8.5.1/8.5.2，例8.5 失眠伴焦虑患者）
# 节点链：患者画像 s → 价值近似器 q̂(s,a,w) → Top-K 四类动作 → 组合方案
# 文字分层：多目标奖励公式与例8.5 注句移入图注③（公式在图注中完整保留）
# ============================================================
def fig8_4():
    fig, ax = plt.subplots(figsize=(11.6, 6.2))
    ax.set_xlim(0, 11.6)
    ax.set_ylim(0, 6.5)
    ax.axis('off')

    # 左：患者画像 s（例8.5：失眠伴焦虑患者；详情见图注③）
    nbox(ax, 1.7, 3.2, 2.7, 3.0, '患者画像\n\n全要素信息', fs=10.5, bold=True, lw=1.3)

    # 中：疗效预判（价值近似器）
    nbox(ax, 4.7, 3.2, 2.7, 2.6, '疗效预判\n\n为候选方案打分', fs=10.5, bold=True, lw=1.3)

    # 箭头：画像 → 近似器 → Top-K
    ar(ax, 3.10, 3.2, 3.32, 3.2, lw=1.6)
    ar(ax, 6.10, 3.2, 6.42, 3.2, lw=1.6)

    # 右：Top-K 四类动作（四维全要素）
    ax.text(8.15, 5.90, '优选候选（四维全要素）', ha='center', fontsize=11,
            fontweight='bold', color=BLACK)
    rows = [
        ('安神方剂\n（生理）', 4.85, DARK),
        ('情志疏导方案\n（心理）', 3.85, GRAY),
        ('家庭支持计划\n（社会）', 2.85, LGRAY),
        ('作息节律调整\n（环境）', 1.85, PALE),
    ]
    for txt, yy, dotc in rows:
        nbox(ax, 8.15, yy, 2.5, 0.85, txt, fs=10, bold=True, lw=1.2)
        ax.add_patch(plt.Circle((7.05, yy), 0.09, facecolor=dotc,
                                edgecolor=dotc, zorder=5))
    # 四框 → 组合方案
    ar(ax, 8.15, 1.42, 8.15, 1.10, lw=1.6)
    nbox(ax, 8.15, 0.6, 6.0, 0.75,
         '组合方案输出：方剂 + 调护 + 随访计划', fs=10.5, bold=True, ec=DARK, lw=1.4)

    fig.savefig(os.path.join(OUT, 'fig8-4.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('fig8-4 done')


if __name__ == '__main__':
    fig8_1()
    fig8_2()
    fig8_3()
    fig8_4()
    print('ALL DONE ->', OUT)
