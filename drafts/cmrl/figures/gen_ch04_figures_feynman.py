# -*- coding: utf-8 -*-
"""《中医场景强化学习》第4章 费曼图标准重构版（图表工程师 v5：文字精简与字号规范）

本版执行【图内文字精简与字号规范】（第4章）：
  ① 文字分层精简：每幅图图内只保留核心标注（节点名 + 1~2 个关键数值，每幅 ≤10 个标注条目）；
     长描述 / 公式细节 / 次要数值一律移入图注（忠实语义不丢）；
  ② 字号规范：核心标注 ≥11、节点名 ≥10、任何文字禁 <9pt（含坐标轴刻度、图例）；
  ③ 背景降噪：白底、无网格、无渐变、无阴影、无装饰，框线细（节点 lw≤1.6、关键节点 2.0）；
  ④ 忠实语义：关键概念与数值锚点保留在图体（v=(9,10,10,10) 回代链、γ=0.9、r=0/+1、1.9 等），
     其余细节（完整公式、错误记法、代入过程）移入图注，数值口径与正文完全一致；
  ⑤ 图注配套：正文 md 与 Excel 图注行同步追加『e. 阅读引导』句（先看主体→再看细节→回图注对照）。

输出：figures/ch04/fig4-1.png ~ fig4-4.png（覆盖 v4 版）。
风格：SimHei / axes.unicode_minus=False / dpi=200。
数值口径：例4.2 修正值 vπ(s1)=9、vπ(s2)=10、vπ(s3)=10；例4.4 v=[9,10,10,10]ᵀ；例4.5 前四步 0/1/1/1、0.9/1.9/1.9/1.9、1.71/2.71、2.439/3.439。

【移入图注清单】（图体精简后信息去向，供 md/Excel 图注同步参考）
- fig4-1：错误记法长句（若把 s2→s3 的 +1 漏记为 0 则 vπ(s2)=9、vπ(s1)=8.1）、s4 迁延难愈"按停留无奖励计"的说明、"到达康复"字样。
- fig4-2：顶部贝尔曼方程完整式、五部分颜色图例（策略/即时奖励/折扣/后继价值/转移概率）、老医师临床对照句、例4.2 代入数值行（s3=1+0.9×10=10；s2=1+0.9×10=10；s1=0+0.9×10=9）。
- fig4-3：状态图转移奖励 r=0/r=+1、Pπ 矩阵元素（[0,1,0,0] 等）、rπ=[0,1,1,1]ᵀ、I−γPπ 下三角块结构与"从最后一行解起"、最终 v=[9,10,10,10]ᵀ、"价值随距离目标步数衰减"解释。
- fig4-4：例4.5 前四步完整数值表（v1=[0,1,1,1]ᵀ、v2=[0.9,1.9,1.9,1.9]ᵀ、v3=[1.71,2.71,2.71,2.71]ᵀ、v4=[2.439,3.439,3.439,3.439]ᵀ）、误差界公式 ‖vπ−vk‖∞≤γ^k‖vπ−v0‖∞、15 回合/88 步精度说明。
"""
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle, Rectangle

plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.facecolor'] = 'white'
plt.rcParams['savefig.facecolor'] = 'white'

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ch04')
os.makedirs(OUT, exist_ok=True)

# ---------- 费曼风格常量：黑白灰 + 2 种低饱和色点缀 ----------
K   = '#111111'   # 主墨
MG  = '#666666'   # 次级灰
LG  = '#999999'   # 浅灰
B   = '#5b7d9e'   # 灰蓝：目标/康复/最优
R   = '#a35555'   # 灰红：警示/修正
G   = '#6b8e6b'   # 灰绿：康复自环
O   = '#b07a4f'   # 灰橙：今日收入/回传弧线

# ---------- 字号规范（v5）：核心标注 ≥11、节点名 ≥10、任何文字禁 <9 ----------
FS_NODE = 11.5    # 节点：节点名 + 数值
FS_NODE_SMALL = 10.5  # 次节点（对照态）
FS_CORE = 12.0    # 核心标注（行标题、关键数值）
FS_LABEL = 11.0   # 箭头旁注释
FS_HELP = 9.5     # 辅助文字（图内最小允许 9）
FS_LEGEND = 9.5   # 图例
FS_TICK = 9.0     # 坐标轴刻度（下限 9）


