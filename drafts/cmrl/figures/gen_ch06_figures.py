# -*- coding: utf-8 -*-
"""《中医场景强化学习》第6章 核心图生成脚本
生成：fig6-1 时序差分一步修正示意 / fig6-2 TD(0) 价值学习曲线（例6.1）
      fig6-3 Q学习法示意（Q表+max更新路径，例6.4）/ fig6-4 在线学习进化闭环
输出：drafts/cmrl/figures/ch06/*.png
风格：与 gen_ch01_figures.py 一致（SimHei / unicode_minus=False / dpi=200）
数值：与正文 6.1-6.8 节及习题集完全一致
      （例6.1：γ=0.9, α=0.1；回合1后(0,0,0,0.1)，回合2后(0,0,0.009,0.19)，
       第三回合 s3 TD目标=0.171，v(s3)=0.0252，回合3后(0,0.00081,0.0252,0.271)；
       例6.4：q(s1,左)=-0.1, q(s1,右)=0.01, q(s2,左)=0, q(s2,右)=0.1, max=0.1）
"""
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle, Patch
from matplotlib.lines import Line2D

plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ch06')
os.makedirs(OUT, exist_ok=True)

# ---- 第1章同款配色 ----
C_BLUE_F, C_BLUE_E = '#d6eaf8', '#1f618d'
C_GREEN_F, C_GREEN_E = '#d5f5e3', '#1e8449'
C_ORANGE_F, C_ORANGE_E = '#fdebd0', '#b9770e'
C_YELLOW_F, C_YELLOW_E = '#fef9e7', '#b7950b'
C_GRAY_F, C_GRAY_E = '#f2f3f4', '#7f8c8d'
C_RED_F, C_RED_E = '#fadbd8', '#c0392b'


def box(ax, x, y, w, h, fc, ec, txt, fs=10, lw=1.6, tc='#1b2631',
        boxstyle='round,pad=0.08', linespacing=1.5, bold=False):
    """圆角框 + 居中文本（第1章 fig1-2 风格）"""
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=boxstyle,
                                facecolor=fc, edgecolor=ec, lw=lw, zorder=3))
    ax.text(x + w / 2, y + h / 2, txt, ha='center', va='center',
            fontsize=fs, color=tc, zorder=4, linespacing=linespacing,
            fontweight=('bold' if bold else 'normal'))


def arrow(ax, x1, y1, x2, y2, color='#1b2631', lw=2.0, ls='-', style='-|>',
          rad=0.0, zorder=3, shrinkA=0, shrinkB=0):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2),
                                 arrowstyle=style, color=color, lw=lw,
                                 linestyle=ls, connectionstyle=f'arc3,rad={rad}',
                                 mutation_scale=14, zorder=zorder,
                                 shrinkA=shrinkA, shrinkB=shrinkB))


