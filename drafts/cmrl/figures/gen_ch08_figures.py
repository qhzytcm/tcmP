# -*- coding: utf-8 -*-
"""《中医场景强化学习》第8章 核心图生成脚本（图表工程师批次：图 8-1 ~ 图 8-4）

生成：fig8-1 函数近似拟合曲线（特征 φ(s) 线性拟合价值 v̂=φᵀw，散点+拟合线）
      fig8-2 随机梯度下降损失曲线（迭代 vs 损失：梯度下降 vs SGD，收敛）
      fig8-3 表格 vs 函数权衡（状态数 vs 存储量级 / 老新状态泛化对比）
      fig8-4 个性化健康推荐示意（患者画像 → 价值打分 → Top-K 全要素方案）
输出：drafts/cmrl/figures/ch08/*.png
范式：与 figures/gen_ch07_figures.py 一致 —— SimHei / unicode_minus=False /
      Agg / dpi=200 / bbox_inches='tight' / 图题入图（ax.set_title / fig.suptitle）
字体约定：数学符号用 mathtext（$\\hat{v}$、$\\varphi^\\top$、$^2$），避免 SimHei
      缺失字形（U+0302 组合抑扬符、U+1D40、U+226A、U+2212、U+2713 等）。
数值一致性（与正文 8.1-8.5 节逐项核对）：
  - 例8.1/8.1.2：φ(s)=[s,1]ᵀ，w=[a,b]ᵀ，v̂(s)=as+b，仅 2 个参数
  - 例8.2/8.2.2：4 状态链 γ=0.9、α=0.1、w₀=[0,0]；首次访问 s3 误差 1 → w=[0.3,0.1]；
    v̂(s1)=0.4、v̂(s2)=0.7、v̂(s3)=1.0；再次访问 s2：TD 目标 0.9、误差 0.2
  - 8.2.1：MSE 目标 J(w)、Robbins-Monro 条件 Σαt=∞ 且 Σαt²<∞、小批量折中方差
  - 8.4.1：10000 状态≈1MB、10^10 状态≈1TB（每条目约 100B）
  - 例8.4/8.4.2：状态 10000、每状态访问 100 次、函数法 m=50 参数、老状态表格更准/新状态函数更可靠
  - 8.5.1/8.5.2：r_total=w1·r_生理+w2·r_心理+w3·r_社会+w4·r_环境；例8.5 失眠伴焦虑患者
    四类动作：安神方剂（生理）/情志疏导（心理）/家庭支持（社会）/作息节律（环境）
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
# 图 8-1 函数近似拟合曲线（正文 8.1.2，例8.1 直线拟合 + 例8.2 参数）
# ============================================================
def fig8_1():
    fig, ax = plt.subplots(figsize=(10.4, 6.7))
    s_all = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    # 真实价值点：围绕拟合线 0.3s+0.1 小幅波动（教学示意，锚点与例8.2 一致）
    v_true = np.array([0.35, 0.75, 0.95, 1.35, 1.55])
    s_fit = np.linspace(0.6, 5.4, 100)
    v_fit = 0.3 * s_fit + 0.1

    ax.axhline(0, color='#b3b6b7', lw=0.8, zorder=0)
    ax.axvline(0, color='#b3b6b7', lw=0.8, zorder=0)
    # 残差竖线
    for s, v in zip(s_all, v_true):
        ax.plot([s, s], [v, 0.3 * s + 0.1], color='#e67e22', lw=1.1,
                ls=':', zorder=1)
    # 真实价值散点
    ax.scatter(s_all, v_true, s=58, color='#7f8c8d', zorder=3,
               label='真实价值 vπ(s)（数据点）')
    # 拟合直线
    ax.plot(s_fit, v_fit, color='#1f618d', lw=2.6, zorder=4,
            label=r'线性近似 $\hat{v}(s) = \varphi^\top w$ = 0.3s + 0.1')
    # 例8.2 锚点（正文 8.2.2 数值，与 check_ch08.py 验算一致）
    for s, v in [(1, 0.4), (2, 0.7), (3, 1.0)]:
        ax.plot(s, v, 'o', color='#c0392b', ms=7, zorder=5)
        ax.annotate(rf'$\hat{{v}}$(s{s})={v}', xy=(s, v),
                    xytext=(s + 0.16, v + 0.07),
                    fontsize=10.5, color='#c0392b', zorder=5)
    ax.annotate('', xy=(3.0, 1.0), xytext=(3.0, 0.95),
                arrowprops=dict(arrowstyle='->', color='#c0392b', lw=1.3))

    ax.text(0.75, 1.62, 'w = [a, b]^T = [0.3, 0.1]（与例8.2 相同）',
            fontsize=10.5, color='#1f618d', fontweight='bold')
    ax.text(0.75, 1.42, '特征 φ(s) = [s, 1]^T：把状态翻译成数值描述',
            fontsize=10.5, color='#1f618d')
    ax.text(0.75, 0.18, 'm = 2 << n：仅 2 个参数表示任意多状态\n'
                        '——参数共享带来泛化（牵一发而动全身）',
            fontsize=10, color='#566573', linespacing=1.4)
    ax.text(4.15, 1.78, r'残差 = vπ - $\hat{v}$' + '\n（近似误差）', ha='center',
            fontsize=9.5, color='#e67e22', linespacing=1.35)

    ax.set_xlabel('证候 s（如证候量化值：舌象、脉象、症状组合）', fontsize=11)
    ax.set_ylabel('疗效把握 ' + r'$\hat{v}$' + '(s, w)', fontsize=11)
    ax.set_xlim(0.4, 5.6)
    ax.set_ylim(-0.05, 1.95)
    ax.set_xticks([1, 2, 3, 4, 5])
    ax.legend(loc='lower right', fontsize=10, frameon=True)
    ax.set_title('图8-1 函数近似：用一条直线拟合千万个状态的价值——'
                 r'$\hat{v}(s) = \varphi^\top w$' + '\n'
                 '线性近似是关于参数 w 的线性，特征 φ(s) 本身可以是非线性（正文 8.1.2）',
                 fontsize=13, pad=10)
    fig.text(0.5, 0.015,
             '特征的本质是相似性的度量：特征接近的状态应有接近的价值——'
             '表格法记录每一个状态，函数法提炼整条规律（正文 8.1.2）',
             ha='center', fontsize=9.5, color='#566573')
    fig.subplots_adjust(bottom=0.13)
    fig.savefig(os.path.join(OUT, 'fig8-1.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('fig8-1 done')


# ============================================================
# 图 8-2 随机梯度下降损失曲线（正文 8.2.1/8.2.2，例8.2 数值演练背景）
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
    losses_sgd = losses_sgd[:151]           # 画 150 步足够展示收敛

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
    fig, ax = plt.subplots(figsize=(10.8, 6.8))
    ts = np.arange(len(losses_sgd))
    ax.plot(ts, losses_gd, color='#1f618d', lw=2.6, zorder=3,
            label='逐批调优（遍历全部证候求平均偏差，证候空间大时不可行）')
    ax.plot(ts, losses_sgd, color='#c0392b', lw=1.7, ls='--', zorder=3,
            label='边走边调（单条随访记录、边用边调、走一步改一点）')

    # 例8.2 锚点标注（正文 8.2.2 数值）
    ax.annotate('t=2 访问 s3：误差 = 1\n'
                'w <- w + 0.1x1x[3,1]^T = [0.3, 0.1]\n'
                r'$\hat{v}$(s1)=0.4  $\hat{v}$(s2)=0.7  $\hat{v}$(s3)=1.0',
                xy=(2, losses_sgd[2]), xytext=(26, 0.42),
                fontsize=10, color='#c0392b', linespacing=1.4,
                arrowprops=dict(arrowstyle='->', color='#c0392b', lw=1.3))
    ax.annotate('t=3 再次访问 s2：\n随访修正目标 0.9、偏差 0.2',
                xy=(3, losses_sgd[3]), xytext=(44, 0.24),
                fontsize=10, color='#b9770e', linespacing=1.4,
                arrowprops=dict(arrowstyle='->', color='#b9770e', lw=1.3))
    ax.annotate('谷底附近：SGD 持续波动（方差）\n'
                '小批量（minibatch）在方差与计算之间折中',
                xy=(140, losses_sgd[-1]), xytext=(66, 0.09),
                fontsize=9.5, color='#7d6608', linespacing=1.4,
                arrowprops=dict(arrowstyle='->', color='#7d6608', lw=1.2))

    ax.set_xlabel('迭代次数 t（每来一条随访经验，参数就微调一次——在线学习）', fontsize=11)
    ax.set_ylabel(r'均方误差损失 J(w) = E[(vπ(S) - $\hat{v}$(S,w))$^2$]',
                  fontsize=11)
    ax.set_xlim(0, 150)
    ax.set_ylim(0, 0.90)
    ax.legend(loc='upper right', fontsize=9.5, frameon=True)
    ax.set_title('图8-2 随机梯度下降：边用边调，损失随迭代收敛（例8.2 数值演练背景）\n'
                 '单样本梯度无偏但有噪声：方向大体正确，走足够久便能抵达谷底（正文 8.2.1）',
                 fontsize=13, pad=10)
    fig.text(0.5, 0.015,
             r'步长满足 Robbins-Monro 条件（Σαt=∞ 且 Σαt$^2$<∞，如 αt=1/t）时，'
             '线性近似的 SGD 以概率 1 收敛到 w*——w* 是真实价值在特征空间上的正交投影'
             '（正文 8.2.1、8.2.2）',
             ha='center', fontsize=9.5, color='#566573')
    fig.subplots_adjust(bottom=0.13)
    fig.savefig(os.path.join(OUT, 'fig8-2.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('fig8-2 done')


# ============================================================
# 图 8-3 表格 vs 函数权衡：存储与泛化对比（正文 8.4.1/8.4.2，例8.4 背景）
# ============================================================
def fig8_3():
    fig, (axL, axR) = plt.subplots(1, 2, figsize=(11.8, 6.6),
                                   gridspec_kw={'width_ratios': [1.05, 1.0]})

    # ---- 左：存储量级 vs 状态数（对数-对数）----
    n = np.logspace(2, 10, 200)
    storage_table = n * 100.0 / 1e6       # 每条目约 100B → MB
    storage_func = 50 * 8.0 / 1e6 * np.ones_like(n)   # 50 参数 → MB
    axL.loglog(n, storage_table, color='#2e86c1', lw=2.6, zorder=3,
               label='表格法：存储随状态数线性增长')
    axL.loglog(n, storage_func, color='#b9770e', lw=2.6, zorder=3,
               label='函数法：50 个参数，恒定不变')
    axL.plot(1e4, 1.0, 'o', color='#c0392b', ms=8, zorder=5)      # 10000 → 1MB
    axL.plot(1e10, 1e6, 'o', color='#c0392b', ms=8, zorder=5)     # 1e10 → 1TB
    axL.annotate('10000 状态 ≈ 1MB\n（可行，一条线）', xy=(1e4, 1.0),
                 xytext=(1e4 * 1.5, 2.2), fontsize=9.5, color='#1e8449',
                 linespacing=1.35,
                 arrowprops=dict(arrowstyle='->', color='#1e8449', lw=1.2))
    axL.annotate('10^10 状态 ≈ 1TB\n且几乎不可能访问完全\n（不可行）',
                 xy=(1e10, 1e6), xytext=(2e8, 1e5), fontsize=9.5, color='#c0392b',
                 linespacing=1.35,
                 arrowprops=dict(arrowstyle='->', color='#c0392b', lw=1.2))
    axL.text(2.2e3, 3e-3, 'm = 50 << n\n参数共享 → 可扩展', fontsize=9.5,
             color='#b9770e', linespacing=1.4)
    axL.set_xlabel('状态数 n（对数刻度：症状-舌象-脉象组合数以万计）', fontsize=10.5)
    axL.set_ylabel('存储量级（MB，对数刻度）', fontsize=10.5)
    axL.set_xlim(1e2, 1e11)
    axL.set_ylim(1e-4, 1e7)
    # 刻度用 ASCII 格式（1e-4 等），避免 mathtext 负号字形问题
    axL.xaxis.set_major_formatter(FuncFormatter(
        lambda v, p: '1e' + str(int(round(np.log10(v))))))
    axL.yaxis.set_major_formatter(FuncFormatter(
        lambda v, p: '1e' + str(int(round(np.log10(v))))))
    axL.legend(loc='upper left', fontsize=9, frameon=True)
    axL.set_title('（a）存储：一条直线 vs 一条水平线\n'
                  '表格法跨过某条线后从可行直接跳入不可行',
                  fontsize=11.5, pad=8)

    # ---- 右：老状态 / 新状态的泛化对比（例8.4 结论）----
    axR.set_xlim(0, 10)
    axR.set_ylim(0, 10)
    axR.axis('off')
    axR.set_title('（b）泛化：老状态表格更准，新状态函数更可靠\n'
                  '（例8.4：10000 状态、每状态访问 100 次、函数 m=50）',
                  fontsize=11.5, pad=8)
    # 第一行两卡：表格法（左列）与函数法（右列）
    box(axR, 0.4, 7.0, 4.6, 2.5, '#d5f5e3', '#1e8449',
        '表格法\n老状态（访问密集）：\n无偏、可逼近真实\n√ 精确',
        fs=10, ls=1.4)
    box(axR, 5.2, 7.0, 4.6, 2.5, '#fdebd0', '#b9770e',
        '函数法（m=50）\n老状态：\n方差小，但可能有逼近误差\n△ 略逊',
        fs=10, ls=1.4)
    # 第二行：新状态对比
    box(axR, 0.4, 4.35, 4.6, 2.2, '#fadbd8', '#c0392b',
        '新状态（从未访问）：\n表格法估计为初始值 0\n× 无任何信息',
        fs=10, ls=1.4)
    box(axR, 5.2, 4.35, 4.6, 2.2, '#d5f5e3', '#1e8449',
        '新状态：\n函数法由特征映射给出\n非平凡估计\n√ 有信息、可泛化',
        fs=10, ls=1.4)
    axR.text(5.0, 3.9, '↓  同一组数据，两个判据同时指向两种表示', ha='center',
             fontsize=10, color='#566573')
    box(axR, 0.4, 2.1, 9.4, 1.7, '#eaf2f8', '#1f618d',
        '真实系统是两者的混合：高频状态用记忆保证精确，低频与未见状态用规律保证覆盖\n'
        '——三种混合方案：表格为底 / 函数插值 / 残差结构（个性与泛化各得其所）',
        fs=10.5, bold=True, ls=1.5)
    axR.text(5.0, 0.95, '选择判据三问：状态空间规模 → 泛化需求 → 精度-鲁棒偏好\n'
                        '医疗决策支持（函数）/ 标准棋类（表格或函数）/ 推荐系统（函数）',
             ha='center', fontsize=9.5, color='#566573', linespacing=1.4)

    fig.suptitle('图8-3 记忆还是规律：表格与函数的权衡——存储与泛化的对比（正文 8.4）',
                 fontsize=13.5, y=0.995)
    fig.text(0.5, 0.012,
             '表格保存的是每一个状态的个性，函数提炼的是跨状态的共性；'
             '个性越精细需要的记忆越多，共性越概括覆盖的范围越广（正文 8.4.1）',
             ha='center', fontsize=9.5, color='#566573')
    fig.subplots_adjust(top=0.86, bottom=0.12, wspace=0.18)
    fig.savefig(os.path.join(OUT, 'fig8-3.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('fig8-3 done')


# ============================================================
# 图 8-4 个性化健康推荐示意（正文 8.5.1/8.5.2，例8.5 失眠伴焦虑患者）
# ============================================================
def fig8_4():
    fig, ax = plt.subplots(figsize=(12.4, 7.0))
    ax.set_xlim(0, 12.4)
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

    # 底部：推荐 vs 关怀
    ax.text(0.3, 0.30, '推荐关心当下给什么：\n哪首方剂、哪项检查、\n哪种调养最适合当前状态',
            ha='left', fontsize=9, color='#566573', linespacing=1.4)

    fig.suptitle('图8-4 从推荐到关怀：患者画像 → 价值打分 → Top-K 全要素方案（正文 8.5）\n'
                 '推荐输出一个物品，关怀输出一套生活——全要素健康服务的实现路径'
                 '（个性化画像 / 长期闭环 / 多目标加权 / 扩展动作空间）',
                 fontsize=13, y=0.985)
    fig.text(0.5, 0.02,
             '如果复诊好转，修正量为正，疗效把握强化该证-方关联；如果转归恶化，修正量为负，'
             '参数向降低该方案价值的方向调整——效不更方、效则守方的算法形态（正文 8.5.2）',
             ha='center', fontsize=9.5, color='#566573')
    fig.subplots_adjust(top=0.84, bottom=0.08)
    fig.savefig(os.path.join(OUT, 'fig8-4.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('fig8-4 done')


if __name__ == '__main__':
    fig8_1()
    fig8_2()
    fig8_3()
    fig8_4()
    print('ALL DONE ->', OUT)