def node(ax, cx, cy, w, h, text, ec=K, lw=1.4, fs=FS_NODE, tc=K,
         ls='-', weight='normal'):
    """费曼节点：白底黑框圆角小方块（无彩色填充），文字居中。lw 细（≤1.6）。"""
    ax.add_patch(FancyBboxPatch((cx - w / 2, cy - h / 2), w, h,
                                boxstyle='square,pad=0',
                                fc='white', ec=ec, lw=lw, linestyle=ls))
    ax.text(cx, cy, text, ha='center', va='center', fontsize=fs, color=tc,
            weight=weight, linespacing=1.45)
    return cx, cy


def arrow(ax, x0, y0, x1, y1, color=K, lw=1.9, ls='-', rad=0.0):
    a = FancyArrowPatch((x0, y0), (x1, y1), arrowstyle='-|>', mutation_scale=13,
                        lw=lw, color=color, linestyle=ls,
                        connectionstyle='arc3,rad={}'.format(rad))
    ax.add_patch(a)


def count_texts(fig):
    """统计一幅图所有坐标轴上的图内标注条目数：非空文本（ax.text/ax.annotate 的正文）
    与图例（legend 计 1 条）。空字符串 annotate（纯箭头）不计；标题/坐标轴标签不计。"""
    n = 0
    for ax in fig.axes:
        for t in ax.texts:
            if t.get_text().strip():
                n += 1
        if ax.get_legend() is not None:
            n += 1
    return n


# ============================================================
# 图 4-1 失眠病程链价值（10 个标注）
# 保留：γ=0.9、三主链节点（节点名+关键数值 v=9/10/10）、r=0、r=+1、
#       自环"每步+1/每步0"、s4 对照节点、红圈"不可漏写"。
# 移图注：错误记法长句、s4 无奖励计说明、"到达康复"字样。
# ============================================================
def fig_4_1():
    fig = plt.figure(figsize=(9.5, 4.8))
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis('off')

    ax.text(0.03, 0.955, r'$\gamma$ = 0.9', fontsize=FS_CORE, color=K, weight='bold')

    # 主链三状态节点（节点名 ≥10、数值 ≥11；s3 康复 = 灰蓝细粗框）
    node(ax, 0.15, 0.62, 0.24, 0.30, 's1\n失眠初起\nv = 9', ec=K, fs=FS_NODE, weight='bold')
    node(ax, 0.49, 0.62, 0.24, 0.30, 's2\n心脾两虚证\nv = 10', ec=K, fs=FS_NODE, weight='bold')
    node(ax, 0.84, 0.62, 0.24, 0.30, 's3\n康复\nv = 10', ec=B, lw=2.0, fs=FS_NODE, weight='bold')

    # 转移箭头与奖励（方向明确：病→愈；只标核心数值 r=0 / r=+1）
    arrow(ax, 0.27, 0.62, 0.37, 0.62, color=K, lw=1.9)
    ax.text(0.32, 0.668, 'r = 0', ha='center', fontsize=FS_LABEL, color=K)
    arrow(ax, 0.61, 0.62, 0.72, 0.62, color=K, lw=2.2)
    ax.text(0.665, 0.668, 'r = +1', ha='center', fontsize=FS_LABEL, color=R, weight='bold')
    # 红圈：+1 不可漏写
    ax.add_patch(Circle((0.665, 0.575), 0.013, fc='none', ec=R, lw=1.8))
    ax.text(0.665, 0.525, '不可漏写', ha='center', fontsize=FS_HELP, color=R)

    # s3 自环（吸收态每步 +1）
    arrow(ax, 0.78, 0.765, 0.90, 0.765, color=G, lw=1.8, ls=(0, (4, 3)), rad=-0.35)
    ax.text(0.84, 0.808, '停留每步 +1', ha='center', fontsize=FS_LABEL, color=G)

    # s4 迁延难愈（灰虚线框 = 对照态）
    node(ax, 0.84, 0.24, 0.24, 0.24, 's4\n迁延难愈\nv = 0', ec=MG, lw=1.2, fs=FS_NODE_SMALL, ls=(0, (4, 3)))
    arrow(ax, 0.78, 0.355, 0.90, 0.355, color=MG, lw=1.6, ls=(0, (4, 3)), rad=-0.35)
    ax.text(0.84, 0.398, '停留每步 0', ha='center', fontsize=FS_LABEL, color=MG)

    fig.savefig(os.path.join(OUT, 'fig4-1.png'), dpi=200, bbox_inches='tight', pad_inches=0.05)
    print('fig4-1 OK  标注数 =', count_texts(fig))
    plt.close(fig)