# ======================================================================
# 图 6-1 走一步看一步：TD 的学习目标与自我修正（6.1.1）
# ======================================================================
def fig6_1():
    fig, ax = plt.subplots(figsize=(12.6, 7.0))
    ax.set_xlim(-0.3, 12.9)
    ax.set_ylim(-0.5, 7.2)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title('图 6-1 走一步看一步：TD 的学习目标与自我修正\n'
                 '初诊判断是"老账"，复诊看到一步真实反馈与后继预判，得到"新账"——'
                 '用新账修订老账，就是自举（bootstrapping）',
                 fontsize=12, pad=14)

    # ---- 左区：老账 / 新账 ----
    box(ax, 0.2, 3.6, 2.9, 2.3, C_BLUE_F, C_BLUE_E,
        '老账 v(St)\n初诊时的判断\n\n"我对当前证候\n长期前景的估计"',
        fs=10.5, bold=False)
    box(ax, 4.0, 3.6, 2.9, 2.3, C_GREEN_F, C_GREEN_E,
        '新账 Rt+1 + γv(St+1)\n复诊看到一步真实反馈\n结合对后继证候的预判\n\n'
        '比老账多了一天的观察，\n自然更可信', fs=10.5)
    arrow(ax, 3.1, 4.75, 4.0, 4.75, color='#1f618d', lw=2.4)
    ax.text(3.55, 5.10, '复诊\n看一步', ha='center', fontsize=9,
            color='#1f618d')
    arrow(ax, 3.55, 3.6, 3.55, 3.3, color='#1b2631', lw=1.6)
    ax.text(3.55, 3.02, '新账 - 老账 = δt', ha='center', fontsize=9.5,
            color='#1b2631', fontweight='bold')

    # ---- 左区底部：TD 误差框 ----
    box(ax, 0.2, 0.55, 6.7, 1.9, C_YELLOW_F, C_YELLOW_E,
        'TD 误差（TD error）：δt = v(St) - (Rt+1 + γv(St+1)) = v(St) - TD目标\n\n'
        'δt > 0 → 估计偏高，往下调　·　δt < 0 → 估计偏低，往上调　·　δt = 0 → 无需修正\n'
        '（等价写法：δt 也可写成方括号 [Rt+1 + γv(St+1) - v(St)] 的形式）',
        fs=9.6)

    # ---- 右区：更新链条（两行）----
    ax.text(8.2, 6.35, '更新链条：把"经验"翻译成"修正量"', ha='center',
            fontsize=10.5, color='#1b2631', fontweight='bold')
    chain = [
        (7.1, 5.5, C_BLUE_F, C_BLUE_E, '旧估计\nv(St)'),
        (9.1, 5.5, C_GREEN_F, C_GREEN_E, 'TD目标\nRt+1 + γv(St+1)'),
        (11.1, 5.5, C_ORANGE_F, C_ORANGE_E, 'TD误差 δt\n= 目标 - 旧估计'),
    ]
    for k, (x, y, fc, ec, txt) in enumerate(chain):
        box(ax, x, y, 1.5, 1.0, fc, ec, txt, fs=9.3, lw=1.8)
        if k < 2:
            arrow(ax, x + 1.5, y + 0.5, x + 1.78, y + 0.5,
                  color='#1b2631', lw=2.0)
    box(ax, 7.1, 3.9, 2.0, 1.0, C_YELLOW_F, C_YELLOW_E,
        '修正方向\n由 δt 符号自动给出', fs=9.3)
    box(ax, 9.6, 3.9, 2.0, 1.0, C_GREEN_F, C_GREEN_E,
        '新估计\nv(St) ← v(St) + α·δt', fs=9.3)
    arrow(ax, 7.85, 5.5, 7.85, 5.02, color='#1b2631', lw=1.8)
    arrow(ax, 10.6, 5.5, 10.6, 5.02, color='#1b2631', lw=1.8)
    arrow(ax, 9.1, 4.9, 9.6, 4.9, color='#1b2631', lw=2.0)
    ax.text(9.35, 5.15, 'α：修正幅度', ha='center', fontsize=8.6,
            color='#7d6608')

    # ---- 右区底部：更新式大框 ----
    box(ax, 7.1, 0.55, 5.6, 1.9, C_GREEN_F, C_GREEN_E,
        '更新式：v(St) ← v(St) + α[Rt+1 + γv(St+1) - v(St)]\n\n'
        'TD目标（TD target）· TD误差（TD error）· 自举（bootstrapping）\n'
        '用自己当前的估计改进自己',
        fs=9.8)

    # ---- 右上：节奏对比框 ----
    box(ax, 7.1, 2.35, 5.6, 1.25, C_GRAY_F, C_GRAY_E,
        '学习节奏对比\n统计估计法：必须等回合结束，整段回报一次修正　·　'
        'TD：每走一步就更新，边走边修正', fs=9.3, lw=1.4)
    arrow(ax, 10.6, 2.35, 10.6, 2.15, color='#566573', lw=1.4)
    ax.text(10.6, 2.0, '对比见 6.1.2 随机游走实验', ha='center', fontsize=8.2,
            color='#566573')

    fig.savefig(os.path.join(OUT, 'fig6-1.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('fig6-1 done')


# ======================================================================
# 图 6-2 TD(0) 价值学习曲线：四状态链的收敛过程（6.2.2 例6.1）
# ======================================================================
def fig6_2():
    gamma, alpha = 0.9, 0.1
    true_v = [0.729, 0.81, 0.9, 1.0]          # s1..s4 真实价值
    v = [0.0, 0.0, 0.0, 0.0]
    N = 60
    hist = []                                  # hist[r] = 第 r 回合结束后的 v（r 从1起）
    for ep in range(1, N + 1):
        start = 1 if ep == 1 else 0            # 回合1 轨迹 s2→s3→s4；其余 s1→s2→s3→s4
        for s in range(start, 4):
            r = 1.0 if s == 3 else 0.0         # 到达 s4 奖励 1 终止
            v_next = 0.0 if s == 3 else v[s + 1]
            target = r + gamma * v_next
            v[s] += alpha * (target - v[s])
        hist.append(list(v))

    # 关键数值核对（与正文/习题集一致）
    assert abs(hist[0][3] - 0.1) < 1e-9, hist[0]
    assert abs(hist[1][2] - 0.009) < 1e-9, hist[1]
    assert abs(hist[1][3] - 0.19) < 1e-9, hist[1]
    assert abs(hist[2][1] - 0.00081) < 1e-9, hist[2]
    assert abs(hist[2][2] - 0.0252) < 1e-9, hist[2]
    assert abs(hist[2][3] - 0.271) < 1e-9, hist[2]
    # 第三回合访问 s3 的 TD 目标 = 0.171
    target_s3 = 0.9 * hist[1][3]              # 0.9 × 0.19 = 0.171

    fig, ax = plt.subplots(figsize=(10.6, 6.6))
    xs = list(range(1, N + 1))
    colors = ['#2e86c1', '#1e8449', '#b9770e', '#c0392b']
    labels = ['v(s1)', 'v(s2)', 'v(s3)', 'v(s4)']
    for i in range(4):
        ax.plot(xs, [h[i] for h in hist], color=colors[i], lw=2.2,
                label=f'{labels[i]}（估计值）')
        ax.axhline(true_v[i], color=colors[i], lw=1.1, ls='--', alpha=0.55)
        ax.text(N + 1.2, true_v[i], f'{true_v[i]:.3f}', fontsize=8.6,
                color=colors[i], va='center')
    # 真实值标注
    ax.text(N + 1.2, 0.02, '虚线 = 真实价值', fontsize=8.6, color='#566573')

    # 关键点标注（回合1/2/3 手算结果）
    marks = [
        (1, 0, 0.1, '回合1后 v(s4)=0.1', 'center'),
        (2, 2, 0.009, '回合2后 v(s3)=0.009', 'top'),
        (2, 3, 0.19, '回合2后 v(s4)=0.19', 'top'),
        (3, 1, 0.00081, '回合3后 v(s2)=0.00081', 'bottom'),
        (3, 2, 0.0252, f'回合3：TD目标={target_s3:.3f}，\nv(s3)=0.0252', 'top'),
        (3, 3, 0.271, '回合3后 v(s4)=0.271', 'top'),
    ]
    for (ep, i, val, txt, va) in marks:
        ax.plot(ep, val, 'o', color=colors[i], ms=7, zorder=5)
        ax.annotate(txt, xy=(ep, val), xytext=(ep + 3.2, val + (0.16 if i < 3 else 0.0)),
                    fontsize=8.4, color=colors[i],
                    arrowprops=dict(arrowstyle='-', color=colors[i], lw=1.0),
                    va=va)
    # 信息回传弧线（s4 奖励 → 回合2 s3、回合3 s2）
    ax.annotate('', xy=(2, 0.009), xytext=(1, 0.1),
                arrowprops=dict(arrowstyle='-|>', color='#b9770e', lw=1.6,
                                connectionstyle='arc3,rad=-0.45'), zorder=4)
    ax.annotate('', xy=(3, 0.00081), xytext=(2, 0.009),
                arrowprops=dict(arrowstyle='-|>', color='#b9770e', lw=1.6,
                                connectionstyle='arc3,rad=-0.45'), zorder=4)
    ax.text(1.55, 0.028, '奖励信息逐格回传\n（每回合最多一格）', fontsize=8.4,
            color='#b9770e')

    ax.set_xlabel('回合（episode）', fontsize=11)
    ax.set_ylabel('状态价值估计 v(s)', fontsize=11)
    ax.set_xlim(0, N + 8)
    ax.set_ylim(-0.05, 1.12)
    ax.set_xticks([1, 2, 3, 10, 20, 30, 40, 50, 60])
    ax.grid(alpha=0.3, ls=':')
    ax.legend(loc='lower right', fontsize=9.3, frameon=True)
    ax.set_title('图 6-2 TD(0) 价值学习曲线：四状态链的收敛过程\n'
                 '例 6.1：γ=0.9，α=0.1，初始全 0；曲线为 60 回合模拟，'
                 '虚线为真实价值 v(s4)=1, v(s3)=0.9, v(s2)=0.81, v(s1)=0.729',
                 fontsize=11.5, pad=12)
    fig.text(0.5, 0.012,
             '更新式 v(St) ← v(St) + α[Rt+1 + γv(St+1) - v(St)]：'
             '第 1 回合奖励信息到达 s4（v(s4)=0.1），第 2 回合传到 s3（目标 0.9×0.1=0.09），'
             '第 3 回合 s3 的目标为 0.9×0.19=0.171，得 v(s3)=0.0252 —— 每步更新最多回传一格',
             ha='center', fontsize=8.8, color='#566573')
    fig.subplots_adjust(bottom=0.13, top=0.88)
    fig.savefig(os.path.join(OUT, 'fig6-2.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('fig6-2 done')


# ======================================================================
# 图 6-3 Q 学习法示意：Q 表与 max 更新路径（6.5.3 例6.4）
# ======================================================================
def fig6_3():
    fig, ax = plt.subplots(figsize=(12.8, 7.0))
    ax.set_xlim(-0.4, 13.2)
    ax.set_ylim(-0.6, 7.4)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title('图 6-3 Q 学习法示意：向最优方案学习（Q 表与 max 更新路径）\n'
                 '例 6.4 数据 4：s1 选"右"到 s2（奖励 0）；Q 学习法用 max{0, 0.1}=0.1 作目标，'
                 '更新 q(s1,右)；与行为策略在 s2 的实际选择无关',
                 fontsize=11.5, pad=14)

    # ---- 左区：Q 表 ----
    ax.text(2.0, 6.6, 'Q 表：状态 × 动作（更新前/后的关键条目）', ha='center',
            fontsize=10.5, fontweight='bold', color='#1b2631')
    cell_w, cell_h, x0, y0 = 1.9, 1.15, 0.5, 4.1
    header = ['', '动作"左"', '动作"右"']
    rows = [['s1', '-0.1', '0.01'], ['s2', '0（假设值）', '0.1']]
    # 表头
    for j, t in enumerate(header):
        fc = C_BLUE_F if j == 0 else '#eaf2f8'
        box(ax, x0 + j * cell_w, y0 + 2 * cell_h + 0.25, cell_w, 0.8, fc,
            '#5d6d7e', t, fs=10.5, lw=1.4)
    for i in range(2):
        for j in range(3):
            fc, ec, lw = 'white', '#999999', 1.2
            if i == 0 and j == 2:      # q(s1,右)：本次更新格，绿色粗框
                fc, ec, lw = C_GREEN_F, '#1e8449', 2.6
            if i == 1 and j == 2:      # q(s2,右)=0.1：max 源，绿色底
                fc, ec = '#a9dfbf', '#1e8449'
            txt = rows[i][j]
            if i == 0 and j == 2:
                txt = '0.01 ← 更新后'
            box(ax, x0 + j * cell_w, y0 + (1 - i) * cell_h, cell_w, cell_h,
                fc, ec, txt, fs=10.0, lw=lw)
    ax.text(x0 + 0.95, y0 + 0.35, '行 = 状态（证候），列 = 动作（方剂）',
            ha='center', fontsize=8.6, color='#566573')
    # 更新格说明箭头
    ax.annotate('本次更新格\nq(s1,右)=0.01', xy=(x0 + 2 * cell_w + 0.02, y0 + 1 * cell_h + 0.02),
                xytext=(x0 + 3 * cell_w + 1.3, y0 + 1.55 * cell_h),
                fontsize=8.8, color='#1e8449',
                arrowprops=dict(arrowstyle='-|>', color='#1e8449', lw=1.6))
    ax.annotate('max 源\ntarget = max{0, 0.1} = 0.1', xy=(x0 + 2 * cell_w + 0.02, y0 + 0.02),
                xytext=(x0 + 3 * cell_w + 1.3, y0 - 0.3 * cell_h),
                fontsize=8.8, color='#1e8449',
                arrowprops=dict(arrowstyle='-|>', color='#1e8449', lw=1.6))

    # ---- 中区：更新式对比 ----
    ax.text(7.0, 6.6, '唯一差别：后继项', ha='center', fontsize=10.5,
            fontweight='bold', color='#1b2631')
    box(ax, 4.9, 5.15, 4.3, 1.15, C_GREEN_F, '#1e8449',
        'Q 学习法：q(St,At) ← q(St,At)\n+ α[Rt+1 + γ·max_a′ q(St+1,a′) - q(St,At)]',
        fs=8.9, lw=2.0)
    box(ax, 4.9, 3.75, 4.3, 1.15, C_ORANGE_F, '#b9770e',
        'Sarsa：q(St,At) ← q(St,At)\n+ α[Rt+1 + γ·q(St+1,At+1) - q(St,At)]',
        fs=8.9, lw=1.6)
    ax.text(9.3, 5.7, 'max_a′\n（最优动作）', fontsize=9, color='#1e8449', ha='center')
    ax.text(9.3, 4.32, 'At+1\n（实际动作）', fontsize=9, color='#a04000', ha='center')
    ax.text(4.9 + 2.15, 3.35, 'Q 学习法：目标与行为分离（异策略 off-policy）',
            ha='center', fontsize=9.2, color='#1e8449')

    # ---- 右区：数据 4 更新路径 ----
    ax.text(11.2, 6.6, '数据 4 的更新路径', ha='center', fontsize=10.5,
            fontweight='bold', color='#1b2631')
    box(ax, 9.8, 5.15, 2.6, 1.0, C_BLUE_F, C_BLUE_E,
        '(s1, 右)\nq = 0（更新前）', fs=9.2)
    box(ax, 9.8, 3.75, 2.6, 1.0, '#eaf2f8', '#5d6d7e',
        '执行"右"\n奖励 r = 0\n到达 s2', fs=9.0)
    arrow(ax, 11.1, 5.15, 11.1, 4.78, color='#1b2631', lw=1.8)
    # 分支 1：Q 学习法 max 路径（绿实线）
    box(ax, 9.8, 2.35, 2.6, 1.0, '#a9dfbf', '#1e8449',
        'max{0, 0.1} = 0.1\nq(s1,右)=0+0.1×(0.1-0)\n= 0.01', fs=8.8, lw=2.2)
    arrow(ax, 11.1, 3.75, 11.1, 3.38, color='#1e8449', lw=2.4)
    ax.text(11.35, 3.55, 'Q 学习法（绿）：\n与 s2 处实际动作无关', fontsize=8.2,
            color='#1e8449', ha='left')
    # 分支 2：Sarsa 实际路径（灰虚线）
    box(ax, 6.4, 0.55, 3.0, 1.0, C_GRAY_F, '#7f8c8d',
        '行为策略在 s2 实际选"左"\nq(s2,左)=0\nSarsa 用之：q(s1,右) 保持不变',
        fs=8.6, lw=1.4)
    arrow(ax, 10.2, 3.75, 7.95, 1.55, color='#7f8c8d', lw=1.8, ls=(0, (4, 2)),
          rad=-0.3)
    ax.text(8.9, 2.9, 'Sarsa（灰虚线）：\n按当前做法实际走下去', fontsize=8.2,
            color='#7f8c8d', ha='center')

    # ---- 底部：两问 ----
    fig.text(0.5, 0.018,
             'Sarsa 问："按当前做法实际走下去，这条路价值多少？"　'
             'Q 学习法问："如果在后继状态采取最优行动，这条路价值多少？"',
             ha='center', fontsize=9.4, color='#1b2631')
    fig.subplots_adjust(bottom=0.09, top=0.88)
    fig.savefig(os.path.join(OUT, 'fig6-3.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('fig6-3 done')


# ======================================================================
# 图 6-4 在线学习进化闭环：对话-日志-更新-服务（6.7.2）
# ======================================================================
def fig6_4():
    fig, ax = plt.subplots(figsize=(11.4, 6.8))
    ax.set_xlim(-0.5, 11.9)
    ax.set_ylim(-0.7, 6.9)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title('图 6-4 在线学习进化闭环：系统自适应\n'
                 '每一次对话都是一步经验：对话 → 日志 → 更新 → 服务 → 更好的对话，'
                 '系统在循环中持续自我修正',
                 fontsize=11.5, pad=14)

    cx, cy = 6.0, 3.3
    # 中央圆
    ax.add_patch(Circle((cx, cy), 1.35, facecolor='#fef9e7', edgecolor='#b7950b',
                        lw=2.0, zorder=3))
    ax.text(cx, cy + 0.45, '在线进化\n(online evolution)', ha='center',
            fontsize=10.5, fontweight='bold', color='#7d6608', zorder=4)
    ax.text(cx, cy - 0.35, '走一步看一步\n边走边修正', ha='center', fontsize=9.2,
            color='#7d6608', zorder=4)

    # 四节点（上右下左）
    nodes = [
        (6.0, 5.55, C_BLUE_F, C_BLUE_E, '① 对话', '患者与医者Agent\n症状—辨证—反馈\n产生一步经验'),
        (9.35, 3.3, C_GREEN_F, C_GREEN_E, '② 日志', '进化记录\n状态-动作-奖励-误差\n每一步都有账可查'),
        (6.0, 1.05, C_ORANGE_F, C_ORANGE_E, '③ 更新', 'TD 增量更新\nv ← v + α(目标 - 旧值)\n每步经验立即入账'),
        (2.65, 3.3, C_YELLOW_F, C_YELLOW_E, '④ 服务', '改进后的辨证与推荐\n价值表刷新\n更好服务'),
    ]
    for (x, y, fc, ec, tag, txt) in nodes:
        box(ax, x - 1.55, y - 0.78, 3.1, 1.56, fc, ec, tag + '\n' + txt,
            fs=9.4, lw=1.9)
    # 环上箭头（顺时针）
    arrow(ax, 6.85, 5.45, 8.45, 4.55, color='#1f618d', lw=2.6, rad=-0.25)
    arrow(ax, 9.25, 2.45, 8.35, 1.5, color='#1e8449', lw=2.6, rad=-0.25)
    arrow(ax, 5.15, 1.15, 3.55, 2.05, color='#b9770e', lw=2.6, rad=-0.25)
    arrow(ax, 2.75, 4.15, 3.65, 5.1, color='#b7950b', lw=2.6, rad=-0.25)
    # 环节点间标签
    ax.text(7.95, 5.35, '一步经验\n可追溯', fontsize=8.6, color='#1f618d')
    ax.text(9.05, 1.75, '增量更新\n无需等待', fontsize=8.6, color='#1e8449')
    ax.text(4.05, 1.35, '价值表\n刷新', fontsize=8.6, color='#b9770e')
    ax.text(2.85, 5.35, '更好服务\n→ 更好数据', fontsize=8.6, color='#b7950b')

    # 底部：四条实现路径
    box(ax, 0.3, -0.55, 11.1, 1.15, '#f8f9f9', '#99a3a4',
        '四条实现路径：增量更新（数据流驱动进化）　·　探索-利用平衡（ε 随场景周期调度）　·　'
        '基线校准（个人定位持续对齐）　·　反馈校准（用实现修正估计）',
        fs=9.2, lw=1.3)
    fig.text(0.5, 0.012,
             '系统自适应：tcmP 平台医者 Agent 的每一次对话都构成一步经验，'
             '日志记录修正轨迹，增量更新即时刷新价值表，改进后的服务又带来新的对话 —— '
             '没有"学成毕业"的终点，只有持续适应（正文 6.7.2）',
             ha='center', fontsize=8.8, color='#566573')
    fig.subplots_adjust(bottom=0.12, top=0.88)
    fig.savefig(os.path.join(OUT, 'fig6-4.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('fig6-4 done')


if __name__ == '__main__':
    fig6_1()
    fig6_2()
    fig6_3()
    fig6_4()
    print('ALL DONE ->', OUT)
