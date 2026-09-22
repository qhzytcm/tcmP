# -*- coding: utf-8 -*-
"""《中医场景强化学习》第9章 费曼图标准重构脚本（图表工程师）

重构依据【费曼图标准】：节点(圆圈/小方块)+连线(曲线/直线/箭头/虚线)，黑白灰线稿为主，
1-2 种低饱和色点缀(灰蓝#4a6785/灰绿#5d7a5e)，禁止大面积填充色块，极简去装饰，
方向明确(箭头)，信息密度高(数值/符号直接标注在节点与线上)，聚焦图段延续
(ch09 沿用 v2 聚焦：9-1 τ∈[0.2,2.0]、9-2 轨迹全段+J 上升段、9-3 x∈[0,80]、9-4 x∈[0,3.2])。
输出：figures/ch09/fig9-1.png ~ fig9-4.png（覆盖）
数值口径：9.1.2 softmax(2.0,1.0) τ=1 -> 0.731/0.269；9.5.2 τ=0.5 -> 0.88/0.12；
  9.2.2 θ=(1.0,0.5)、∇θ≈(0.495,-0.495)、J 0.904->1.440、θ1 1.0->1.568（α=0.1、12 步）；
  9.6.2 μ=1.5、σ=0.5（σ=1.0 对照示意）；9.5.2 探索率曲线（教学示意，起始 0.9）
"""
import os
import math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch

plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ch09')
os.makedirs(OUT, exist_ok=True)

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


def softmax_pair(x, y, tau=1.0):
    ex = math.exp(x / tau)
    ey = math.exp(y / tau)
    return ex / (ex + ey), ey / (ex + ey)


