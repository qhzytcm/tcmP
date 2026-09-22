# -*- coding: utf-8 -*-
"""《中医场景强化学习》第6章 核心图生成脚本（v2 聚焦版，图表工程师·聚焦重绘）

聚焦原则：图体只保留'能代表含义的图段'——收紧 figsize 与 xlim/ylim 并调节
数轴起止刻度与步长，突出关键区域；图题由图题行承担（Excel 图题行/正文图题行），
图内不再重复大标题；图注由四要素版承担（a.对接正文提示语 b.线的注释
c.符号的注释 d.代表含义的指针图段）。
生成：fig6-1 TD 一步修正 / fig6-2 TD(0) 价值学习曲线（聚焦收敛段）
      fig6-3 Q 学习法 Q 表与 max 更新路径 / fig6-4 在线学习进化闭环
输出：drafts/cmrl/figures/ch06/*.png（覆盖既有文件）
风格：SimHei / unicode_minus=False / dpi=200（与全系列一致）
数值：与正文 6.1-6.8 节及习题集完全一致
      （例6.1：γ=0.9, α=0.1；回合1后(0,0,0,0.1)，回合2后(0,0,0.009,0.19)，
       第三回合 s3 TD目标=0.171，v(s3)=0.0252，回合3后(0,0.00081,0.0252,0.271)；
       例6.4：q(s1,左)=-0.1, q(s1,右)=0.01, q(s2,左)=0, q(s2,右)=0.1, max=0.1）
"""
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle
from matplotlib.lines import Line2D

plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ch06')
os.makedirs(OUT, exist_ok=True)

# ---- 全系列统一配色 ----
C_BLUE_F, C_BLUE_E = '#d6eaf8', '#1f618d'
C_GREEN_F, C_GREEN_E = '#d5f5e3', '#1e8449'
C_ORANGE_F, C_ORANGE_E = '#fdebd0', '#b9770e'
C_YELLOW_F, C_YELLOW_E = '#fef9e7', '#b7950b'
C_GRAY_F, C_GRAY_E = '#f2f3f4', '#7f8c8d'
C_RED_F, C_RED_E = '#fadbd8', '#c0392b'


def box(ax, x, y, w, h, fc, ec, txt, fs=9.5, lw=1.6, tc='#1b2631',
        boxstyle='round,pad=0.08', linespacing=1.45, bold=False):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=boxstyle,
                                facecolor=fc, edgecolor=ec, lw=lw, zorder=3))
    ax.text(x + w / 2, y + h / 2, txt, ha='center', va='center',
            fontsize=fs, color=tc, zorder=4, linespacing=linespacing,
            fontweight=('bold' if bold else 'normal'))


def arrow(ax, x1, y1, x2, y2, color='#1b2631', lw=2.0, ls='-', style='-|>',
          rad=0.0, zorder=3, shrinkA=0, shrinkB=0):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2),
                                 arrowstyle=style, color=color, lw=lw,
                                 linestyle=ls, connectionstyle='arc3,rad={}'.format(rad),
                                 mutation_scale=14, zorder=zorder,
                                 shrinkA=shrinkA, shrinkB=shrinkB))


def tag(ax, x, y, txt, color='#566573', fs=9.0):
    """区域小标签（非大标题）"""
    ax.text(x, y, txt, ha='left', va='center', fontsize=fs,
            color=color, fontweight='bold')


