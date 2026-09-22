# -*- coding: utf-8 -*-
"""《中医场景强化学习》第6章 费曼图标准重构版（图表工程师 v5：文字精简与字号规范）

本版执行【图内文字精简与字号规范】（第6章）：
  ① 文字分层精简：每幅图只保留核心标注（节点名 + 1~2 个关键数值，每幅 ≤10 个标注条目）；
     长描述 / 公式细节 / 次要数值一律移入图注（忠实语义不丢）；
  ② 字号规范：核心标注 ≥11、节点名 ≥10、任何文字禁 <9pt（含图例、坐标轴刻度）；
  ③ 背景降噪：白底、无网格、无渐变、无阴影，框线细（节点 lw≤1.6、关键格 2.0）；
  ④ 忠实语义：关键数值锚点保留在图体（v(s3)=0.0252、q(s2,右)=0.1、q(s1,右)=0.01、
     max{0,0.1}=0.1、α=0.1/γ=0.9 等），其余细节（完整更新式、TD目标 0.171、Sarsa 对比）移入图注；
  ⑤ 图注配套：正文 md 与 Excel 图注行同步追加『e. 阅读引导』句。

输出：figures/ch06/fig6-1.png ~ fig6-4.png（覆盖 v4 版）。
风格：SimHei / axes.unicode_minus=False / dpi=200。
数值：例6.1（γ=0.9, α=0.1）：回合1后(0,0,0,0.1)、回合2后(0,0,0.009,0.19)、
      第三回合 s3 TD目标=0.171、v(s3)=0.0252、回合3后(0,0.00081,0.0252,0.271)；
      例6.4：q(s1,左)=-0.1, q(s1,右)=0.01, q(s2,左)=0, q(s2,右)=0.1, max=0.1。

【移入图注清单】
- fig6-1：左右两 tag 标题、"相减得差"、"δt 符号自动给出修正方向 ↑/↓"、更新式完整大框
          （v(St)←v(St)+α[Rt+1+γv(St+1)−v(St)]）、TD目标/TD误差/自举英文对照、
          "比老账多了一天观察更可信"。
- fig6-2：真实价值虚线标注（v(s1)=0.729、v(s2)=0.81、v(s3)=0.9、v(s4)=1）、
          其余手算点（轮2 v(s3)=0.009、轮3 v(s2)=0.00081、v(s4)=0.271、TD目标 0.171）、
          15 轮后数值（0.041、0.149、0.406、0.794）、回传弧线说明。
- fig6-3：Q 表标题"状态（证候）× 动作（方剂）"、"行=状态列=动作"、两条更新式对比
          （Q学习法 max vs Sarsa 实际所选）、Sarsa 灰虚线路径与"q(s1,右)保持不变"、
          "更新目标与行为策略在 s2 的实际动作无关"。
- fig6-4：四节点内长描述（对话内容/日志要素/更新式/服务内容）、四段箭头旁注释
          （一步经验可追溯/增量更新无需等待/价值表刷新/更好服务→更好数据）、
          "走一步看一步、边走边修正"。
"""
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle

plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.facecolor'] = 'white'
plt.rcParams['savefig.facecolor'] = 'white'

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ch06')
os.makedirs(OUT, exist_ok=True)

# ---------- 费曼风格常量 ----------
K   = '#111111'
MG  = '#666666'
LG  = '#999999'
B   = '#5b7d9e'
R   = '#a35555'
G   = '#6b8e6b'
O   = '#b07a4f'
GREEN_FILL = '#eef3ee'   # max 源格浅绿底（极低饱和）

# ---------- 字号规范（v5）：核心标注 ≥11、节点名 ≥10、任何文字禁 <9 ----------
FS_NODE = 11.0      # 节点（节点名）
FS_NODE_SMALL = 10.0  # 次节点
FS_CORE = 12.0      # 核心数值/标题
FS_LABEL = 11.0     # 箭头旁注释
FS_HELP = 9.5       # 辅助文字
FS_LEGEND = 9.5     # 图例
FS_TICK = 9.0       # 坐标轴刻度


def box(ax, x, y, w, h, ec, txt, fs=FS_NODE, lw=1.4, tc=K, fc='white',
        boxstyle='square,pad=0', linespacing=1.4, bold=False, ls='-'):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=boxstyle,
                                facecolor=fc, edgecolor=ec, lw=lw,
                                linestyle=ls, zorder=3))
    ax.text(x + w / 2, y + h / 2, txt, ha='center', va='center',
            fontsize=fs, color=tc, zorder=4, linespacing=linespacing,
            fontweight=('bold' if bold else 'normal'))


