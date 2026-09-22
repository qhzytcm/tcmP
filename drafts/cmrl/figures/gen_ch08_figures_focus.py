# -*- coding: utf-8 -*-
"""《中医场景强化学习》第8章 核心图生成脚本（v2 聚焦版，图表工程师）

聚焦原则（用户要求，延续 ch02/ch03 实测范式）：
  - 图体只保留'能代表含义的图段'——收紧 figsize 与 xlim/ylim/xticks/yticks，
    聚焦关键区域（fig8-1 聚焦 s∈[1,3] 样本密集段；fig8-2 聚焦损失快速下降段前 50 步）；
  - 图题由 Excel sheet 图题行承担（图体上方一行居中黑体），图内不再重复大标题；
  - 图注由 Excel sheet 图注行承担（图体下方一行左顶格），四要素：
    a.对接正文提示语 / b.线的注释 / c.符号的注释 / d.代表含义的指针图段；
    与正文 md 图注逐字一致；
  - 图内底部说明行移除（信息并入图注 d）。

生成：fig8-1 ~ fig8-4（覆盖 figures/ch08/*.png）
数值口径与正文 8.1–8.5 节严格一致（与 gen_ch08_figures.py 同源）：
  - 例8.1/8.1.2：φ(s)=[s,1]^T，w=[a,b]^T，v̂(s)=as+b，仅 2 个参数
  - 例8.2/8.2.2：4 状态链 γ=0.9、α=0.1、w0=[0,0]；首次访问 s3 误差 1 → w=[0.3,0.1]；
    v̂(s1)=0.4、v̂(s2)=0.7、v̂(s3)=1.0；再次访问 s2：TD 目标 0.9、误差 0.2
  - 8.2.1：MSE 目标 J(w)、Robbins-Monro 条件 Σαt=∞ 且 Σαt²<∞、小批量折中方差
  - 8.4.1：10000 状态≈1MB、10^10 状态≈1TB（每条目约 100B）；函数法 m=50（≈0.4 KB）
  - 例8.4/8.4.2：状态 10000、每状态访问 100 次、函数法 m=50 参数
  - 8.5.1/8.5.2：r_total=w1·r_生理+w2·r_心理+w3·r_社会+w4·r_环境；例8.5 失眠伴焦虑患者
    四类动作：安神方剂（生理）/情志疏导（心理）/家庭支持（社会）/作息节律（环境）
字体约定：图内数学符号一律 mathtext（$\\hat{v}$、$\\varphi^\\top$、$^2$、$v_\\pi$），
      避免 SimHei 缺失字形（U+0302 组合抑扬符、U+1D40、U+226A、U+2212 等；
      图内 '≪' 用 ASCII '<<'，减号用 ASCII '-'）。
"""
import os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from matplotlib.lines import Line2D
from matplotlib.ticker import FuncFormatter

plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ch08')
os.makedirs(OUT, exist_ok=True)


def box(ax, x, y, w, h, fc, ec, txt, fs=10.5, tc='#1b2631', lw=1.6,
        style='round,pad=0.06', bold=False, ls=1.45):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=style,
                                facecolor=fc, edgecolor=ec, lw=lw, zorder=2))
    ax.text(x + w / 2, y + h / 2, txt, ha='center', va='center',
            fontsize=fs, color=tc, zorder=3,
            fontweight='bold' if bold else 'normal', linespacing=ls)