# ======================================================================
# 图 6-1 TD 一步修正：老账/新账 + 更新链条（聚焦两段核心，去节奏对比大框）
# ======================================================================
def fig6_1():
    fig, ax = plt.subplots(figsize=(12.4, 5.2))
    ax.set_xlim(-0.3, 13.1)
    ax.set_ylim(-0.5, 5.2)
    ax.set_aspect('equal')
    ax.axis('off')

    # ---- 左半幅：临床比喻（老账 → 新账 → δt） ----
    tag(ax, 0.2, 4.95, '临床比喻：老账 / 新账')
    box(ax, 0.2, 2.7, 2.5, 1.7, C_BLUE_F, C_BLUE_E,
        '老账 v(St)\n初诊时的判断\n\n"我对当前证候\n长期前景的估计"', fs=9.6)
    box(ax, 3.3, 2.7, 2.7, 1.7, C_GREEN_F, C_GREEN_E,
        '新账 Rt+1 + γv(St+1)\n复诊看一步真实反馈\n+ 对后继证候的预判\n\n'
        '"比老账多了一天\n的观察，自然更可信"', fs=9.4)
    arrow(ax, 2.7, 3.55, 3.3, 3.55, color='#1f618d', lw=2.4)
    ax.text(3.0, 3.95, '复诊\n看一步', ha='center', fontsize=8.6, color='#1f618d')
    # 指针图段 1：新账 → δt（相减得差）
    arrow(ax, 4.65, 2.7, 4.65, 2.32, color='#1b2631', lw=1.6)
    ax.text(4.9, 2.48, '相减得差', ha='left', fontsize=8.4, color='#1b2631')
    box(ax, 0.2, 0.45, 5.8, 1.5, C_YELLOW_F, C_YELLOW_E,
        'TD 误差（TD error）：δt = v(St) - (Rt+1 + γv(St+1)) = 新账 - 老账\n\n'
        'δt > 0 估计偏高 → 往下调 ↓　·　δt < 0 估计偏低 → 往上调 ↑　·　δt = 0 无需修正',
        fs=9.2)

    # ---- 右半幅：TD 更新链条（旧估计 → TD目标 → TD误差 → 新估计） ----
    tag(ax, 6.6, 4.95, 'TD 更新链条：把"经验"翻译成"修正量"')
    chain = [
        (6.6, 3.15, C_BLUE_F, C_BLUE_E, '旧估计\nv(St)'),
        (8.4, 3.15, C_GREEN_F, C_GREEN_E, 'TD目标\nRt+1 + γv(St+1)'),
        (10.45, 3.15, C_ORANGE_F, C_ORANGE_E, 'TD误差 δt\n= 目标 - 旧估计'),
    ]
    for k, (x, y, fc, ec, txt) in enumerate(chain):
        box(ax, x, y, 1.35, 1.05, fc, ec, txt, fs=8.8, lw=1.8)
        if k < 2:
            arrow(ax, x + 1.35, y + 0.52, x + 1.61, y + 0.52, color='#1b2631', lw=2.0)
    # 指针图段 2：δt 符号 → 修正方向 → 新估计（自举闭环的核心）
    box(ax, 10.35, 1.55, 1.9, 1.0, C_GREEN_F, C_GREEN_E,
        '新估计\nv(St) ← v(St) + α·δt', fs=8.8, lw=2.0)
    arrow(ax, 11.05, 3.15, 11.3, 2.62, color='#1e8449', lw=2.0, rad=-0.3)
    ax.text(11.55, 2.92, 'δt 符号自动给出\n修正方向 ↑/↓', ha='left', fontsize=8.2,
            color='#1e8449',
            bbox=dict(boxstyle='round,pad=0.15', fc='white', ec='none', alpha=0.85))
    box(ax, 6.6, 0.45, 5.6, 1.5, C_GREEN_F, C_GREEN_E,
        '更新式：v(St) ← v(St) + α[Rt+1 + γv(St+1) - v(St)]\n\n'
        'TD目标（TD target）· TD误差（TD error）· 自举（bootstrapping）\n'
        '用自己当前的估计改进自己', fs=9.4)

    fig.savefig(os.path.join(OUT, 'fig6-1.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('fig6-1 done')


# ======================================================================
# 图 6-2 TD(0) 价值学习曲线：聚焦收敛段（前 15 回合，60 回合模拟）
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
    # 关键数值核对（与正文/习题集一致）
    assert abs(hist[0][3] - 0.1) < 1e-9, hist[0]
    assert abs(hist[1][2] - 0.009) < 1e-9, hist[1]
    assert abs(hist[1][3] - 0.19) < 1e-9, hist[1]
    assert abs(hist[2][1] - 0.00081) < 1e-9, hist[2]
    assert abs(hist[2][2] - 0.0252) < 1e-9, hist[2]
    assert abs(hist[2][3] - 0.271) < 1e-9, hist[2]
    target_s3 = 0.9 * hist[1][3]
    assert abs(target_s3 - 0.171) < 1e-9

    FOCUS = 15   # 聚焦收敛段：前 15 回合
    fig, ax = plt.subplots(figsize=(9.6, 5.8))
    xs = list(range(1, FOCUS + 1))
    colors = ['#2e86c1', '#1e8449', '#b9770e', '#c0392b']
    labels = ['v(s1)', 'v(s2)', 'v(s3)', 'v(s4)']
    for i in range(4):
        ax.plot(xs, [h[i] for h in hist[:FOCUS]], color=colors[i], lw=2.4,
                label='{}（估计值）'.format(labels[i]))
        ax.axhline(true_v[i], color=colors[i], lw=1.1, ls='--', alpha=0.55)
        ax.text(FOCUS + 0.55, true_v[i], '{}'.format(true_v[i]), fontsize=8.6,
                color=colors[i], va='center')
    ax.text(FOCUS + 0.55, 0.015, '虚线 = 真实价值', fontsize=8.4, color='#566573')

    # 关键手算点（回合1/2/3）
    marks = [
        (1, 3, 0.1, '回合1后\nv(s4)=0.1', 0.32, 'left'),
        (2, 3, 0.19, 'v(s4)=0.19', 0.34, 'left'),
        (2, 2, 0.009, '回合2后\nv(s3)=0.009', 0.075, 'left'),
        (3, 3, 0.271, '回合3后 v(s4)=0.271', 0.42, 'left'),
        (3, 2, 0.0252, '回合3：TD目标=0.171\nv(s3)=0.0252', 0.17, 'left'),
        (3, 1, 0.00081, '回合3后\nv(s2)=0.00081', 0.052, 'left'),
    ]
    for (ep, i, val, txt, txty, ha_) in marks:
        ax.plot(ep, val, 'o', color=colors[i], ms=7, zorder=5)
        tx = ep + 1.6 if ha_ == 'left' else ep - 1.0
        ax.annotate(txt, xy=(ep, val), xytext=(tx, txty),
                    fontsize=8.0, color=colors[i], ha=ha_, va='center',
                    arrowprops=dict(arrowstyle='-', color=colors[i], lw=0.9,
                                    shrinkA=2, shrinkB=2),
                    bbox=dict(boxstyle='round,pad=0.12', fc='white',
                              ec='none', alpha=0.82))

    # 信息回传弧线（指针图段：奖励信息逐格反向回传）
    ax.annotate('', xy=(2, 0.009), xytext=(1, 0.1),
                arrowprops=dict(arrowstyle='-|>', color='#b9770e', lw=1.8,
                                connectionstyle='arc3,rad=-0.45'), zorder=4)
    ax.annotate('', xy=(3, 0.00081), xytext=(2, 0.009),
                arrowprops=dict(arrowstyle='-|>', color='#b9770e', lw=1.8,
                                connectionstyle='arc3,rad=-0.45'), zorder=4)
    ax.text(1.35, 0.14, '奖励信息逐格回传\n（每回合最多一格）', fontsize=8.0,
            color='#b9770e')

    ax.set_xlabel('回合（episode）——聚焦收敛段（前 15 回合）', fontsize=10.5)
    ax.set_ylabel('状态价值估计 v(s)', fontsize=10.5)
    ax.set_xlim(0, FOCUS + 1.6)
    ax.set_ylim(-0.03, 1.05)
    ax.set_xticks([1, 2, 3, 5, 10, 15])
    ax.set_yticks([0.0, 0.2, 0.4, 0.6, 0.8, 1.0])
    ax.grid(alpha=0.3, ls=':')
    ax.legend(loc='lower right', fontsize=9.0, frameon=True)
    fig.savefig(os.path.join(OUT, 'fig6-2.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('fig6-2 done; 15回合后 v =', [round(hist[FOCUS - 1][i], 4) for i in range(4)])


# ======================================================================
# 图 6-3 Q 学习法：Q 表 + max 更新路径（数据 4，目标与行为分离）
# ======================================================================
def fig6_3():
    fig, ax = plt.subplots(figsize=(11.8, 5.9))
    ax.set_xlim(-0.4, 12.4)
    ax.set_ylim(-0.5, 5.9)
    ax.set_aspect('equal')
    ax.axis('off')

    # ---- 左区：Q 表（行=状态，列=动作；行间留 0.25 空隙放 max 指向箭头） ----
    tag(ax, 0.35, 5.55, 'Q 表：状态（证候）× 动作（方剂）')
    cell_w, cell_h, x0, y0, gap = 1.5, 1.05, 0.35, 2.15, 0.25
    # 行1(s1) y 3.45~4.5；行2(s2) y 2.15~3.2；表头 y 4.7~5.45
    header = ['', '动作"左"', '动作"右"']
    rows = [['s1', '-0.1', '0.01'], ['s2', '0（假设值）', '0.1']]
    for j, t in enumerate(header):
        fc = C_BLUE_F if j == 0 else '#eaf2f8'
        box(ax, x0 + j * cell_w, y0 + 2 * (cell_h + gap) + 0.2, cell_w, 0.75,
            fc, '#5d6d7e', t, fs=9.8, lw=1.4)
    for i in range(2):
        for j in range(3):
            fc, ec, lw = 'white', '#999999', 1.2
            if i == 0 and j == 2:
                fc, ec, lw = C_GREEN_F, '#1e8449', 2.6
            if i == 1 and j == 2:
                fc, ec = '#a9dfbf', '#1e8449'
            txt = rows[i][j]
            if i == 0 and j == 2:
                txt = '0.01 ← 更新后'
            y = y0 + (1 - i) * (cell_h + gap)
            box(ax, x0 + j * cell_w, y, cell_w, cell_h, fc, ec, txt,
                fs=9.6, lw=lw)
    # 指针图段：绿色箭头 max 源(行2右) → 更新格(行1右)，标注目标与行为分离
    mx = x0 + 2 * cell_w + cell_w / 2          # 第 3 列格心 x = 4.1
    arrow(ax, mx, y0 + cell_h + 0.04, mx, y0 + cell_h + gap - 0.04,
          color='#1e8449', lw=2.2)             # 间隙 3.2~3.45 内的向上箭头
    ax.text(2.6, 1.78,
            '绿色箭头：max 源 q(s2,右)=0.1 → 更新格 q(s1,右)=0.01；'
            '更新目标与行为策略在 s2 的实际动作无关（目标与行为分离）',
            fontsize=8.2, color='#1e8449', ha='center')
    ax.text(2.6, 1.42, '行 = 状态，列 = 动作', fontsize=8.0,
            color='#566573', ha='center')

    # ---- 中区：两条更新式对比（唯一差别：后继项） ----
    tag(ax, 5.55, 5.35, '唯一差别：后继项')
    box(ax, 5.55, 3.5, 3.55, 1.1, C_GREEN_F, '#1e8449',
        'Q 学习法：q(St,At) ← q(St,At)\n+ α[Rt+1 + γ·max_a\' q(St+1,a\') - q(St,At)]',
        fs=8.4, lw=2.0)
    box(ax, 5.55, 2.1, 3.55, 1.1, C_ORANGE_F, '#b9770e',
        'Sarsa：q(St,At) ← q(St,At)\n+ α[Rt+1 + γ·q(St+1,At+1) - q(St,At)]',
        fs=8.4, lw=1.6)
    ax.text(9.25, 4.05, 'max_a\'\n（最优动作）', fontsize=8.4, color='#1e8449', ha='center')
    ax.text(9.25, 2.65, 'At+1\n（实际动作）', fontsize=8.4, color='#a04000', ha='center')
    ax.text(7.32, 1.68, 'Q 学习法：目标与行为分离（异策略 off-policy）',
            ha='center', fontsize=8.8, color='#1e8449')

    # ---- 右区：数据 4 更新路径 ----
    tag(ax, 9.55, 5.35, '数据 4 的更新路径')
    box(ax, 9.55, 3.5, 2.4, 1.0, C_BLUE_F, C_BLUE_E,
        '(s1, 右)\nq = 0（更新前）', fs=8.6)
    box(ax, 9.55, 2.1, 2.4, 1.0, '#eaf2f8', '#5d6d7e',
        '执行"右"\n奖励 r = 0\n到达 s2', fs=8.4)
    arrow(ax, 10.75, 3.5, 10.75, 3.12, color='#1b2631', lw=1.8)
    # Q 学习法 max 路径（绿实线）
    box(ax, 9.55, 0.45, 2.4, 1.1, '#a9dfbf', '#1e8449',
        'max{0, 0.1} = 0.1\nq(s1,右)=0+0.1×(0.1-0)\n= 0.01', fs=8.2, lw=2.2)
    arrow(ax, 10.75, 2.1, 10.75, 1.6, color='#1e8449', lw=2.4)
    ax.text(11.08, 1.88, 'Q 学习法（绿）：\n与 s2 处实际动作无关', fontsize=7.6,
            color='#1e8449', ha='left')
    # Sarsa 实际路径（灰虚线）
    box(ax, 6.3, 0.45, 2.75, 1.1, C_GRAY_F, '#7f8c8d',
        '行为策略在 s2 实际选"左"\nq(s2,左)=0\nSarsa 用之：q(s1,右) 保持不变',
        fs=8.0, lw=1.4)
    arrow(ax, 9.95, 2.28, 7.75, 1.62, color='#7f8c8d', lw=1.8,
          ls=(0, (4, 2)), rad=-0.18)
    ax.text(8.75, 1.68, 'Sarsa（灰虚线）：按当前做法实际走下去', fontsize=7.6,
            color='#7f8c8d', ha='center')

    fig.savefig(os.path.join(OUT, 'fig6-3.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('fig6-3 done')


# ======================================================================
# 图 6-4 在线学习进化闭环：对话-日志-更新-服务（聚焦环体+实现路径横带）
# ======================================================================
def fig6_4():
    fig, ax = plt.subplots(figsize=(10.0, 6.0))
    ax.set_xlim(-0.5, 10.5)
    ax.set_ylim(-0.6, 6.0)
    ax.set_aspect('equal')
    ax.axis('off')

    cx, cy = 5.0, 3.0
    # 中央圆（在线进化）
    ax.add_patch(Circle((cx, cy), 1.15, facecolor='#fef9e7', edgecolor='#b7950b',
                        lw=2.0, zorder=3))
    ax.text(cx, cy + 0.38, '在线进化\n(online evolution)', ha='center',
            fontsize=9.6, fontweight='bold', color='#7d6608', zorder=4)
    ax.text(cx, cy - 0.42, '走一步看一步\n边走边修正', ha='center', fontsize=8.6,
            color='#7d6608', zorder=4)

    # 四节点（上右下左）
    nodes = [
        (5.0, 4.9, C_BLUE_F, C_BLUE_E, '① 对话', '患者与医者Agent\n症状—辨证—反馈\n产生一步经验'),
        (8.35, 3.0, C_GREEN_F, C_GREEN_E, '② 日志', '进化记录\n状态-动作-奖励-误差\n每一步都有账可查'),
        (5.0, 1.1, C_ORANGE_F, C_ORANGE_E, '③ 更新', 'TD 增量更新\nv ← v + α(目标 - 旧值)\n每步经验立即入账'),
        (1.65, 3.0, C_YELLOW_F, C_YELLOW_E, '④ 服务', '改进后的辨证与推荐\n价值表刷新\n更好服务'),
    ]
    for (x, y, fc, ec, tag_, txt) in nodes:
        box(ax, x - 1.5, y - 0.72, 3.0, 1.44, fc, ec, tag_ + '\n' + txt,
            fs=8.8, lw=1.8)
    # 环上箭头（顺时针）
    arrow(ax, 5.85, 4.82, 7.55, 4.05, color='#1f618d', lw=2.4, rad=-0.25)
    arrow(ax, 8.25, 2.2, 7.45, 1.4, color='#1e8449', lw=2.4, rad=-0.25)
    arrow(ax, 4.15, 1.18, 2.45, 1.95, color='#b9770e', lw=2.4, rad=-0.25)
    arrow(ax, 1.75, 3.8, 2.55, 4.6, color='#b7950b', lw=2.4, rad=-0.25)
    # 环节点间标签
    ax.text(6.85, 4.75, '一步经验\n可追溯', fontsize=8.0, color='#1f618d')
    ax.text(8.05, 1.55, '增量更新\n无需等待', fontsize=8.0, color='#1e8449')
    ax.text(3.0, 1.15, '价值表\n刷新', fontsize=8.0, color='#b9770e')
    ax.text(1.6, 4.75, '更好服务\n→ 更好数据', fontsize=8.0, color='#b7950b')

    # 底部横带：四条实现路径（代表含义图段之一）
    box(ax, 0.3, -0.5, 9.4, 1.0, '#f8f9f9', '#99a3a4',
        '四条实现路径：增量更新（数据流驱动进化）　·　探索-利用平衡（ε 随场景周期调度）　·\n'
        '基线校准（个人定位持续对齐）　·　反馈校准（用实现修正估计）',
        fs=8.6, lw=1.3)

    fig.savefig(os.path.join(OUT, 'fig6-4.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('fig6-4 done')


if __name__ == '__main__':
    fig6_1()
    fig6_2()
    fig6_3()
    fig6_4()
    print('ALL DONE ->', OUT)