def arrow(ax, x1, y1, x2, y2, color=K, lw=1.9, ls='-', rad=0.0, zorder=3):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2),
                                 arrowstyle='-|>', color=color, lw=lw,
                                 linestyle=ls, connectionstyle='arc3,rad={}'.format(rad),
                                 mutation_scale=13, zorder=zorder))


def count_texts(fig):
    n = 0
    for ax in fig.axes:
        for t in ax.texts:
            if t.get_text().strip():
                n += 1
        if ax.get_legend() is not None:
            n += 1
    return n


# ======================================================================
# 图 6-1 TD 一步修正：老账/新账 + 更新链条（8 个标注）
# 保留：老账/新账两节点、复诊看一步、δt 公式、链条三框、新估计框。
# 移图注：tag 标题、修正方向注释、更新式大框、英文对照。
# ======================================================================
def fig6_1():
    fig, ax = plt.subplots(figsize=(12.4, 5.2))
    ax.set_xlim(-0.3, 13.1)
    ax.set_ylim(-0.5, 5.2)
    ax.set_aspect('equal')
    ax.axis('off')

    # ---- 左半幅：临床比喻（老账 → 新账 → δt）----
    box(ax, 0.2, 2.7, 2.5, 1.7, K, '老账 v(St)\n初诊时的判断',
        fs=FS_NODE, lw=1.4)
    box(ax, 3.3, 2.7, 2.7, 1.7, K, '新账 Rt+1 + γv(St+1)\n复诊看一步真实反馈\n+ 对后继证候的预判',
        fs=FS_NODE, lw=1.8)
    arrow(ax, 2.7, 3.55, 3.3, 3.55, color=B, lw=2.0)
    ax.text(3.0, 3.98, '复诊\n看一步', ha='center', fontsize=FS_LABEL, color=B)
    arrow(ax, 4.65, 2.7, 4.65, 2.32, color=K, lw=1.5)
    box(ax, 0.2, 0.45, 5.8, 1.5, K,
        'TD 误差：δt = v(St) - (Rt+1 + γv(St+1)) = 老账 - 新账\n\n'
        'δt > 0 估计偏高 → 往下调 ↓　·　δt < 0 估计偏低 → 往上调 ↑　·　δt = 0 无需修正',
        fs=FS_NODE)

    # ---- 右半幅：TD 更新链条（旧估计 → TD目标 → TD误差 → 新估计）----
    chain = [
        (6.6, 3.15, '旧估计\nv(St)'),
        (8.4, 3.15, 'TD目标\nRt+1 + γv(St+1)'),
        (10.45, 3.15, 'TD误差 δt\n= 目标 - 旧估计'),
    ]
    for k, (x, y, txt) in enumerate(chain):
        box(ax, x, y, 1.35, 1.05, K, txt, fs=FS_NODE_SMALL, lw=1.5)
        if k < 2:
            arrow(ax, x + 1.35, y + 0.52, x + 1.61, y + 0.52, color=K, lw=1.9)
    box(ax, 10.35, 1.55, 1.9, 1.0, K,
        '新估计\nv(St) ← v(St) + α·δt', fs=FS_NODE, lw=1.8)
    arrow(ax, 11.05, 3.15, 11.3, 2.62, color=G, lw=1.9, rad=-0.3)

    print('fig6-1 done  标注数 =', count_texts(fig))
    fig.savefig(os.path.join(OUT, 'fig6-1.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)


# ======================================================================
# 图 6-2 TD(0) 价值学习曲线（7 个标注；聚焦前 15 回合；无网格）
# 保留：图例、手算锚点（轮1 v(s4)=0.1、轮2 v(s4)=0.19、轮3 v(s3)=0.0252）、
#       信息逐格回传、虚线=真实价值。
# 移图注：真实值标注、其余手算点、15 轮后数值。
# ======================================================================
def fig6_2():
    gamma, alpha = 0.9, 0.1
    true_v = [0.729, 0.81, 0.9, 1.0]
    v = [0.0, 0.0, 0.0, 0.0]
    N = 60
    hist = []
    for ep in range(1, N + 1):
        start = 1 if ep == 1 else 0
        for s in range(start, 4):
            r = 1.0 if s == 3 else 0.0
            v_next = 0.0 if s == 3 else v[s + 1]
            target = r + gamma * v_next
            v[s] += alpha * (target - v[s])
        hist.append(list(v))
    assert abs(hist[0][3] - 0.1) < 1e-9, hist[0]
    assert abs(hist[1][2] - 0.009) < 1e-9, hist[1]
    assert abs(hist[1][3] - 0.19) < 1e-9, hist[1]
    assert abs(hist[2][1] - 0.00081) < 1e-9, hist[2]
    assert abs(hist[2][2] - 0.0252) < 1e-9, hist[2]
    assert abs(hist[2][3] - 0.271) < 1e-9, hist[2]
    target_s3 = 0.9 * hist[1][3]
    assert abs(target_s3 - 0.171) < 1e-9
    print('  手算校验通过；15回合后 v =', [round(hist[14][i], 4) for i in range(4)])

    FOCUS = 15
    fig, ax = plt.subplots(figsize=(9.6, 5.8))
    xs = list(range(1, FOCUS + 1))
    styles = [
        (K, '-', 'v(s4)'),
        (MG, '-', 'v(s3)'),
        (MG, (0, (5, 3)), 'v(s2)'),
        (LG, (0, (1, 2)), 'v(s1)'),
    ]
    for i in range(4):
        c, ls, lab = styles[i]
        ax.plot(xs, [h[i] for h in hist[:FOCUS]], color=c, lw=2.2, ls=ls, label=lab)
        ax.axhline(true_v[i], color=c, lw=1.0, ls=(0, (8, 4)), alpha=0.55)
    ax.text(FOCUS + 0.55, 0.015, '虚线 = 真实价值', fontsize=FS_HELP, color=MG)

    # 手算关键锚点（≤3 个；0.0252 为本章核心数值锚点，必留）
    marks = [
        (1, 3, 0.1, '轮1后\nv(s4) = 0.1', 0.32, 'left'),
        (2, 3, 0.19, '轮2后 v(s4) = 0.19', 0.36, 'left'),
        (3, 2, 0.0252, '轮3后\nv(s3) = 0.0252', 0.18, 'left'),
    ]
    for (ep, i, val, txt, txty, ha_) in marks:
        c = styles[i][0]
        ax.plot(ep, val, 'o', color=c, ms=7, zorder=5)
        tx = ep + 1.6
        ax.annotate(txt, xy=(ep, val), xytext=(tx, txty),
                    fontsize=FS_HELP, color=c, ha=ha_, va='center',
                    arrowprops=dict(arrowstyle='-', color=c, lw=0.9,
                                    shrinkA=2, shrinkB=2),
                    bbox=dict(boxstyle='round,pad=0.12', fc='white',
                              ec='none', alpha=0.85))

    # 信息回传弧线（灰色虚线；只保留说明文字一条）
    ax.annotate('', xy=(2, 0.009), xytext=(1, 0.1),
                arrowprops=dict(arrowstyle='-|>', color=O, lw=1.6,
                                linestyle=(0, (4, 2)),
                                connectionstyle='arc3,rad=-0.45'), zorder=4)
    ax.annotate('', xy=(3, 0.00081), xytext=(2, 0.009),
                arrowprops=dict(arrowstyle='-|>', color=O, lw=1.6,
                                linestyle=(0, (4, 2)),
                                connectionstyle='arc3,rad=-0.45'), zorder=4)
    ax.text(1.35, 0.14, '奖励信息逐格回传\n（每回合最多一格）', fontsize=FS_HELP, color=MG)

    ax.set_xlabel('回合——聚焦收敛段（前 15 回合）', fontsize=FS_LABEL, color=K)
    ax.set_ylabel('状态价值估计 v(s)', fontsize=FS_LABEL, color=K)
    ax.set_xlim(0, FOCUS + 1.6)
    ax.set_ylim(-0.03, 1.05)
    ax.set_xticks([1, 2, 3, 5, 10, 15])
    ax.set_yticks([0.0, 0.2, 0.4, 0.6, 0.8, 1.0])
    ax.tick_params(labelsize=FS_TICK, colors=K)
    for sp in ax.spines.values():
        sp.set_color(K)
        sp.set_linewidth(1.0)
    leg = ax.legend(loc='lower right', fontsize=FS_LEGEND, frameon=True,
                    edgecolor=K, handlelength=1.6)
    leg.get_frame().set_facecolor('white')
    leg.get_frame().set_linewidth(0.8)
    print('fig6-2 done  标注数 =', count_texts(fig))
    fig.savefig(os.path.join(OUT, 'fig6-2.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)


# ======================================================================
# 图 6-3 Q 学习法：Q 表 + max 更新路径（10 个标注）
# 保留：表头（动作左/右）、行首（s1/s2）、四格数值、绿色箭头"目标与行为分离"、
#       更新式数值行（q(s1,右)=0+0.1×(0.1−0)=0.01）。
# 移图注：Q 表标题、两条更新式对比、Sarsa 路径、max 源与更新格关系说明。
# ======================================================================
def fig6_3():
    fig, ax = plt.subplots(figsize=(11.8, 5.9))
    ax.set_xlim(-0.4, 12.4)
    ax.set_ylim(-0.5, 5.9)
    ax.set_aspect('equal')
    ax.axis('off')

    # ---- Q 表（行=状态，列=动作；白底黑框网格；核心标注 ≤10）----
    cell_w, cell_h, x0, y0, gap = 1.5, 1.05, 1.6, 2.15, 0.25
    header = ['', '动作"左"', '动作"右"']
    rows = [['s1', '-0.1', '0.01'], ['s2', '0', '0.1']]
    for j, t in enumerate(header):
        if j == 0:
            continue
        box(ax, x0 + j * cell_w, y0 + 2 * (cell_h + gap) + 0.2, cell_w, 0.75,
            K, t, fs=FS_NODE, lw=1.2)
    for i in range(2):
        for j in range(3):
            ec, lw = K, 1.1
            if (i, j) == (0, 2):
                ec, lw = G, 2.0
            if (i, j) == (1, 2):
                ec, lw = G, 1.6
            txt = rows[i][j]
            y = y0 + (1 - i) * (cell_h + gap)
            if (i, j) == (1, 2):
                box(ax, x0 + j * cell_w, y, cell_w, cell_h, ec, txt,
                    fs=FS_CORE, lw=lw, fc=GREEN_FILL, bold=True)
            else:
                box(ax, x0 + j * cell_w, y, cell_w, cell_h, ec, txt,
                    fs=FS_CORE, lw=lw)
    # 绿色箭头：max 源 → 更新格（核心指针图段）
    mx = x0 + 2 * cell_w + cell_w / 2
    arrow(ax, mx, y0 + cell_h + 0.04, mx, y0 + cell_h + gap - 0.04,
          color=G, lw=2.0)
    ax.text(x0 + 3 * cell_w / 2, 1.52,
            '绿色箭头：max 源 q(s2,右)=0.1 → 更新格 q(s1,右)=0.01\n（目标与行为分离）',
            fontsize=FS_HELP, color=G, ha='center')

    # ---- 右区：更新数值行（核心数值锚点：max{0,0.1}=0.1 → 0.01）----
    box(ax, 8.1, 2.5, 3.4, 1.15, G,
        '更新：q(s1,右) = 0 + 0.1×(0.1 - 0)\n= 0.01', fs=FS_NODE, lw=1.6)

    print('fig6-3 done  标注数 =', count_texts(fig))
    fig.savefig(os.path.join(OUT, 'fig6-3.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)


# ======================================================================
# 图 6-4 在线学习进化闭环（6 个标注）
# 保留：中央圆"在线进化"、四节点（①对话 ②日志 ③更新 ④服务）、底部四条实现路径。
# 移图注：节点内长描述、四段箭头注释、"走一步看一步"。
# ======================================================================
def fig6_4():
    fig, ax = plt.subplots(figsize=(10.0, 6.0))
    ax.set_xlim(-0.5, 10.5)
    ax.set_ylim(-0.6, 6.0)
    ax.set_aspect('equal')
    ax.axis('off')

    cx, cy = 5.0, 3.0
    ax.add_patch(Circle((cx, cy), 1.15, facecolor='white', edgecolor=K,
                        lw=1.8, zorder=3))
    ax.text(cx, cy, '在线进化', ha='center', fontsize=FS_CORE,
            fontweight='bold', color=K, zorder=4)

    nodes = [
        (5.0, 4.9, '① 对话'),
        (8.35, 3.0, '② 日志'),
        (5.0, 1.1, '③ 更新'),
        (1.65, 3.0, '④ 服务'),
    ]
    for (x, y, tag_) in nodes:
        box(ax, x - 1.5, y - 0.72, 3.0, 1.44, K, tag_, fs=FS_CORE, lw=1.6)
    arrow(ax, 5.85, 4.82, 7.55, 4.05, color=B, lw=2.0, rad=-0.25)
    arrow(ax, 8.25, 2.2, 7.45, 1.4, color=G, lw=2.0, rad=-0.25)
    arrow(ax, 4.15, 1.18, 2.45, 1.95, color=O, lw=2.0, rad=-0.25)
    arrow(ax, 1.75, 3.8, 2.55, 4.6, color=R, lw=2.0, rad=-0.25)

    box(ax, 0.3, -0.5, 9.4, 1.0, MG,
        '四条实现路径：增量更新 · 探索-利用平衡 · 基线校准 · 反馈校准',
        fs=FS_NODE, lw=1.2)

    print('fig6-4 done  标注数 =', count_texts(fig))
    fig.savefig(os.path.join(OUT, 'fig6-4.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)


if __name__ == '__main__':
    fig6_1()
    fig6_2()
    fig6_3()
    fig6_4()
    print('ALL DONE ->', OUT)
