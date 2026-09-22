# -*- coding: utf-8 -*-
"""《中医场景强化学习》第9章 核心图生成脚本（v2 聚焦重绘，图表工程师）

聚焦原则（用户要求：图体只保留'能代表含义的图段'）：
  - 图体只保留能代表含义的图段——调节数轴起止刻度与步长聚焦：
      fig9-1 softmax 温度曲线: τ ∈ [0.2, 2.0]（旧 [0.15, 3.0]），聚焦正文两个
              标注点 τ=0.5/τ=1 所在的探索→利用过渡段；
      fig9-2 策略梯度上升: 左图参数空间聚焦 θ1∈[0.95,1.65]/θ2∈[-0.15,0.55]
              （轨迹起点 1.0,0.5 → 12 步终点 1.568,-0.068），右图 J 聚焦
              [0.88,1.50]（12 步从 0.904 升到 1.440 的上升段）；
      fig9-3 ε 衰减曲线: x 聚焦 [0, 80]（旧 [0, 100]），聚焦探索→利用过渡段
              （住院医 0-33 / 主治 33-66 / 副高 66-80，裁掉右端低平尾段）；
      fig9-4 正态分布策略: 横轴聚焦 μ=1.5 附近 [0, 3.2]（旧 [-1.6, 4.6]），
              保留两曲线主体与均值标注；
  - 图内不再重复大标题（图题由 Excel 图题行承担：图体上方一行居中黑体）；
  - 图内底部说明行移除，信息并入图注四要素（Excel 图注行左顶格）；
  - 图注四要素（正文 md 与 Excel 图注行逐字一致）：
      a.对接正文提示语 / b.线的注释 / c.符号的注释 / d.代表含义的指针图段。

数值口径与正文 9.1-9.6 节严格一致（与 gen_ch09_figures.py 相同）：
  - 9.1.2  softmax(2.0,1.0) tau=1 -> 0.731 / 0.269
  - 9.5.2  温度减半 tau=0.5 -> 0.88 / 0.12
  - 9.2.2  两状态模型：theta=(1.0,0.5)、pi(a1)≈0.62、d_pi(s1)≈0.726、
            d_pi(s2)≈0.274、nabla_theta1≈0.495、nabla_theta2≈-0.495；
            梯度上升 α=0.1、12 步：J 0.904 -> 1.440、theta1 1.0 -> 1.568
  - 9.6.2  高斯演算：mu=1.5、sigma=0.5（sigma=1.0 为大方差对照示意）
  - 9.5.2  探索率衰减：初期高、中期缓降、后期低位（曲线为教学示意）
字形安全：theta/tau/pi/mu/sigma/varepsilon/nabla 一律用 mathtext，
          避免 SimHei 缺失的 U+2081 下标、U+00B2/U+00B3 上标与 U+2212 减号。
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


# ---------------------------------------------------------------- 共用函数
def softmax_pair(x, y, tau=1.0):
    ex = math.exp(x / tau)
    ey = math.exp(y / tau)
    return ex / (ex + ey), ey / (ex + ey)


def fig9_1():
    """图 9-1 softmax 策略示意：温度 tau 对动作概率分布的影响（正文 9.1.2、9.5.2）

    聚焦：τ ∈ [0.2, 2.0]（步长刻度 0.2/0.5/1.0/1.5/2.0），
          保留 τ=0.5 与 τ=1 两个正文标注点所在的过渡段；概率条只画
          τ=1 与 τ=0.5 两组（0.731/0.269 与 0.88/0.12）。
    """
    # ---- 数值校验（与正文 / check_ch09.py B2 一致）----
    p1_t1, p2_t1 = softmax_pair(2.0, 1.0, 1.0)   # 正文 9.1.2
    p1_t05, p2_t05 = softmax_pair(2.0, 1.0, 0.5)  # 正文 9.5.2
    assert abs(p1_t1 - 0.731) < 0.002 and abs(p2_t1 - 0.269) < 0.002
    assert abs(p1_t05 - 0.88) < 0.01 and abs(p2_t05 - 0.12) < 0.01

    fig, (axL, axR) = plt.subplots(
        1, 2, figsize=(10.2, 4.5),
        gridspec_kw={'width_ratios': [1.25, 1.0]})

    # ---- 左：温度曲线（聚焦 τ∈[0.2,2.0] 过渡段）----
    taus = np.linspace(0.2, 2.0, 300)
    p1 = np.exp(2.0 / taus) / (np.exp(2.0 / taus) + np.exp(1.0 / taus))
    p2 = 1.0 - p1
    axL.plot(taus, p1, color='#1f618d', lw=2.6, label=r'$\pi(a_1)$（偏好 2.0）')
    axL.plot(taus, p2, color='#b7950b', lw=2.6, label=r'$\pi(a_2)$（偏好 1.0）')
    # 两个正文标注点
    axL.axvline(0.5, color='#c0392b', ls='--', lw=1.2, alpha=0.7)
    axL.axvline(1.0, color='#c0392b', ls='--', lw=1.2, alpha=0.7)
    axL.plot([0.5], [p1_t05], 'o', ms=7, color='#c0392b', zorder=5)
    axL.plot([1.0], [p1_t1], 'o', ms=7, color='#c0392b', zorder=5)
    axL.annotate(r'$\tau=0.5 \to 0.88/0.12$（温度减半，正文 9.5.2）',
                 xy=(0.5, p1_t05), xytext=(0.52, 0.965),
                 fontsize=9, color='#c0392b',
                 arrowprops=dict(arrowstyle='->', color='#c0392b', lw=1.1))
    axL.annotate(r'$\tau=1 \to 0.731/0.269$（正文 9.1.2）',
                 xy=(1.0, p1_t1), xytext=(1.28, 0.80),
                 fontsize=9, color='#c0392b',
                 arrowprops=dict(arrowstyle='->', color='#c0392b', lw=1.1))
    axL.text(0.24, 0.07, r'$\tau \to 0$：只选首选（1/0）',
             fontsize=8.5, color='#566573')
    axL.text(1.42, 0.62, r'$\tau \to \infty$：均匀（0.5/0.5）',
             fontsize=8.5, color='#566573')
    # 聚焦数轴：起止 0.2~2.0、刻度步长见 xticks
    axL.set_xlim(0.2, 2.0)
    axL.set_ylim(0, 1.05)
    axL.set_xticks([0.2, 0.5, 1.0, 1.5, 2.0])
    axL.set_xlabel('决策锐度 $\\tau$（越小越集中，越大越均匀；聚焦 0.2-2.0）',
                   fontsize=10.5)
    axL.set_ylabel('动作概率 $\\pi(a)$', fontsize=10.5)
    axL.grid(alpha=0.3)
    axL.legend(loc='lower left', fontsize=9.5)

    # ---- 右：tau=1 与 tau=0.5 的概率条形（仅正文两组数值）----
    axR.bar([0.35], [p1_t1], width=0.5, color='#1f618d', alpha=0.92, zorder=3)
    axR.bar([1.05], [p2_t1], width=0.5, color='#85c1e9', alpha=0.92, zorder=3)
    axR.bar([1.85], [p1_t05], width=0.5, color='#b9770e', alpha=0.92, zorder=3)
    axR.bar([2.55], [p2_t05], width=0.5, color='#f5cba7', alpha=0.92, zorder=3)
    axR.text(0.35, p1_t1 + 0.03, '0.731', ha='center', fontsize=10,
             fontweight='bold')
    axR.text(1.05, p2_t1 + 0.03, '0.269', ha='center', fontsize=10)
    axR.text(1.85, p1_t05 + 0.03, '0.88', ha='center', fontsize=10,
             fontweight='bold')
    axR.text(2.55, p2_t05 + 0.03, '0.12', ha='center', fontsize=10)
    axR.text(0.7, 0.55, r'$\tau=1$', ha='center', fontsize=11)
    axR.text(2.2, 0.55, r'$\tau=0.5$', ha='center', fontsize=11)
    axR.annotate('锐度减半\n试新收缩', xy=(1.45, 0.95), xytext=(1.45, 0.72),
                 ha='center', fontsize=9.5, color='#7d6608',
                 arrowprops=dict(arrowstyle='->', color='#7d6608', lw=1.3))
    axR.set_ylim(0, 1.05)
    axR.set_xticks([])
    axR.set_ylabel('动作概率', fontsize=10.5)
    axR.grid(axis='y', alpha=0.3)

    fig.tight_layout()
    fig.savefig(os.path.join(OUT, 'fig9-1.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('fig9-1 done   tau=1: %.3f/%.3f, tau=0.5: %.3f/%.3f'
          % (p1_t1, p2_t1, p1_t05, p2_t05))


def pg_model(theta1, theta2):
    """9.2.2 两状态两动作模型：返回 (pi1, pi2, d1, rbar, grad1)。
    约定：softmax 策略 h(a1)=theta1、h(a2)=theta2（两状态共用，正文 v2 口径）；
    s1 下 a1->s1、a2->s2；s2 任意->s1；r(s1,a1)=2、r(s1,a2)=0、r(s2,·)=0。"""
    pi1 = math.exp(theta1) / (math.exp(theta1) + math.exp(theta2))
    pi2 = 1.0 - pi1
    d1 = 1.0 / (1.0 + pi2)          # 平稳方程 d(s1)=1/(1+pi2)
    rbar = d1 * pi1 * 2.0           # 平均回报 J(theta)
    grad1 = d1 * pi1 * pi2 * (2.0 + rbar)   # 相对动作价值口径梯度
    return pi1, pi2, d1, rbar, grad1


def fig9_2():
    """图 9-2 策略梯度上升轨迹：参数空间迭代与目标函数上升（正文 9.2.2）

    聚焦：左图参数空间 θ1∈[0.95,1.65]、θ2∈[-0.15,0.55]（轨迹 12 步
          1.0,0.5 -> 1.568,-0.068 全段可见）；右图 J 聚焦 [0.88,1.50]、
          迭代步 0-12（J 0.904 -> 1.440 的上升段）。
    """
    # ---- 数值校验（与正文 9.2.2 一致）----
    pi1_0, pi2_0, d1_0, rbar_0, grad1_0 = pg_model(1.0, 0.5)
    assert abs(pi1_0 - 0.62) < 0.01 and abs(pi2_0 - 0.38) < 0.01
    assert abs(d1_0 - 0.726) < 0.005
    assert abs(grad1_0 - 0.495) < 0.005   # 正文 v2：∇θ1≈0.495

    # ---- 梯度上升迭代（alpha=0.1，对称性保证 theta1+theta2=1.5 守恒）----
    alpha = 0.1
    steps = 12
    th1 = 1.0
    th2 = 0.5
    traj = [(th1, th2)]
    Js = [rbar_0]
    for _ in range(steps):
        _, _, _, _, g1 = pg_model(th1, th2)
        th1 = th1 + alpha * g1
        th2 = 1.5 - th1            # grad2 = -grad1（对称性）
        traj.append((th1, th2))
        Js.append(pg_model(th1, th2)[3])
    # J 单调上升（容许数值舍入的平台期）
    for a, b in zip(Js, Js[1:]):
        assert b >= a - 1e-9
    print('fig9-2 迭代: J: %.3f -> %.3f, theta1: %.3f -> %.3f'
          % (Js[0], Js[-1], traj[0][0], traj[-1][0]))

    fig, (axL, axR) = plt.subplots(1, 2, figsize=(11.2, 4.9))

    # ---- 左：参数空间等高线 + 迭代轨迹（聚焦轨迹全段）----
    g1 = np.linspace(0.95, 1.65, 240)
    g2 = np.linspace(-0.15, 0.55, 240)
    G1, G2 = np.meshgrid(g1, g2)
    Jg = np.empty_like(G1)
    for i in range(g1.size):
        for j in range(g2.size):
            Jg[j, i] = pg_model(g1[i], g2[j])[3]
    cf = axL.contour(G1, G2, Jg, levels=np.linspace(0.90, 1.45, 12),
                     cmap='YlOrBr', alpha=0.75, zorder=1)
    axL.clabel(cf, inline=True, fontsize=7.5, fmt='%.2f')
    tx = [t[0] for t in traj]
    ty = [t[1] for t in traj]
    axL.plot(tx, ty, color='#1f618d', lw=1.8, ls='--', zorder=4)
    axL.plot(tx, ty, 'o', ms=5, color='#1f618d', zorder=5)
    axL.plot(tx[0], ty[0], 'o', ms=10, color='#c0392b', zorder=6)
    axL.annotate('起点 (1.0,0.5)', xy=(1.0, 0.5),
                 xytext=(0.955, 0.56), fontsize=9.5, color='#c0392b',
                 arrowprops=dict(arrowstyle='->', color='#c0392b', lw=1.2))
    # 初始梯度方向箭头（∇θ≈(0.495,-0.495)）
    axL.add_patch(FancyArrowPatch((1.0, 0.5), (1.0 + 0.30 * 0.495,
                                               0.5 - 0.30 * 0.495),
                                  arrowstyle='-|>', mutation_scale=18,
                                  color='#1e8449', lw=2.4, zorder=6))
    axL.text(1.02, 0.435, r'调优方向 $\approx (0.495,-0.495)$',
             fontsize=9.5, color='#1e8449')
    # 12 步终点
    axL.plot(tx[-1], ty[-1], 's', ms=7, color='#1a5276', zorder=6)
    axL.annotate('12 步后 (1.57,-0.07)', xy=(tx[-1], ty[-1]),
                 xytext=(1.24, -0.125), fontsize=9, color='#1a5276',
                 arrowprops=dict(arrowstyle='->', color='#1a5276', lw=1.1))
    # 聚焦数轴：起止与步长
    axL.set_xlim(0.95, 1.65)
    axL.set_ylim(-0.15, 0.55)
    axL.set_xticks([1.0, 1.2, 1.4, 1.6])
    axL.set_yticks([0.0, 0.2, 0.4])
    axL.set_xlabel('首选方偏好', fontsize=10.5)
    axL.set_ylabel('备选方偏好', fontsize=10.5)
    axL.grid(alpha=0.3)

    # ---- 右：目标函数 J(theta) 随迭代上升（聚焦上升段 0.88-1.50）----
    axR.plot(range(steps + 1), Js, color='#b9770e', lw=2.6, marker='o', ms=5,
             zorder=3)
    axR.annotate('初始 $J \\approx 0.90$\n（平均疗效）', xy=(0, Js[0]),
                 xytext=(1.0, 0.92), fontsize=9, color='#7d6608',
                 arrowprops=dict(arrowstyle='->', color='#7d6608', lw=1.1))
    axR.annotate('沿调优方向调整\n平均疗效单调上升', xy=(steps, Js[-1]),
                 xytext=(6.0, 1.35), fontsize=9.5, color='#1f618d',
                 arrowprops=dict(arrowstyle='->', color='#1f618d', lw=1.1))
    axR.set_xlim(-0.4, steps + 0.6)
    axR.set_ylim(0.88, 1.50)
    axR.set_xticks([0, 3, 6, 9, 12])
    axR.set_yticks([0.9, 1.0, 1.1, 1.2, 1.3, 1.4])
    axR.set_xlabel('迭代步数 $k$（学习率 $\\alpha=0.1$；聚焦 0-12 步）',
                   fontsize=10.5)
    axR.set_ylabel(r'平均疗效 $J$', fontsize=10.5)
    axR.grid(alpha=0.3)

    fig.tight_layout()
    fig.savefig(os.path.join(OUT, 'fig9-2.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('fig9-2 done')


def fig9_3():
    """图 9-3 探索与利用权衡：探索率 epsilon 随成长阶段衰减（正文 9.5.1、9.5.2）

    聚焦：x ∈ [0, 80]（旧 [0, 100]），聚焦探索→利用过渡段——住院医
    0-33 高探索、主治 33-66 缓降、副高 66-80 低位起始，裁掉右端
    低平尾段（>80 的 ε<0.1 区）；底部教学示意说明行移除（并入图注）。
    """
    fig, ax = plt.subplots(figsize=(9.4, 4.6))

    x = np.linspace(0, 80, 400)
    eps = 0.9 * np.exp(-0.028 * x)      # 教学示意曲线：初期高、中期缓降、后期低位
    # 三阶段背景色带与竖线（第三段仅到 80）
    ax.axvspan(0, 33, color='#fdebd0', alpha=0.9, zorder=0)
    ax.axvspan(33, 66, color='#fcf3cf', alpha=0.9, zorder=0)
    ax.axvspan(66, 80, color='#eafaf1', alpha=0.9, zorder=0)
    for xv in (33, 66):
        ax.axvline(xv, color='#aab7b8', ls='--', lw=1.2, zorder=2)
    ax.plot(x, eps, color='#c0392b', lw=3.0, zorder=4)
    ax.text(16.5, 0.68, '住院医阶段\n高试探比例\n低风险虚拟病例大胆试错',
            ha='center', fontsize=9.5, color='#7d6608', linespacing=1.45)
    ax.text(49.5, 0.46, '主治阶段\n缓降\n把成熟经验提炼为可复用策略',
            ha='center', fontsize=9.5, color='#7d6608', linespacing=1.45)
    ax.text(73, 0.30, '副高以上\n低位\n仅证据不足的新场景探索',
            ha='center', fontsize=9.5, color='#1e8449', linespacing=1.45)
    # 探索 -> 利用 过渡箭头（聚焦段内）
    ax.annotate('', xy=(77, 0.05), xytext=(77, 0.72),
                arrowprops=dict(arrowstyle='-|>', color='#566573', lw=1.8),
                zorder=3)
    ax.text(78.4, 0.40, '探索 → 利用\n过渡', rotation=90, va='center',
            fontsize=9, color='#566573', linespacing=1.3)
    # 聚焦数轴：起止 0~80、刻度 0/33/66/80
    ax.set_xlim(0, 80)
    ax.set_ylim(0, 0.98)
    ax.set_xticks([0, 33, 66, 80])
    ax.set_xticklabels(['起步', '住院医', '主治', '副高以上'])
    ax.set_xlabel('训练轮次 / 职业成长阶段（聚焦探索→利用过渡段 0-80）',
                  fontsize=10.5)
    ax.set_ylabel('试探比例 $\\varepsilon$', fontsize=10.5)
    ax.grid(axis='y', alpha=0.3)

    fig.tight_layout()
    fig.savefig(os.path.join(OUT, 'fig9-3.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('fig9-3 done')


def fig9_4():
    """图 9-4 正态分布策略示意：连续动作，均值 mu 附近高斯分布采样（正文 9.6.1、9.6.2）

    聚焦：横轴 [0, 3.2]（旧 [-1.6, 4.6]），保留均值 μ=1.5 附近两条曲线
    主体与红色均值虚线；刻度步长 0.5；底部中医示例行移除（并入图注）。
    """
    mu = 1.5          # 正文 9.6.2 演算取值
    sig_s = 0.5       # 正文 9.6.2：sigma=0.5
    sig_l = 1.0       # 大方差对照（教学示意）
    a = np.linspace(0.0, 3.2, 500)
    p_s = (1.0 / (sig_s * math.sqrt(2 * math.pi))) * \
          np.exp(-0.5 * ((a - mu) / sig_s) ** 2)
    p_l = (1.0 / (sig_l * math.sqrt(2 * math.pi))) * \
          np.exp(-0.5 * ((a - mu) / sig_l) ** 2)

    fig, ax = plt.subplots(figsize=(9.0, 4.6))
    ax.plot(a, p_s, color='#1f618d', lw=2.8,
            label=r'$\sigma=0.5$（方差小：利用强，动作抖动小；正文 9.6.2 取值）')
    ax.plot(a, p_l, color='#b9770e', lw=2.8,
            label=r'$\sigma=1.0$（方差大：探索强，动作抖动大；对照示意）')
    ax.axvline(mu, color='#c0392b', ls='--', lw=1.4)
    ax.plot([mu], [0], 'o', ms=8, color='#c0392b', zorder=5)
    ax.annotate(r'均值 $\mu=1.5$：最可能采取的动作', xy=(mu, 0),
                xytext=(1.55, 0.62), fontsize=10, color='#c0392b',
                arrowprops=dict(arrowstyle='->', color='#c0392b', lw=1.2))
    ax.annotate('每次先在均值附近随机“抖一下”\n再输出动作', xy=(2.35, 0.30),
                xytext=(1.95, 0.78), fontsize=9.5, color='#2c3e50',
                arrowprops=dict(arrowstyle='->', color='#2c3e50', lw=1.1))
    # 聚焦数轴：起止 0~3.2、刻度步长 0.5
    ax.set_xlim(0, 3.2)
    ax.set_ylim(0, 0.85)
    ax.set_xticks([0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0])
    ax.set_xlabel('动作 $a$（如方剂剂量 / g；聚焦均值附近 0-3.2）', fontsize=10.5)
    ax.set_ylabel(r'概率密度 $\pi(a|s,\theta)$', fontsize=10.5)
    ax.grid(alpha=0.3)
    ax.legend(loc='upper left', fontsize=9.5)

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
