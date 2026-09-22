# -*- coding: utf-8 -*-
"""《中医场景强化学习》第9章 核心图生成脚本（图表工程师批次：图 9-1 ~ 图 9-4）

生成：fig9-1 softmax 策略示意（温度 tau 对动作概率分布的影响曲线）
      fig9-2 策略梯度上升轨迹（参数空间 theta 迭代，目标函数 J(theta) 上升）
      fig9-3 探索与利用权衡（epsilon 衰减曲线：探索 -> 利用过渡）
      fig9-4 正态分布策略示意（连续动作：均值 mu 附近高斯分布采样）
输出：drafts/cmrl/figures/ch09/*.png
范式：与 figures/gen_ch01_figures.py、gen_ch07_figures.py 一致 —— SimHei /
      unicode_minus=False / Agg / dpi=200 / bbox_inches='tight' / 图题入图
数值一致性（正文口径）：
      9.1.2  softmax(2.0,1.0) tau=1 -> 0.731 / 0.269
      9.5.2  温度减半 tau=0.5 -> 0.88 / 0.12
      9.2.2  两状态模型：theta=(1.0,0.5)、pi(a1)≈0.62、d_pi(s1)≈0.726、
             d_pi(s2)≈0.274、nabla_theta1≈0.495、nabla_theta2≈-0.495
      9.6.2  高斯演算：mu=1.5、sigma=0.5（a=1.8、残差 1.2）
      9.5.2  探索率衰减：初期高、中期缓降、后期低位（曲线为教学示意）
字形安全：theta/tau/pi/mu/sigma/varepsilon/nabla 一律用 mathtext，
          避免 SimHei 缺失的 U+2081 下标与 U+2212 减号。
"""
import os
import math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrowPatch, FancyBboxPatch

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
    """图 9-1 softmax 策略示意：温度 tau 对动作概率分布的影响（正文 9.1.2、9.5.2）"""
    # ---- 数值校验（与正文 / check_ch09.py B2 一致）----
    p1_t1, p2_t1 = softmax_pair(2.0, 1.0, 1.0)   # 正文 9.1.2
    p1_t05, p2_t05 = softmax_pair(2.0, 1.0, 0.5)  # 正文 9.5.2
    assert abs(p1_t1 - 0.731) < 0.002 and abs(p2_t1 - 0.269) < 0.002
    assert abs(p1_t05 - 0.88) < 0.01 and abs(p2_t05 - 0.12) < 0.01

    fig, (axL, axR) = plt.subplots(
        1, 2, figsize=(12.8, 5.6),
        gridspec_kw={'width_ratios': [1.35, 1.0]})
    fig.suptitle('图9-1 softmax 策略示意：温度 $\\tau$ 对动作概率分布的影响\n'
                 '偏好 h(a1)=2.0、h(a2)=1.0（正文 9.1.2）',
                 fontsize=13.5, y=0.99)

    # ---- 左：温度曲线 ----
    taus = np.linspace(0.15, 3.0, 300)
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
                 xy=(0.5, p1_t05), xytext=(0.62, 0.97),
                 fontsize=9.5, color='#c0392b',
                 arrowprops=dict(arrowstyle='->', color='#c0392b', lw=1.2))
    axL.annotate(r'$\tau=1 \to 0.731/0.269$（正文 9.1.2）',
                 xy=(1.0, p1_t1), xytext=(1.55, 0.88),
                 fontsize=9.5, color='#c0392b',
                 arrowprops=dict(arrowstyle='->', color='#c0392b', lw=1.2))
    axL.text(0.22, 0.06, r'$\tau \to 0$：只选首选（1/0）',
             fontsize=9.5, color='#566573')
    axL.text(2.02, 0.55, r'$\tau \to \infty$：均匀（0.5/0.5）',
             fontsize=9.5, color='#566573')
    axL.set_xlabel('决策锐度 $\\tau$（越小越集中，越大越均匀）', fontsize=11)
    axL.set_ylabel('动作概率 $\\pi(a)$', fontsize=11)
    axL.set_xlim(0.15, 3.0)
    axL.set_ylim(0, 1.05)
    axL.grid(alpha=0.3)
    axL.legend(loc='center right', fontsize=10.5)

    # ---- 右：tau=1 与 tau=0.5 的概率条形 ----
    axR.bar([0.35], [p1_t1], width=0.5, color='#1f618d', alpha=0.92, zorder=3)
    axR.bar([1.05], [p2_t1], width=0.5, color='#85c1e9', alpha=0.92, zorder=3)
    axR.bar([1.85], [p1_t05], width=0.5, color='#b9770e', alpha=0.92, zorder=3)
    axR.bar([2.55], [p2_t05], width=0.5, color='#f5cba7', alpha=0.92, zorder=3)
    axR.text(0.35, p1_t1 + 0.03, '0.731', ha='center', fontsize=10, fontweight='bold')
    axR.text(1.05, p2_t1 + 0.03, '0.269', ha='center', fontsize=10)
    axR.text(1.85, p1_t05 + 0.03, '0.88', ha='center', fontsize=10, fontweight='bold')
    axR.text(2.55, p2_t05 + 0.03, '0.12', ha='center', fontsize=10)
    axR.text(0.7, 0.55, r'$\tau=1$', ha='center', fontsize=11)
    axR.text(2.2, 0.55, r'$\tau=0.5$', ha='center', fontsize=11)
    axR.annotate('锐度减半\n试新收缩', xy=(1.45, 0.95), xytext=(1.45, 0.70),
                 ha='center', fontsize=10, color='#7d6608',
                 arrowprops=dict(arrowstyle='->', color='#7d6608', lw=1.4))
    axR.set_ylim(0, 1.05)
    axR.set_xticks([])
    axR.set_ylabel('动作概率', fontsize=11)
    axR.grid(axis='y', alpha=0.3)

    fig.tight_layout(rect=[0, 0.02, 1, 0.94])
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
    """图 9-2 策略梯度上升轨迹：参数空间迭代与目标函数上升（正文 9.2.2）"""
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

    fig, (axL, axR) = plt.subplots(1, 2, figsize=(12.8, 5.8))
    fig.suptitle('图9-2 策略梯度上升轨迹：参数空间迭代与目标函数上升\n'
                 '两状态两动作任务（正文 9.2.2）：$\\theta=(1.0,0.5)$、'
                 '$\\pi(a_1)\\approx 0.62$、$d_\\pi(s_1)\\approx 0.726$、'
                 '$\\nabla_{\\theta_1}\\approx 0.495$',
                 fontsize=13.5, y=0.99)

    # ---- 左：参数空间等高线 + 迭代轨迹 ----
    g1 = np.linspace(0.85, 1.75, 240)
    g2 = np.linspace(-0.05, 0.65, 240)
    G1, G2 = np.meshgrid(g1, g2)
    Jg = np.empty_like(G1)
    for i in range(g1.size):
        for j in range(g2.size):
            Jg[j, i] = pg_model(g1[i], g2[j])[3]
    cf = axL.contour(G1, G2, Jg, levels=np.linspace(0.90, 1.55, 12),
                     cmap='YlOrBr', alpha=0.75, zorder=1)
    axL.clabel(cf, inline=True, fontsize=8, fmt='%.2f')
    tx = [t[0] for t in traj]
    ty = [t[1] for t in traj]
    axL.plot(tx, ty, color='#1f618d', lw=1.8, ls='--', zorder=4)
    axL.plot(tx, ty, 'o', ms=5, color='#1f618d', zorder=5)
    axL.plot(tx[0], ty[0], 'o', ms=10, color='#c0392b', zorder=6)
    axL.annotate('起点 (1.0,0.5)', xy=(1.0, 0.5),
                 xytext=(0.87, 0.60), fontsize=10.5, color='#c0392b',
                 arrowprops=dict(arrowstyle='->', color='#c0392b', lw=1.3))
    # 初始梯度方向箭头（∇θ≈(0.495,-0.495)）
    axL.add_patch(FancyArrowPatch((1.0, 0.5), (1.0 + 0.30 * 0.495, 0.5 - 0.30 * 0.495),
                                  arrowstyle='-|>', mutation_scale=18,
                                  color='#1e8449', lw=2.4, zorder=6))
    axL.text(1.09, 0.42, r'调优方向 $\approx (0.495,-0.495)$',
             fontsize=10.5, color='#1e8449')
    axL.set_xlabel('首选方偏好', fontsize=11)
    axL.set_ylabel('备选方偏好', fontsize=11)
    axL.set_xlim(0.85, 1.75)
    axL.set_ylim(-0.05, 0.65)
    axL.grid(alpha=0.3)

    # ---- 右：目标函数 J(theta) 随迭代上升 ----
    axR.plot(range(steps + 1), Js, color='#b9770e', lw=2.6, marker='o', ms=5, zorder=3)
    axR.annotate('初始 $J \\approx %.2f$\n（平均疗效）' % Js[0],
                 xy=(0, Js[0]), xytext=(1.2, 0.94),
                 fontsize=10, color='#7d6608',
                 arrowprops=dict(arrowstyle='->', color='#7d6608', lw=1.2))
    axR.annotate('沿调优方向调整\n平均疗效单调上升', xy=(steps, Js[-1]),
                 xytext=(5.5, 1.22), fontsize=10.5, color='#1f618d',
                 arrowprops=dict(arrowstyle='->', color='#1f618d', lw=1.2))
    axR.set_xlabel('调整步数 $k$（每次调整幅度 0.1）', fontsize=11)
    axR.set_ylabel(r'平均疗效 $J$', fontsize=11)
    axR.set_xlim(-0.5, steps + 1.0)
    axR.set_ylim(0.85, 1.40)
    axR.grid(alpha=0.3)

    fig.tight_layout(rect=[0, 0.02, 1, 0.93])
    fig.savefig(os.path.join(OUT, 'fig9-2.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('fig9-2 done')


def fig9_3():
    """图 9-3 探索与利用权衡：探索率 epsilon 随成长阶段衰减（正文 9.5.1、9.5.2）"""
    fig, ax = plt.subplots(figsize=(11.8, 5.8))
    fig.suptitle('图9-3 探索与利用权衡：探索率 $\\varepsilon$ 随成长阶段衰减\n'
                 '探索=点一道没吃过的新菜，利用=点那道从不踩雷的老字号（正文 9.5.1）',
                 fontsize=13.5, y=0.98)

    x = np.linspace(0, 100, 400)
    eps = 0.9 * np.exp(-0.028 * x)      # 教学示意曲线：初期高、中期缓降、后期低位
    # 三阶段背景色带与竖线
    ax.axvspan(0, 33, color='#fdebd0', alpha=0.9, zorder=0)
    ax.axvspan(33, 66, color='#fcf3cf', alpha=0.9, zorder=0)
    ax.axvspan(66, 100, color='#eafaf1', alpha=0.9, zorder=0)
    for xv in (33, 66):
        ax.axvline(xv, color='#aab7b8', ls='--', lw=1.2, zorder=2)
    ax.plot(x, eps, color='#c0392b', lw=3.0, zorder=4)
    ax.text(16.5, 0.66, '住院医阶段\n高试探比例\n低风险虚拟病例大胆试错',
            ha='center', fontsize=10.5, color='#7d6608', linespacing=1.45)
    ax.text(49.5, 0.42, '主治阶段\n缓降\n把成熟经验提炼为可复用策略',
            ha='center', fontsize=10.5, color='#7d6608', linespacing=1.45)
    ax.text(83, 0.24, '副高以上\n低位\n仅证据不足的新场景探索',
            ha='center', fontsize=10.5, color='#1e8449', linespacing=1.45)
    # 探索 -> 利用 过渡箭头
    ax.annotate('', xy=(97, 0.055), xytext=(97, 0.80),
                arrowprops=dict(arrowstyle='-|>', color='#566573', lw=1.8), zorder=3)
    ax.text(97.6, 0.44, '探索 → 利用\n过渡', rotation=90, va='center',
            fontsize=10, color='#566573', linespacing=1.3)
    # 右下角：点菜/老字号小框
    ax.add_patch(FancyBboxPatch((74, 0.60), 24.5, 0.32, boxstyle='round,pad=0.02',
                                facecolor='white', edgecolor='#566573', lw=1.0, zorder=5))
    ax.text(86.2, 0.76, '信息收益递减之处，就是探索应当收敛之时',
            ha='center', fontsize=9, color='#2c3e50', zorder=6)
    ax.set_xlabel('训练轮次 / 职业成长阶段', fontsize=11.5)
    ax.set_ylabel('试探比例 $\\varepsilon$', fontsize=11.5)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 0.98)
    ax.set_xticks([0, 33, 66, 100])
    ax.set_xticklabels(['起步', '住院医', '主治', '副高以上'])
    ax.grid(axis='y', alpha=0.3)
    ax.text(0.5, -0.20,
            '注：曲线为教学示意（正文仅定性描述“初期高、中期缓降、后期低位”，见 9.5.2）',
            transform=ax.transAxes, ha='center', fontsize=9, color='#7f8c8d')

    fig.tight_layout(rect=[0, 0.04, 1, 0.93])
    fig.savefig(os.path.join(OUT, 'fig9-3.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('fig9-3 done')


def fig9_4():
    """图 9-4 正态分布策略示意：连续动作，均值 mu 附近高斯分布采样（正文 9.6.1、9.6.2）"""
    mu = 1.5          # 正文 9.6.2 演算取值
    sig_s = 0.5       # 正文 9.6.2：sigma=0.5
    sig_l = 1.0       # 大方差对照（教学示意）
    a = np.linspace(-1.6, 4.6, 500)
    p_s = (1.0 / (sig_s * math.sqrt(2 * math.pi))) * np.exp(-0.5 * ((a - mu) / sig_s) ** 2)
    p_l = (1.0 / (sig_l * math.sqrt(2 * math.pi))) * np.exp(-0.5 * ((a - mu) / sig_l) ** 2)

    fig, ax = plt.subplots(figsize=(10.8, 5.9))
    fig.suptitle('图9-4 正态分布策略示意：均值附近随机抖动\n'
                 r'$\pi(a|s,\theta)=\mathcal{N}(a;\mu(s,\theta),\sigma^2)$'
                 ' —— 均值决定在哪，方差决定抖多大（正文 9.6.1）',
                 fontsize=13.5, y=0.98)
    ax.plot(a, p_s, color='#1f618d', lw=2.8,
            label=r'$\sigma=0.5$（方差小：利用强，动作抖动小；正文 9.6.2 取值）')
    ax.plot(a, p_l, color='#b9770e', lw=2.8,
            label=r'$\sigma=1.0$（方差大：探索强，动作抖动大；对照示意）')
    ax.axvline(mu, color='#c0392b', ls='--', lw=1.4)
    ax.plot([mu], [0], 'o', ms=8, color='#c0392b', zorder=5)
    ax.annotate(r'均值 $\mu=1.5$：最可能采取的动作', xy=(mu, 0),
                xytext=(2.1, 0.55), fontsize=10.5, color='#c0392b',
                arrowprops=dict(arrowstyle='->', color='#c0392b', lw=1.3))
    ax.annotate('每次先在均值附近随机“抖一下”\n再输出动作', xy=(2.35, 0.30),
                xytext=(2.7, 0.72), fontsize=10, color='#2c3e50',
                arrowprops=dict(arrowstyle='->', color='#2c3e50', lw=1.2))
    # 中医连续动作示例
    ax.text(0.5, -0.19,
            '中医连续动作：方剂剂量（0–30 g）、针刺深度、疗程长短、康复训练强度'
            '——不是“轻、中、重”三档，而是连续可调的量',
            transform=ax.transAxes, ha='center', fontsize=9.5, color='#7f8c8d')
    ax.set_xlabel('动作 $a$（如方剂剂量 / g）', fontsize=11.5)
    ax.set_ylabel('概率密度 $\\pi(a|s,\\theta)$', fontsize=11.5)
    ax.set_xlim(-1.6, 4.6)
    ax.set_ylim(0, 0.88)
    ax.grid(alpha=0.3)
    ax.legend(loc='upper left', fontsize=10)

    fig.tight_layout(rect=[0, 0.06, 1, 0.93])
    fig.savefig(os.path.join(OUT, 'fig9-4.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('fig9-4 done')


if __name__ == '__main__':
    fig9_1()
    fig9_2()
    fig9_3()
    fig9_4()
    print('ALL DONE ->', OUT)