# ============================================================
# 图 4-2 递归账本（6 个标注）
# 保留：三栏节点（①今日收入 + ②明日账 = 今日价值）、+、递归弯箭头、账本隐喻行。
# 移图注：顶部贝尔曼方程、五部分颜色图例、老医师句、例4.2 代入数值行。
# ============================================================
def fig_4_2():
    fig = plt.figure(figsize=(10, 5.2))
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis('off')

    # 三栏（指针图段；节点名 ≥10、核心数值 ≥11）
    node(ax, 0.185, 0.60, 0.29, 0.30, '① 今日收入\n期望即时奖励', ec=K, fs=FS_NODE)
    node(ax, 0.545, 0.60, 0.29, 0.30, '② 明日账\n折扣 × 后继价值', ec=K, fs=FS_NODE)
    node(ax, 0.865, 0.60, 0.22, 0.30, '今日价值\nvπ(s)\n= ① + ②', ec=B, lw=2.0, fs=FS_NODE, weight='bold')

    # 汇聚箭头
    arrow(ax, 0.33, 0.66, 0.755, 0.66, color=O, lw=1.9, rad=0.12)
    ax.text(0.52, 0.71, '+', fontsize=FS_CORE + 3, ha='center', color=K)
    arrow(ax, 0.69, 0.60, 0.755, 0.60, color=B, lw=1.9, rad=0.12)

    # 递归弯箭头：今日价值 → 明日账（bootstrap）
    arrow(ax, 0.865, 0.75, 0.545, 0.75, color=R, lw=2.0, rad=0.42)
    ax.text(0.705, 0.84, '递归：明日的账明天再记', ha='center', fontsize=FS_LABEL,
            color=R, weight='bold')

    # 账本隐喻（核心临床对照，保留一行）
    ax.text(0.5, 0.10, '账本隐喻：今天的账 = 今天的收入 + 折扣 × 明天的账',
            ha='center', fontsize=FS_CORE, weight='bold', color=K)

    fig.savefig(os.path.join(OUT, 'fig4-2.png'), dpi=200, bbox_inches='tight', pad_inches=0.05)
    print('fig4-2 OK  标注数 =', count_texts(fig))
    plt.close(fig)


# ============================================================
# 图 4-3 矩阵求解（10 个标注）
# 保留：①状态图四节点（γ=0.9）、②打包→③求逆回代 标题、回代链 v4=10/v3=10/v2=10/v1=9。
# 移图注：状态图奖励 r、Pπ/rπ/(I−γPπ) 矩阵元素、下三角块结构、最终 v=[9,10,10,10]ᵀ、
#         "价值随距离衰减"解释。
# ============================================================
def fig_4_3():
    fig = plt.figure(figsize=(10.5, 5.8))
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis('off')

    # ---- 行1：四状态图（节点名 ≥10；无奖励文字，奖励值移图注）----
    ax.text(0.02, 0.955, '① 状态图（γ = 0.9）', fontsize=FS_CORE, color=K, weight='bold')
    node(ax, 0.115, 0.88, 0.10, 0.10, 's1', ec=K, fs=FS_NODE_SMALL)
    node(ax, 0.30, 0.88, 0.10, 0.10, 's2', ec=K, fs=FS_NODE_SMALL)
    node(ax, 0.60, 0.88, 0.10, 0.10, 's3', ec=K, fs=FS_NODE_SMALL)
    node(ax, 0.83, 0.88, 0.14, 0.12, 's4\n吸收态 +1', ec=K, lw=2.0, fs=FS_NODE_SMALL, weight='bold')
    arrow(ax, 0.165, 0.88, 0.25, 0.88, color=K, lw=1.7)
    arrow(ax, 0.35, 0.88, 0.76, 0.88, color=K, lw=2.0)
    arrow(ax, 0.65, 0.88, 0.76, 0.88, color=K, lw=1.7)
    arrow(ax, 0.83, 0.815, 0.83, 0.845, color=K, lw=1.5, ls=(0, (4, 3)), rad=-0.3)

    # ---- 行2：打包 → 求逆回代（标题为核心标注；矩阵/向量元素与公式移图注）----
    ax.text(0.02, 0.60, '② 打包 → ③ 求逆回代', fontsize=FS_CORE, color=K, weight='bold')
    # 无文字几何占位：小方块示意"打包为矩阵"，箭头示意"求逆回代"（不产生标注）
    ax.add_patch(FancyBboxPatch((0.18, 0.42), 0.13, 0.13, boxstyle='square,pad=0',
                                fc='white', ec=K, lw=1.1))
    ax.add_patch(FancyBboxPatch((0.34, 0.42), 0.13, 0.13, boxstyle='square,pad=0',
                                fc='white', ec=K, lw=1.1))
    arrow(ax, 0.52, 0.49, 0.62, 0.49, color=B, lw=1.8)

    # ---- 行3：回代链（核心数值锚点 v=(9,10,10,10)，≥11）----
    vals = [('v4 = 10', K), ('v3 = 10', K), ('v2 = 10', K), ('v1 = 9', K)]
    xc = 0.32
    for i, (t, c) in enumerate(vals):
        node(ax, xc, 0.135, 0.105, 0.075, t, ec=c, fs=FS_CORE, tc=c, lw=1.5, weight='bold')
        if i < 3:
            arrow(ax, xc + 0.058, 0.135, xc + 0.098, 0.135, color=K, lw=1.6)
        xc += 0.128
    # 回代起点箭头（几何：从"求逆"指向 v4=10）
    arrow(ax, 0.24, 0.17, 0.265, 0.135, color=MG, lw=1.6, rad=0.2)

    fig.savefig(os.path.join(OUT, 'fig4-3.png'), dpi=200, bbox_inches='tight', pad_inches=0.05)
    print('fig4-3 OK  标注数 =', count_texts(fig))
    plt.close(fig)