# ============================================================
# 图 8-1 函数近似拟合曲线（正文 8.1.2，例8.1 直线拟合 + 例8.2 锚点）
# 聚焦：s∈[1,3] 样本密集段（三个红锚点恰在拟合线上，最能代表
#       "参数共享 + 残差"含义；s=4,5 及千万级其余状态裁出图外，入图注 d）
# ============================================================
def fig8_1():
    fig, ax = plt.subplots(figsize=(8.6, 4.9))
    s_all = np.array([1.0, 2.0, 3.0])          # 聚焦样本密集段 s1~s3
    v_true = np.array([0.35, 0.75, 0.95])      # 真实价值（围绕拟合线小幅波动）
    s_fit = np.linspace(0.7, 3.5, 100)
    v_fit = 0.3 * s_fit + 0.1

    # 残差虚线（s1~s3）
    for s, v in zip(s_all, v_true):
        ax.plot([s, s], [v, 0.3 * s + 0.1], color='#e67e22', lw=1.3,
                ls=':', zorder=1)
    # 真实价值散点
    ax.scatter(s_all, v_true, s=60, color='#7f8c8d', zorder=3,
               label=r'真实价值 $v_\pi(s)$（数据点）')
    # 拟合直线
    ax.plot(s_fit, v_fit, color='#1f618d', lw=2.8, zorder=4,
            label=r'线性近似 $\hat{v}(s)=\varphi^\top w=0.3s+0.1$')
    # 例8.2 锚点红点（恰在拟合线上）
    for s, v in [(1, 0.4), (2, 0.7), (3, 1.0)]:
        ax.plot(s, v, 'o', color='#c0392b', ms=7, zorder=5)
        ax.annotate(r'$\hat{v}(s_%d)$' % s, xy=(s, v),
                    xytext=(s + 0.09, v + 0.045), fontsize=10,
                    color='#c0392b', zorder=5)

    # 残差标注（指向 s1 的残差段）
    ax.annotate(r'残差 = $v_\pi-\hat{v}$（近似误差）', xy=(1.0, 0.375),
                xytext=(1.62, 0.28), fontsize=9.5, color='#e67e22',
                arrowprops=dict(arrowstyle='->', color='#e67e22', lw=1.2),
                zorder=5)

    # 特征/参数框（左上，聚焦信息）
    ax.text(0.78, 1.00,
            r'特征 $\varphi(s)=[s,1]^\top$' + '\n' +
            r'参数 $w=[0.3,0.1]$（与例8.2 相同）' + '\n' +
            'm = 2 << n：仅 2 个参数表示任意多状态',
            fontsize=9.5, color='#1f618d', linespacing=1.45,
            bbox=dict(boxstyle='round,pad=0.45', facecolor='#eaf2f8',
                      edgecolor='#1f618d', lw=1.1), zorder=6)

    ax.set_xlabel('证候 s（聚焦 s1~s3 样本密集段，对应正文 8.1.2）', fontsize=11)
    ax.set_ylabel(r'疗效把握 $\hat{v}(s,w)$', fontsize=11)
    ax.set_xlim(0.68, 3.55)
    ax.set_ylim(0.08, 1.32)
    ax.set_xticks([1, 2, 3])
    ax.set_yticks([0.2, 0.4, 0.6, 0.8, 1.0, 1.2])
    ax.grid(alpha=0.25)
    ax.legend(loc='lower right', fontsize=9, frameon=True)

    fig.savefig(os.path.join(OUT, 'fig8-1.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('fig8-1 done')


# ============================================================
# 图 8-2 随机梯度下降损失曲线（正文 8.2.1/8.2.2，例8.2 数值演练背景）
# 聚焦：损失快速下降段（前 50 步，x∈[0,50]；y∈[0,0.45] 聚焦收敛带，
#       初始 J0≈0.82 在图外，入图注 d）；锚点 t=2、t=3 均在窗口内
# ============================================================
def fig8_2():
    # ---- 例8.2 四状态链半梯度 TD(0) 在线模拟（数值锚点与正文一致）----
    gamma, alpha = 0.9, 0.1
    vpi = {1: 0.81, 2: 0.90, 3: 1.00}   # 真实价值（s3 一步到终止 r=1, γ=0.9）
    def vhat(i, w):
        return i * w[0] + 1 * w[1]
    def loss(w):
        return float(np.mean([(vpi[i] - vhat(i, w)) ** 2 for i in [1, 2, 3]]))

    seq = [2, 3, 2]                       # 前 3 次访问复现正文
    rng = np.random.default_rng(42)
    for _ in range(197):
        seq.append(int(rng.integers(1, 4)))

    # SGD（半梯度 TD 在线更新）
    w = np.array([0.0, 0.0])
    losses_sgd = [loss(w)]
    for t, s in enumerate(seq):
        target = 1.0 if s == 3 else gamma * vhat(s + 1, w)
        delta = target - vhat(s, w)
        w = w + alpha * delta * np.array([s, 1.0])
        losses_sgd.append(loss(w))
    losses_sgd = losses_sgd[:151]

    # GD（每步遍历全部状态求期望，同一损失函数）
    def grad_full(w):
        return np.mean([-2 * (vpi[i] - vhat(i, w)) * np.array([i, 1.0])
                        for i in [1, 2, 3]], axis=0)
    wg = np.array([0.0, 0.0])
    losses_gd = [loss(wg)]
    for _ in range(150):
        wg = wg - alpha * grad_full(wg)
        losses_gd.append(loss(wg))

    # ---- 绘图 ----
    fig, ax = plt.subplots(figsize=(10.0, 5.3))
    ts = np.arange(len(losses_sgd))
    ax.plot(ts, losses_gd, color='#1f618d', lw=2.8, zorder=3,
            label='逐批调优（遍历全部证候求平均偏差，证候空间大时不可行）')
    ax.plot(ts, losses_sgd, color='#c0392b', lw=1.8, ls='--', zorder=3,
            label='边走边调（单条随访记录、边用边调、走一步改一点）')

    # 例8.2 锚点标注（正文 8.2.2 数值；v̂ 值入图注 c）
    ax.annotate('t=2 访问 s3：误差 = 1\nw <- w + 0.1*1*[3,1]^T = [0.3, 0.1]',
                xy=(2, losses_sgd[2]), xytext=(10, 0.36),
                fontsize=9.5, color='#c0392b', linespacing=1.4,
                arrowprops=dict(arrowstyle='->', color='#c0392b', lw=1.3),
                zorder=5)
    ax.annotate('t=3 再次访问 s2：\n随访修正目标 0.9、偏差 0.2',
                xy=(3, losses_sgd[3]), xytext=(24, 0.22),
                fontsize=9.5, color='#b9770e', linespacing=1.4,
                arrowprops=dict(arrowstyle='->', color='#b9770e', lw=1.3),
                zorder=5)
    ax.annotate('谷底附近：SGD 持续波动（方差）\n小批量（minibatch）折中',
                xy=(48, losses_sgd[-1]), xytext=(20, 0.05),
                fontsize=9.5, color='#7d6608', linespacing=1.4,
                arrowprops=dict(arrowstyle='->', color='#7d6608', lw=1.2),
                zorder=5)

    ax.set_xlabel('迭代次数 t（聚焦损失快速下降段 0-50；每来一条随访经验参数微调一次）',
                  fontsize=11)
    ax.set_ylabel(r'均方误差损失 $J(w)=E[(v_\pi(S)-\hat{v}(S,w))^2]$', fontsize=11)
    ax.set_xlim(-2, 54)
    ax.set_ylim(0, 0.45)
    ax.set_xticks([0, 10, 20, 30, 40, 50])
    ax.set_yticks([0, 0.1, 0.2, 0.3, 0.4])
    ax.grid(alpha=0.25)
    ax.legend(loc='upper right', fontsize=9, frameon=True)

    fig.savefig(os.path.join(OUT, 'fig8-2.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('fig8-2 done')


# ============================================================
# 图 8-3 表格 vs 函数权衡：存储与泛化对比（正文 8.4.1/8.4.2，例8.4 背景）
# 聚焦：（a）loglog 收紧到 10000≈1MB 与 10^10≈1TB 两个锚点之间；
#       （b）四卡泛化对比保留核心判据；删除 suptitle 与底部说明行
# ============================================================
def fig8_3():
    fig, (axL, axR) = plt.subplots(1, 2, figsize=(11.4, 5.4),
                                   gridspec_kw={'width_ratios': [1.05, 1.0]})

    # ---- 左：存储量级 vs 状态数（对数-对数，聚焦锚点区间）----
    n = np.logspace(3, 10, 200)
    storage_table = n * 100.0 / 1e6       # 每条目约 100B → MB
    storage_func = 50 * 8.0 / 1e6 * np.ones_like(n)   # 50 参数 → MB（≈0.4 KB）
    axL.loglog(n, storage_table, color='#2e86c1', lw=2.8, zorder=3,
               label='表格法：存储随状态数线性增长')
    axL.loglog(n, storage_func, color='#b9770e', lw=2.8, zorder=3,
               label='函数法：m=50 参数，恒定不变')
    axL.plot(1e4, 1.0, 'o', color='#c0392b', ms=9, zorder=5)      # 10000 → 1MB
    axL.plot(1e10, 1e6, 'o', color='#c0392b', ms=9, zorder=5)     # 1e10 → 1TB
    axL.annotate('10000 状态 ≈ 1MB\n（可行，一条线）', xy=(1e4, 1.0),
                 xytext=(1.5e4, 2.2), fontsize=9, color='#1e8449',
                 linespacing=1.35,
                 arrowprops=dict(arrowstyle='->', color='#1e8449', lw=1.2))
    axL.annotate('10^10 状态 ≈ 1TB\n且几乎不可能访问完全\n（不可行）',
                 xy=(1e10, 1e6), xytext=(3e8, 1e5), fontsize=9, color='#c0392b',
                 linespacing=1.35,
                 arrowprops=dict(arrowstyle='->', color='#c0392b', lw=1.2))
    axL.text(6e3, 8e-4, '函数法 m=50：约 0.4 KB，恒定', fontsize=9,
             color='#b9770e')
    axL.set_xlabel('状态数 n（对数刻度：症状-舌象-脉象组合数以万计）', fontsize=10.5)
    axL.set_ylabel('存储量级（MB，对数刻度）', fontsize=10.5)
    axL.set_xlim(3e3, 3e10)
    axL.set_ylim(1e-4, 1e7)
    axL.set_xticks([1e4, 1e6, 1e8, 1e10])
    axL.set_yticks([1e-2, 1e0, 1e2, 1e4, 1e6])
    axL.xaxis.set_major_formatter(FuncFormatter(
        lambda v, p: '1e' + str(int(round(np.log10(v))))))
    axL.yaxis.set_major_formatter(FuncFormatter(
        lambda v, p: '1e' + str(int(round(np.log10(v))))))
    axL.legend(loc='upper left', fontsize=8.8, frameon=True)
    axL.text(0.015, 0.965, '(a) 存储量级 vs 状态数', transform=axL.transAxes,
             fontsize=12, fontweight='bold', color='#1b2631', va='top')

    # ---- 右：老状态 / 新状态的泛化对比（例8.4 结论）----
    axR.set_xlim(0, 10)
    axR.set_ylim(0, 10)
    axR.axis('off')
    axR.text(0.015, 0.965, '(b) 泛化：老状态 vs 新状态', transform=axR.transAxes,
             fontsize=12, fontweight='bold', color='#1b2631', va='top')
    box(axR, 0.4, 6.4, 4.6, 2.5, '#d5f5e3', '#1e8449',
        '表格法\n老状态（访问密集）：\n无偏、可逼近真实\n√ 精确',
        fs=10, ls=1.4)
    box(axR, 5.2, 6.4, 4.6, 2.5, '#fdebd0', '#b9770e',
        '函数法（m=50）\n老状态：\n方差小，但可能有逼近误差\n△ 略逊',
        fs=10, ls=1.4)
    box(axR, 0.4, 3.9, 4.6, 2.2, '#fadbd8', '#c0392b',
        '新状态（从未访问）：\n表格法估计为初始值 0\n× 无任何信息',
        fs=10, ls=1.4)
    box(axR, 5.2, 3.9, 4.6, 2.2, '#d5f5e3', '#1e8449',
        '新状态：\n函数法由特征映射给出\n非平凡估计\n√ 有信息、可泛化',
        fs=10, ls=1.4)
    axR.text(5.0, 3.45, '↓  同一组数据，两个判据同时指向两种表示', ha='center',
             fontsize=10, color='#566573')
    box(axR, 0.4, 1.75, 9.4, 1.7, '#eaf2f8', '#1f618d',
        '真实系统是两者的混合：高频状态用记忆保证精确，低频与未见状态用规律保证覆盖\n'
        '——三种混合方案：表格为底 / 函数插值 / 残差结构（个性与泛化各得其所）',
        fs=10, bold=True, ls=1.5)
    axR.text(5.0, 0.65, '选择判据三问：状态空间规模 → 泛化需求 → 精度-鲁棒偏好\n'
                        '医疗决策支持（函数）/ 标准棋类（表格或函数）/ 推荐系统（函数）',
             ha='center', fontsize=9, color='#566573', linespacing=1.4)

    fig.subplots_adjust(wspace=0.22)
    fig.savefig(os.path.join(OUT, 'fig8-3.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('fig8-3 done')


# ============================================================
# 图 8-4 个性化健康推荐示意（正文 8.5.1/8.5.2，例8.5 失眠伴焦虑患者）
# 聚焦：保留完整链路（画像 → 打分 → Top-K → 组合方案）+ 顶部多目标公式；
#       删除 suptitle 与底部说明行，左下旁注并入图注 c
# ============================================================
def fig8_4():
    fig, ax = plt.subplots(figsize=(11.8, 5.9))
    ax.set_xlim(0, 11.8)
    ax.set_ylim(0, 8.0)
    ax.axis('off')

    # 顶部：多目标奖励公式（正文 8.5.1）
    box(ax, 2.7, 6.9, 7.0, 0.95, '#fef9e7', '#b9770e',
        'r_total = w1·r_生理 + w2·r_心理 + w3·r_社会 + w4·r_环境\n'
        '（权重表达价值观取舍，约束划定安全红线）', fs=10.5, bold=True, ls=1.4)

    # 左：患者画像 s（例8.5：失眠伴焦虑患者）
    box(ax, 0.3, 2.2, 2.7, 4.3, '#d6eaf8', '#1f618d',
        '患者画像 s（全要素特征向量）\n\n四诊信息\n体质类型\n既往史\n生活习惯\n'
        '心理状态\n社会支持', fs=9.8, ls=1.55, bold=True)
    ax.text(1.65, 1.95, '例8.5：失眠伴焦虑患者', ha='center', fontsize=9.5,
            color='#c0392b', fontweight='bold')

    # 中：价值近似器
    box(ax, 3.6, 2.9, 3.0, 2.9, '#fdebd0', '#b9770e',
         '疗效预判' + '\n\n为每个候选方案打分\n'
         '（参数来自诊疗-随访数据）',
         fs=10, ls=1.5, bold=True)
    ax.text(5.1, 2.55, '候选多时：先检索缩小候选集\n再计算价值排序（argmax 的工程实现）',
            ha='center', fontsize=8.8, color='#7d6608', linespacing=1.35)

    # 箭头：画像 → 近似器 → Top-K
    ax.annotate('', xy=(3.6, 4.35), xytext=(3.05, 4.35),
                arrowprops=dict(arrowstyle='-|>', color='#1b2631', lw=2.0), zorder=4)
    ax.annotate('', xy=(7.0, 4.35), xytext=(6.65, 4.35),
                arrowprops=dict(arrowstyle='-|>', color='#b9770e', lw=2.2), zorder=4)

    # 右：Top-K 四类动作（四维颜色：生理红/心理蓝/社会绿/环境橙）
    ax.text(8.85, 6.6, 'Top-K 候选（四维全要素）', ha='center', fontsize=11,
            fontweight='bold', color='#1b2631')
    rows = [
        [(7.3, 5.2, 3.1, 1.05, '#fadbd8', '#c0392b', '安神方剂\n（生理）'),
         (10.55, 5.2, 1.6, 1.05, '#fadbd8', '#c0392b', '')],
        [(7.3, 3.95, 2.4, 1.05, '#d6eaf8', '#2e86c1', '情志疏导方案\n（心理）'),
         (10.55, 3.95, 1.6, 1.05, '#d6eaf8', '#2e86c1', '')],
        [(7.3, 2.7, 2.4, 1.05, '#d5f5e3', '#1e8449', '家庭支持计划\n（社会）'),
         (10.55, 2.7, 1.6, 1.05, '#d5f5e3', '#1e8449', '')],
        [(7.3, 1.45, 2.4, 1.05, '#fdebd0', '#b9770e', '作息节律调整\n（环境）'),
         (10.55, 1.45, 1.6, 1.05, '#fdebd0', '#b9770e', '')],
    ]
    for row in rows:
        for (x, y, w, h, fc, ec, txt) in row:
            box(ax, x, y, w, h, fc, ec, txt, fs=9.3, ls=1.35, bold=True)
    ax.text(12.05, 5.72, '生理', ha='center', fontsize=9, color='#c0392b')
    ax.text(12.05, 4.47, '心理', ha='center', fontsize=9, color='#2e86c1')
    ax.text(12.05, 3.22, '社会', ha='center', fontsize=9, color='#1e8449')
    ax.text(12.05, 1.97, '环境', ha='center', fontsize=9, color='#b9770e')

    # 右箭头 → 组合方案
    ax.annotate('', xy=(9.1, 0.85), xytext=(9.1, 1.30),
                arrowprops=dict(arrowstyle='-|>', color='#1e8449', lw=2.0), zorder=4)
    box(ax, 5.4, 0.15, 7.0, 0.85, '#e8f8f5', '#1e8449',
        '组合方案输出：方剂 + 调护 + 随访计划（关怀输出一套生活）',
        fs=10.5, bold=True, ls=1.35)

    fig.savefig(os.path.join(OUT, 'fig8-4.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('fig8-4 done')


if __name__ == '__main__':
    fig8_1()
    fig8_2()
    fig8_3()
    fig8_4()
    print('ALL DONE ->', OUT)