# ============================================================
# 图 9-1 softmax 策略示意：温度 τ 对动作概率分布的影响（正文 9.1.2、9.5.2）
# 曲线：π(a1) 灰蓝实线 / π(a2) 灰绿实线；关键点 τ=0.5/τ=1（空心圆+数值）
# 右栏：τ=1 与 τ=0.5 概率条形（白底黑框 + 低饱和浅填充）
# ============================================================
def fig9_1():
    p1_t1, p2_t1 = softmax_pair(2.0, 1.0, 1.0)
    p1_t05, p2_t05 = softmax_pair(2.0, 1.0, 0.5)
    assert abs(p1_t1 - 0.731) < 0.002 and abs(p2_t1 - 0.269) < 0.002
    assert abs(p1_t05 - 0.88) < 0.01 and abs(p2_t05 - 0.12) < 0.01

    fig, (axL, axR) = plt.subplots(
        1, 2, figsize=(10.0, 4.8), gridspec_kw={'width_ratios': [1.25, 1.0]})

    # ---- 左：温度曲线（聚焦 τ∈[0.2,2.0]）----
    taus = np.linspace(0.2, 2.0, 300)
    p1 = np.exp(2.0 / taus) / (np.exp(2.0 / taus) + np.exp(1.0 / taus))
    p2 = 1.0 - p1
    axL.plot(taus, p1, color=BLUE, lw=2.2, label='首选方概率（偏好 2.0）')
    axL.plot(taus, p2, color=GOLD, lw=2.2, label='备选方概率（偏好 1.0）')
    axL.axvline(0.5, color=RED, ls='--', lw=1.2)
    axL.axvline(1.0, color=RED, ls='--', lw=1.2)
    axL.plot([0.5], [p1_t05], 'o', ms=7, mfc='white', mec=RED, mew=1.4, zorder=5)
    axL.plot([1.0], [p1_t1], 'o', ms=7, mfc='white', mec=RED, mew=1.4, zorder=5)
    # 关键数值锚点（正文 9.5.2 / 9.1.2）
    axL.annotate(r'$\tau=0.5 \to 0.88/0.12$', xy=(0.5, p1_t05),
                 xytext=(0.55, 0.97), fontsize=11, color=RED, fontweight='bold',
                 arrowprops=dict(arrowstyle='->', color=RED, lw=1.0))
    axL.annotate(r'$\tau=1 \to 0.731/0.269$', xy=(1.0, p1_t1),
                 xytext=(1.30, 0.82), fontsize=11, color=RED, fontweight='bold',
                 arrowprops=dict(arrowstyle='->', color=RED, lw=1.0))
    axL.set_xlim(0.2, 2.0)
    axL.set_ylim(0, 1.05)
    axL.set_xticks([0.2, 0.5, 1.0, 1.5, 2.0])
    axL.set_xlabel(r'决策锐度 $\tau$', fontsize=11)
    axL.set_ylabel('选方概率', fontsize=11)
    axL.legend(loc='lower left', fontsize=10)

    # ---- 右：τ=1 与 τ=0.5 概率条形（仅正文两组数值；图注未提颜色，保持黑白灰）----
    bars = [(0.35, p1_t1, LGRAY), (1.05, p2_t1, PALE),
            (1.85, p1_t05, LGRAY), (2.55, p2_t05, PALE)]
    for x, h, c in bars:
        axR.bar(x, h, width=0.5, color=c, alpha=0.45, edgecolor=BLACK,
                linewidth=1.1, zorder=3)
    axR.text(0.7, 0.99, '0.731/0.269', ha='center', fontsize=11,
             fontweight='bold')
    axR.text(2.2, 0.99, '0.88/0.12', ha='center', fontsize=11,
             fontweight='bold')
    axR.text(0.7, 0.50, r'$\tau=1$', ha='center', fontsize=10.5)
    axR.text(2.2, 0.50, r'$\tau=0.5$', ha='center', fontsize=10.5)
    axR.set_ylim(0, 1.05)
    axR.set_xticks([])
    axR.set_yticks([])

    fig.tight_layout()
    fig.savefig(os.path.join(OUT, 'fig9-1.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('fig9-1 done')


def pg_model(theta1, theta2):
    """9.2.2 两状态两动作模型（与正文 v2 口径一致）"""
    pi1 = math.exp(theta1) / (math.exp(theta1) + math.exp(theta2))
    pi2 = 1.0 - pi1
    d1 = 1.0 / (1.0 + pi2)
    rbar = d1 * pi1 * 2.0
    grad1 = d1 * pi1 * pi2 * (2.0 + rbar)
    return pi1, pi2, d1, rbar, grad1


# ============================================================
# 图 9-2 策略梯度上升轨迹：参数空间迭代与目标函数上升（正文 9.2.2）
# 左：参数空间（灰等高线 + 灰蓝虚线轨迹 + 起点/终点/梯度箭头标注）
# 右：目标函数 J 上升（灰蓝曲线+点，初始 0.90 → 12 步 1.44）
# ============================================================
def fig9_2():
    pi1_0, pi2_0, d1_0, rbar_0, grad1_0 = pg_model(1.0, 0.5)
    assert abs(pi1_0 - 0.62) < 0.01 and abs(pi2_0 - 0.38) < 0.01
    assert abs(d1_0 - 0.726) < 0.005
    assert abs(grad1_0 - 0.495) < 0.005

    alpha = 0.1
    steps = 12
    th1 = 1.0
    th2 = 0.5
    traj = [(th1, th2)]
    Js = [rbar_0]
    for _ in range(steps):
        _, _, _, _, g1 = pg_model(th1, th2)
        th1 = th1 + alpha * g1
        th2 = 1.5 - th1
        traj.append((th1, th2))
        Js.append(pg_model(th1, th2)[3])
    for a, b in zip(Js, Js[1:]):
        assert b >= a - 1e-9

    fig, (axL, axR) = plt.subplots(1, 2, figsize=(11.2, 4.9))

    # ---- 左：参数空间等高线 + 迭代轨迹 ----
    g1 = np.linspace(0.95, 1.65, 240)
    g2 = np.linspace(-0.15, 0.55, 240)
    G1, G2 = np.meshgrid(g1, g2)
    Jg = np.empty_like(G1)
    for i in range(g1.size):
        for j in range(g2.size):
            Jg[j, i] = pg_model(g1[i], g2[j])[3]
    # 等高线（只画线，不标等高值，去装饰）
    cf = axL.contour(G1, G2, Jg, levels=np.linspace(0.92, 1.44, 7),
                     colors=LGRAY, linewidths=0.9, zorder=1)

    tx = [t[0] for t in traj]
    ty = [t[1] for t in traj]
    axL.plot(tx, ty, color=BLUE, lw=1.6, ls='--', zorder=4)
    axL.plot(tx, ty, 'o', ms=4, color=BLUE, zorder=5)
    axL.plot(tx[0], ty[0], 'o', ms=9, mfc=RED, mec=RED, mew=1.5, zorder=6)
    axL.annotate('起点 (1.0, 0.5)', xy=(1.0, 0.5),
                 xytext=(0.955, 0.56), fontsize=11, color=RED, fontweight='bold',
                 arrowprops=dict(arrowstyle='->', color=RED, lw=1.0))
    axL.add_patch(FancyArrowPatch((1.0, 0.5), (1.0 + 0.30 * 0.495,
                                               0.5 - 0.30 * 0.495),
                                  arrowstyle='-|>', mutation_scale=15,
                                  color=GREEN, lw=2.0, zorder=6))
    # 关键数值锚点 0.495（正文 9.2.2，图注）
    axL.text(1.02, 0.42, '调优方向 ≈ (0.495, −0.495)', fontsize=11,
             color=GREEN, fontweight='bold')
    axL.plot(tx[-1], ty[-1], 's', ms=7, mfc=BLUE, mec=BLUE, zorder=6)
    axL.annotate('12 步后 (1.57, −0.07)', xy=(tx[-1], ty[-1]),
                 xytext=(1.22, -0.13), fontsize=10, color=BLUE,
                 arrowprops=dict(arrowstyle='->', color=BLUE, lw=1.0))
    axL.set_xlim(0.95, 1.65)
    axL.set_ylim(-0.15, 0.55)
    axL.set_xticks([1.0, 1.2, 1.4, 1.6])
    axL.set_yticks([0.0, 0.2, 0.4])
    axL.set_xlabel('首选方偏好', fontsize=11)
    axL.set_ylabel('备选方偏好', fontsize=11)

    # ---- 右：目标函数 J 随迭代上升（橙色折线，图注）----
    axR.plot(range(steps + 1), Js, color=ORANGE, lw=2.0, marker='o', ms=4,
             zorder=3)
    axR.annotate('初始 J ≈ 0.90', xy=(0, Js[0]),
                 xytext=(1.0, 0.92), fontsize=11, color=GRAY, fontweight='bold',
                 arrowprops=dict(arrowstyle='->', color=GRAY, lw=1.0))
    axR.annotate('12 步 J ≈ 1.44', xy=(steps, Js[-1]),
                 xytext=(6.0, 1.36), fontsize=11, color=ORANGE, fontweight='bold',
                 arrowprops=dict(arrowstyle='->', color=ORANGE, lw=1.0))
    axR.set_xlim(-0.4, steps + 0.6)
    axR.set_ylim(0.88, 1.50)
    axR.set_xticks([0, 3, 6, 9, 12])
    axR.set_yticks([0.9, 1.0, 1.1, 1.2, 1.3, 1.4])
    axR.set_xlabel(r'调整步数 $k$', fontsize=11)
    axR.set_ylabel(r'平均疗效 $J$', fontsize=11)

    fig.tight_layout()
    fig.savefig(os.path.join(OUT, 'fig9-2.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('fig9-2 done')


# ============================================================
# 图 9-3 探索与利用权衡：探索率 ε 随成长阶段衰减（正文 9.5.1、9.5.2）
# 曲线：ε 衰减（灰蓝实线）；关键点：(0,0.9)/(33,0.36)/(66,0.14)（空心圆+数值）
# 阶段：竖虚线 33/66 + 文字标签；探索→利用过渡箭头
# ============================================================
def fig9_3():
    fig, ax = plt.subplots(figsize=(9.4, 4.8))
    x = np.linspace(0, 80, 400)
    eps = 0.9 * np.exp(-0.028 * x)

    # 三条背景色带为阶段分界（图注：橙=住院医 0-33、黄=主治 33-66、绿=副高以上 66-80）
    ax.axvspan(0, 33, color=BG_ORANGE, zorder=0)
    ax.axvspan(33, 66, color=BG_YELLOW, zorder=0)
    ax.axvspan(66, 80, color=BG_GREEN, zorder=0)
    ax.axvline(33, color=ORANGE, ls='--', lw=1.2, zorder=2)
    ax.axvline(66, color=YELLOW, ls='--', lw=1.2, zorder=2)

    ax.plot(x, eps, color=RED, lw=2.2, zorder=3)

    # 关键点（关键数值直接标注；阶段名由横轴刻度承担，阶段说明移入图注）
    for xp, yp in [(0, 0.9), (33, 0.9 * math.exp(-0.028 * 33)),
                   (66, 0.9 * math.exp(-0.028 * 66))]:
        ax.plot(xp, yp, 'o', ms=6, mfc='white', mec=DARK, mew=1.3, zorder=5)
    ax.text(1.5, 0.86, 'ε=0.9', fontsize=11, color=DARK, fontweight='bold')
    ax.text(34.5, 0.40, 'ε≈0.36', fontsize=11, color=DARK, fontweight='bold')
    ax.text(67.5, 0.17, 'ε≈0.14', fontsize=11, color=DARK, fontweight='bold')

    # 探索 → 利用 过渡箭头
    ax.annotate('', xy=(77, 0.05), xytext=(77, 0.74),
                arrowprops=dict(arrowstyle='-|>', color=DARK, lw=1.6), zorder=3)
    ax.text(78.4, 0.40, '试新→守成', rotation=90, va='center',
            fontsize=10, color=DARK)

    ax.set_xlim(0, 80)
    ax.set_ylim(0, 0.98)
    ax.set_xticks([0, 33, 66, 80])
    ax.set_xticklabels(['起步', '住院医', '主治', '副高以上'], fontsize=9)
    ax.set_xlabel('成长阶段', fontsize=11)
    ax.set_ylabel(r'试探比例 $\varepsilon$', fontsize=11)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, 'fig9-3.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('fig9-3 done')


# ============================================================
# 图 9-4 正态分布策略示意：连续动作，均值 μ 附近高斯采样（正文 9.6.1、9.6.2）
# 曲线：σ=0.5（灰蓝实线）vs σ=1.0（灰绿虚线）；均值 μ=1.5 竖虚线 + 峰值标注
# ============================================================
def fig9_4():
    mu = 1.5
    sig_s = 0.5
    sig_l = 1.0
    a = np.linspace(0.0, 3.2, 500)
    p_s = (1.0 / (sig_s * math.sqrt(2 * math.pi))) * \
          np.exp(-0.5 * ((a - mu) / sig_s) ** 2)
    p_l = (1.0 / (sig_l * math.sqrt(2 * math.pi))) * \
          np.exp(-0.5 * ((a - mu) / sig_l) ** 2)

    fig, ax = plt.subplots(figsize=(9.0, 4.8))
    ax.plot(a, p_s, color=BLUE, lw=2.2,
            label=r'$\sigma=0.5$（把握紧）')
    ax.plot(a, p_l, color=GOLD, lw=2.2, ls='--',
            label=r'$\sigma=1.0$（把握松）')
    ax.axvline(mu, color=RED, ls='--', lw=1.3)
    ax.plot([mu], [0], 'o', ms=7, mfc='white', mec=RED, mew=1.4, zorder=5)
    ax.annotate(r'最适剂量 $\mu=1.5$', xy=(mu, 0),
                xytext=(1.55, 0.66), fontsize=11, color=RED, fontweight='bold',
                arrowprops=dict(arrowstyle='->', color=RED, lw=1.0))
    # 峰值关键点（关键数值直接标注）
    ax.plot(mu, 1.0 / (sig_s * math.sqrt(2 * math.pi)), 'o', ms=7,
            mfc='white', mec=BLUE, mew=1.4, zorder=5)
    ax.plot(mu, 1.0 / (sig_l * math.sqrt(2 * math.pi)), 'o', ms=7,
            mfc='white', mec=GOLD, mew=1.4, zorder=5)
    ax.text(1.56, 0.80, '0.80', fontsize=11, color=BLUE, fontweight='bold')
    ax.text(1.56, 0.44, '0.40', fontsize=11, color=GOLD, fontweight='bold')

    ax.set_xlim(0, 3.2)
    ax.set_ylim(0, 0.85)
    ax.set_xticks([0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0])
    ax.set_xlabel(r'剂量 $a$', fontsize=11)
    ax.set_ylabel('剂量把握密度', fontsize=11)
    ax.legend(loc='upper left', fontsize=10)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, 'fig9-4.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('fig9-4 done')


if __name__ == '__main__':
    fig9_1()
    fig9_2()
    fig9_3()
    fig9_4()
    print('ALL DONE ->', OUT)