# ============================================================
# 图 4-4 价值迭代收敛（10 个标注）
# 保留：① 分量逼近（图例+ k=2 关键点 0.9/1.9）、② 误差收缩（10/9 + 每步 ×0.9）、
#       ③ 不同初值趋同标题。
# 移图注：例4.5 前四步完整数值、误差界公式、收敛精度说明。
# ============================================================
def fig_4_4():
    gamma = 0.9
    NSTEPS = 25
    v = [0.0, 0.0, 0.0, 0.0]
    series1 = [v[0]]
    series2 = [v[1]]
    for k in range(NSTEPS):
        nv = [0.0, 0.0, 0.0, 0.0]
        nv[0] = 0.0 + gamma * v[1]
        nv[1] = 1.0 + gamma * v[3]
        nv[2] = 1.0 + gamma * v[3]
        nv[3] = 1.0 + gamma * v[3]
        v = nv
        series1.append(v[0])
        series2.append(v[1])
    assert abs(series1[1] - 0.0) < 1e-9 and abs(series2[1] - 1.0) < 1e-9
    assert abs(series1[2] - 0.9) < 1e-9 and abs(series2[2] - 1.9) < 1e-9
    assert abs(series1[3] - 1.71) < 1e-9 and abs(series2[3] - 2.71) < 1e-9
    assert abs(series1[4] - 2.439) < 1e-9 and abs(series2[4] - 3.439) < 1e-9

    vpi = [9.0, 10.0, 10.0, 10.0]
    v = [0.0, 0.0, 0.0, 0.0]
    errs = [max(abs(vpi[i] - v[i]) for i in range(4))]
    for k in range(NSTEPS):
        nv = [0.0, 0.0, 0.0, 0.0]
        nv[0] = 0.0 + gamma * v[1]
        nv[1] = 1.0 + gamma * v[3]
        nv[2] = 1.0 + gamma * v[3]
        nv[3] = 1.0 + gamma * v[3]
        v = nv
        errs.append(max(abs(vpi[i] - v[i]) for i in range(4)))
    assert abs(errs[1] - 9.0) < 1e-9 and abs(errs[2] - 8.1) < 1e-9
    assert abs(errs[3] - 7.29) < 1e-9 and abs(errs[4] - 6.561) < 1e-9
    print('  前四步校验通过：', series1[:5], series2[:5])

    fig = plt.figure(figsize=(12.5, 5.6))
    FOCUS = 6
    kk = list(range(NSTEPS + 1))

    # ---- ① 分量逼近：黑白灰线稿，无 grid，刻度字号 ≥9 ----
    ax = fig.add_axes([0.055, 0.14, 0.295, 0.78])
    ax.plot(kk[:FOCUS + 1], series2[:FOCUS + 1], color=B, lw=2.2, marker='o', markersize=4,
            label='v2 = v3 = v4（s2/s3/s4 → 10）')
    ax.plot(kk[:FOCUS + 1], series1[:FOCUS + 1], color=O, lw=2.2, marker='s', markersize=4,
            label='v1（s1 → 9）')
    ax.axhline(10, color=K, ls=(0, (5, 4)), lw=1.0, alpha=0.6)
    ax.axhline(9, color=MG, ls=(0, (5, 4)), lw=1.0, alpha=0.6)
    # 关键数值锚点（k=2：0.9 / 1.9，例4.5 第二步，图体只留这一对）
    for k in (2,):
        ax.plot(k, series2[k], 'o', color=B, markersize=8, zorder=5)
        ax.plot(k, series1[k], 's', color=O, markersize=8, zorder=5)
    ax.text(2, series2[2] + 0.65, '1.9', fontsize=FS_LABEL, ha='center', color=K, weight='bold')
    ax.text(2, series1[2] - 0.95, '0.9', fontsize=FS_LABEL, ha='center', color=K, weight='bold')
    ax.set_xlabel('迭代步 k', fontsize=FS_LABEL, color=K)
    ax.set_ylabel(r'价值估计 $v_k$', fontsize=FS_LABEL, color=K)
    ax.set_xlim(0, FOCUS + 0.3)
    ax.set_ylim(-1.0, 11.3)
    ax.set_xticks(range(0, FOCUS + 1))
    ax.tick_params(labelsize=FS_TICK, colors=K)
    for sp in ax.spines.values():
        sp.set_color(K)
        sp.set_linewidth(1.0)
    leg = ax.legend(loc='lower right', fontsize=FS_LEGEND, frameon=True, edgecolor=K, handlelength=1.6)
    leg.get_frame().set_facecolor('white')
    leg.get_frame().set_linewidth(0.8)
    ax.set_title('① 分量逼近', fontsize=FS_CORE, color=K)

    # ---- ② 误差收缩：每步 ×0.9（指针图段），无 grid ----
    ax2 = fig.add_axes([0.42, 0.14, 0.30, 0.78])
    ax2.plot(kk[:FOCUS + 1], errs[:FOCUS + 1], color=R, lw=2.4, marker='o', markersize=5,
             label=r'误差 = 10 × 0.9$^k$')
    for k in (1, 2):
        ax2.plot(k, errs[k], 'o', color=R, markersize=8, zorder=5)
    ax2.text(1, errs[1] + 0.5, '10', fontsize=FS_LABEL, ha='center', color=K, weight='bold')
    ax2.text(2, errs[2] + 0.5, '9', fontsize=FS_LABEL, ha='center', color=K, weight='bold')
    ax2.annotate('每步 ×0.9', xy=(2.0, errs[2] + 1.4), xytext=(3.6, 8.6),
                 fontsize=FS_CORE, color=R, weight='bold', ha='center',
                 arrowprops=dict(arrowstyle='->', color=R, lw=1.8))
    ax2.set_xlabel('迭代步 k', fontsize=FS_LABEL, color=K)
    ax2.set_ylabel(r'误差 $\|v_\pi - v_k\|_\infty$', fontsize=FS_LABEL, color=K)
    ax2.set_xlim(0, FOCUS + 0.3)
    ax2.set_ylim(0, 11)
    ax2.set_xticks(range(0, FOCUS + 1))
    ax2.tick_params(labelsize=FS_TICK, colors=K)
    for sp in ax2.spines.values():
        sp.set_color(K)
        sp.set_linewidth(1.0)
    leg2 = ax2.legend(loc='upper right', fontsize=FS_LEGEND, frameon=True, edgecolor=K, handlelength=1.6)
    leg2.get_frame().set_facecolor('white')
    leg2.get_frame().set_linewidth(0.8)
    ax2.set_title('② 误差收缩（每步 ×0.9）', fontsize=FS_CORE, color=K)

    # ---- ③ 右下小图：不同初值趋同，无 grid ----
    ax3 = fig.add_axes([0.80, 0.14, 0.175, 0.34])
    for v0, c, ls in [(0.0, K, '-'), (8.0, MG, (0, (5, 4)))]:
        vv = [v0]
        for k in range(20):
            vv.append(1.0 + gamma * vv[-1])
        ax3.plot(range(21), vv, color=c, lw=1.8, ls=ls)
    ax3.axhline(10, color=LG, ls=':', lw=1.0)
    ax3.set_title('③ 不同初值趋同', fontsize=FS_HELP, color=K)
    ax3.set_xlabel('k', fontsize=FS_HELP, color=K)
    ax3.set_ylabel('v(s4)', fontsize=FS_HELP, color=K)
    ax3.tick_params(labelsize=FS_TICK, colors=K)
    ax3.set_xlim(0, 20)
    ax3.set_ylim(0, 11)
    for sp in ax3.spines.values():
        sp.set_color(K)
        sp.set_linewidth(1.0)

    print('fig4-4 OK  标注数 =', count_texts(fig))
    fig.savefig(os.path.join(OUT, 'fig4-4.png'), dpi=200, bbox_inches='tight', pad_inches=0.05)
    plt.close(fig)


if __name__ == '__main__':
    fig_4_1()
    fig_4_2()
    fig_4_3()
    fig_4_4()
    print('ALL DONE ->', OUT)
