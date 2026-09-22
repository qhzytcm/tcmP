# -*- coding: utf-8 -*-
"""《中医场景强化学习》第1章 核心图生成脚本（v2 聚焦版，图表工程师·试点验证）
聚焦原则：图体只保留'能代表含义的图段'——收紧 figsize 与 xlim/ylim，
突出关键区域；图题由 Excel sheet 图题行承担，图内不再重复大标题。
生成：fig1-1 医院垂直切面网格寻路（v3：沿走廊+电梯，不穿越科室） / fig1-2 四诊→治法方剂→疗效反馈
      fig1-3 辨证论治策略示意 / fig1-5 诊疗主链轨迹与回报时间线（只保留 0-5 步主链）
      fig1-6 双向映射环（映射⇄反哺）
输出：drafts/cmrl/figures/ch01/*.png（覆盖既有文件）
"""
import os
import math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyBboxPatch, Circle, Patch
from matplotlib.lines import Line2D

plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ch01')
os.makedirs(OUT, exist_ok=True)


def state_xy(s):
    """行优先编号 → 格心坐标 (col, row)"""
    i = int(s[1:]) - 1
    return (i % 3, i // 3)


# 医院垂直切面映射（图1-1 共用；v3 真实寻路逻辑：沿走廊+电梯，不穿越科室）
# 中间列 s2/s5/s8 = 垂直交通核（电梯/楼梯）；左右两列 = 左手侧/右手侧诊室房间。
ROOMS = {
    's1': '大厅·挂号处', 's2': '电梯核', 's3': '内科诊室',
    's4': '针灸科', 's5': '电梯核', 's6': '手术区',
    's7': '检验科', 's8': '电梯核', 's9': '专家门诊',
}
ZHENG = {
    's1': '风寒表证', 's2': '风热犯表', 's3': '寒湿困脾',
    's4': '脾虚气弱', 's5': '食积中阻', 's6': '湿热蕴结',
    's7': '肾阳不足', 's8': '气血两虚', 's9': '向愈恢复',
}
ACT = {
    's1': ('↓', 'a3'), 's2': ('↓', 'a3'), 's3': ('←', 'a4'),
    's4': ('↓', 'a3'), 's5': ('↓', 'a3'), 's6': ('←', 'a4'),
    's7': ('→', 'a2'), 's8': ('→', 'a2'), 's9': ('·', 'a5'),
}


def draw_grid(ax, with_room=True, with_zheng=False, with_act=False):
    """绘制 3×3 医院科室网格（图1-1/图1-3 共用，仅格内标注不同）"""
    for s in ['s1', 's2', 's3', 's4', 's5', 's6', 's7', 's8', 's9']:
        col, row = state_xy(s)
        fc = '#f5b041' if s == 's6' else ('#82e0aa' if s == 's9' else 'white')
        ax.add_patch(Rectangle((col - 0.5, row - 0.5), 1, 1, facecolor=fc,
                               edgecolor='#999999', lw=1.2, zorder=1))
        if with_act:  # 图1-3：编号左上、动作右上、证候下方
            ax.text(col - 0.20, row - 0.20, s, ha='center', va='center',
                    fontsize=12, fontweight='bold', zorder=3)
            ax.text(col + 0.28, row - 0.15, f'{ACT[s][0]} {ACT[s][1]}', ha='center',
                    va='center', fontsize=8.8, color='#424949', zorder=3)
            if with_zheng:
                ax.text(col, row + 0.30, ZHENG[s], ha='center', va='center',
                        fontsize=7.2, color='#616a6b', zorder=3)
        else:  # 图1-1：编号偏上、科室名偏下，禁区/目标加标签
            ax.text(col, row - 0.15, s, ha='center', va='center',
                    fontsize=13, fontweight='bold', zorder=3)
            ax.text(col, row + 0.22, ROOMS[s], ha='center', va='center',
                    fontsize=8.5, color='#444444', zorder=3)
            if s == 's6':
                ax.text(col, row + 0.40, '禁区（r = -1）', ha='center', va='center',
                        fontsize=7, color='#b03a2e', zorder=3)
            if s == 's9':
                ax.text(col, row + 0.40, '目标（r = +1）', ha='center', va='center',
                        fontsize=7, color='#1e8449', zorder=3)
    # 越界弹回：四周边框加粗
    for (x0, y0, x1, y1) in [(-0.5, -0.5, 2.5, -0.5), (-0.5, 2.5, 2.5, 2.5),
                             (-0.5, -0.5, -0.5, 2.5), (2.5, -0.5, 2.5, 2.5)]:
        ax.plot([x0, x1], [y0, y1], color='#333333', lw=3.2,
                solid_capstyle='butt', zorder=2)


def fig1_1():
    """图 1-1 医院垂直切面网格寻路（聚焦核心楼层走廊区域，去除图内大标题）

    真实寻路逻辑修正（v3）：患者沿走廊行走 → 乘电梯/楼梯到目标楼层 →
    再沿走廊行走 → 找到左手侧/右手侧第 N 个窗口（诊室）→ 敲门进入或候诊叫号。
    3×3 网格重解释为医院垂直切面（3 层楼 × 每层走廊+两侧诊室）：
      · 中间列 s2/s5/s8 = 垂直交通核（电梯/楼梯），上下楼在此移动；
      · 左右两列 s1/s4/s7、s3/s6/s9 = 左手侧/右手侧诊室房间，从走廊进入；
      · 每层一条水平走廊连通（s1→s2→s3 等）；
      · s6 = 2 层右手侧禁区（手术区/设备间，患者不可进入）；
      · s9 = 3 层右手侧第 2 个窗口（专家门诊：敲门进入或候诊叫号）。
    示例路径（蓝色虚线箭头）：s1(1层走廊左端·大厅) → s2(1层走廊) → 乘电梯↑ →
    s5(2层走廊) → 乘电梯↑ → s8(3层走廊) → 右转进入 s9，全程沿走廊+电梯，
    不穿越任何科室房间。奖励约定：越界 −1、禁区 −1、目标 +1、其他 0（与 1.5 节一致）。
    """
    fig, ax = plt.subplots(figsize=(6.4, 6.9))
    ax.set_xlim(-1.65, 3.60)   # 聚焦：3×3 网格 + 左侧楼层标签 + 右侧标注
    ax.set_ylim(2.95, -0.95)
    ax.set_aspect('equal')
    ax.axis('off')

    # ---- 医院外轮廓 + 两道楼板（越界/楼板弹回边界） ----
    for (x0, y0, x1, y1) in [(-0.5, -0.5, 2.5, -0.5), (-0.5, 2.5, 2.5, 2.5),
                             (-0.5, -0.5, -0.5, 2.5), (2.5, -0.5, 2.5, 2.5)]:
        ax.plot([x0, x1], [y0, y1], color='#333333', lw=3.4,
                solid_capstyle='butt', zorder=2)
    for y in [0.5, 1.5]:   # 中间两道楼板
        ax.plot([-0.5, 2.5], [y, y], color='#5d6d7e', lw=2.6,
                solid_capstyle='butt', zorder=2)

    # ---- 楼层标签（左侧） ----
    for row, name in {0: '1层', 1: '2层', 2: '3层'}.items():
        ax.text(-1.00, row, name, ha='center', va='center',
                fontsize=12.5, fontweight='bold', color='#34495e', zorder=5)

    # ---- 中间列：垂直交通核 s2/s5/s8（浅灰底 + 电梯井虚线边界） ----
    for s in ['s2', 's5', 's8']:
        col, row = state_xy(s)
        ax.add_patch(Rectangle((col - 0.5, row - 0.5), 1, 1, facecolor='#eaecee',
                               edgecolor='#85929e', lw=1.6, zorder=1))
        ax.text(col - 0.34, row + 0.33, s, ha='center', va='center',
                fontsize=8, fontweight='bold', color='#566573', zorder=3)
        ax.text(col, row + 0.12, '走廊', ha='center', va='center',
                fontsize=8.2, color='#7f8c8d', zorder=3)
        ax.text(col, row - 0.24, '电梯↑', ha='center', va='center',
                fontsize=9, color='#1a5276', fontweight='bold', zorder=3)
    for x in [0.5, 1.5]:
        ax.plot([x, x], [-0.5, 2.5], color='#85929e', lw=1.4,
                linestyle=(0, (3, 2)), zorder=2)

    # ---- 左右两列：诊室房间（s6 禁区橙、s9 目标绿） ----
    room_names = {
        's1': '大厅·挂号处', 's3': '内科诊室', 's4': '针灸科',
        's6': '手术区', 's7': '检验科', 's9': '专家门诊',
    }
    sides = {'s1': '左手侧', 's3': '右手侧', 's4': '左手侧',
             's6': '右手侧', 's7': '左手侧', 's9': '右手侧'}
    for s in ['s1', 's3', 's4', 's6', 's7', 's9']:
        col, row = state_xy(s)
        if s == 's6':
            fc = '#f5b041'
        elif s == 's9':
            fc = '#82e0aa'
        else:
            fc = 'white'
        ax.add_patch(Rectangle((col - 0.5, row - 0.5), 1, 1, facecolor=fc,
                               edgecolor='#999999', lw=1.2, zorder=1))
        ax.text(col - 0.33, row + 0.33, s, ha='center', va='center',
                fontsize=9.5, fontweight='bold', color='#2c3e50', zorder=3)
        ax.text(col, row + 0.06, room_names[s], ha='center', va='center',
                fontsize=8.8, color='#444444', zorder=3)
        if s in ('s6', 's9'):
            label = '禁区 r = -1' if s == 's6' else '目标 r = +1'
            color = '#b03a2e' if s == 's6' else '#1e8449'
            ax.text(col, row - 0.36, label, ha='center', va='center',
                    fontsize=7.4, color=color, fontweight='bold', zorder=3)
        else:
            ax.text(col, row - 0.36, sides[s], ha='center', va='center',
                    fontsize=7.0, color='#7f8c8d', zorder=3)
        # 门：朝走廊（中间列）一边
        dx = 0.5 if col == 0 else -0.5
        ax.plot([col + dx, col + dx], [row - 0.10, row + 0.10],
                color='#5d6d7e', lw=2.0, zorder=3)
    # s6 / s9 补充标注（指针图段：指向 s9 专家门诊窗口）
    ax.annotate('患者不可进入', xy=(2, 0.56), xytext=(2, 0.40),
                arrowprops=dict(arrowstyle='->', color='#b03a2e', lw=1.2),
                ha='center', va='center', fontsize=7.2, color='#b03a2e', zorder=4)
    ax.annotate('右手侧第2窗口', xy=(2.44, 2.08), xytext=(2.62, 2.36),
                arrowprops=dict(arrowstyle='->', color='#1e8449', lw=1.2),
                ha='center', va='center', fontsize=7.8, color='#1e8449',
                fontweight='bold', zorder=4)
    ax.text(2, 1.56, '敲门进入/候诊叫号', ha='center', va='center',
            fontsize=6.9, color='#145a32', zorder=4)

    # ---- 示例路径：蓝色虚线箭头 s1→s2→s5→s8→s9（沿走廊+电梯，不穿科室） ----
    for (a, b) in [('s1', 's2'), ('s2', 's5'), ('s5', 's8'), ('s8', 's9')]:
        x1, y1 = state_xy(a)
        x2, y2 = state_xy(b)
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle='-|>', color='#1a5276', lw=2.4,
                                    linestyle=(0, (4, 2))), zorder=4)
    # 电梯段标注（s2→s5、s5→s8：垂直交通核内上行）
    for yy in [0.30, 1.30]:
        ax.text(1.42, yy, '乘电梯↑', ha='left', va='center',
                fontsize=7.4, color='#1a5276', fontweight='bold', zorder=5)

    handles = [
        Patch(facecolor='white', edgecolor='#999999', label='诊室房间：可进入，r = 0'),
        Patch(facecolor='#eaecee', edgecolor='#85929e', label='垂直交通核（电梯/楼梯）'),
        Patch(facecolor='#f5b041', edgecolor='#999999', label='禁区（手术区）：r = -1'),
        Patch(facecolor='#82e0aa', edgecolor='#999999', label='目标（专家门诊）：r = +1'),
        Line2D([0], [0], color='#1a5276', lw=2.4, linestyle=(0, (4, 2)),
               label='示例路径：沿走廊+乘电梯'),
        Line2D([0], [0], color='#333333', lw=3.2, label='越界弹回：r = -1'),
    ]
    ax.legend(handles=handles, loc='lower center', bbox_to_anchor=(0.5, -0.14),
              ncol=2, fontsize=7.6, frameon=True, handlelength=1.8)
    fig.savefig(os.path.join(OUT, 'fig1-1.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('fig1-1 done')


def fig1_2():
    """图 1-2 从四诊到疗效：状态—动作—奖励的临床映射（聚焦三框主链，去除图内大标题）"""
    fig, ax = plt.subplots(figsize=(9.4, 4.5))
    ax.set_xlim(-0.35, 11.75)   # 聚焦：三框 + 双箭头 + 反馈回路
    ax.set_ylim(-0.45, 4.95)
    ax.set_aspect('equal')
    ax.axis('off')
    boxes = [
        (0.2, 1.0, 3.0, 3.4, '#d6eaf8', '#1f618d',
         '状态 S：四诊信息\n（"此刻我在哪"）\n\n望 —— 神色形态\n闻 —— 声息气味\n问 —— 症候病史\n切 —— 脉象舌象\n\n辨证 = 读状态'),
        (4.2, 1.0, 3.0, 3.4, '#d5f5e3', '#1e8449',
         '动作 A：治法方剂\n（"可以怎么改变情形"）\n\n八法：汗·吐·下·和\n温·清·消·补\n具体到方：麻黄汤、\n银翘散、四君子汤……\n\n论治 = 选动作'),
        (8.2, 1.0, 3.0, 3.4, '#fdebd0', '#b9770e',
         '奖励 R：疗效反馈\n（"做得如何"）\n\n疗效良好 → 正奖励 + \n误诊、疗效不佳 → 负奖励 -\n信任、依从 → 正奖励 + \n\n复诊 = 看奖励'),
    ]
    for x, y, w, h, fc, ec, txt in boxes:
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.08',
                                    facecolor=fc, edgecolor=ec, lw=1.8, zorder=2))
        ax.text(x + w / 2, y + h / 2, txt, ha='center', va='center',
                fontsize=9.8, color='#1b2631', zorder=3, linespacing=1.5)
    # 主箭头 S→A 与 A→R
    ax.annotate('', xy=(4.05, 2.7), xytext=(3.35, 2.7),
                arrowprops=dict(arrowstyle='-|>', color='#1b2631', lw=2.2), zorder=3)
    ax.annotate('', xy=(8.05, 2.7), xytext=(7.35, 2.7),
                arrowprops=dict(arrowstyle='-|>', color='#1b2631', lw=2.2), zorder=3)
    ax.text(3.7, 3.10, '辨证 → 论治', ha='center', fontsize=9.2, color='#1b2631')
    ax.text(7.7, 3.10, '执行动作后收到 Rt+1', ha='center', fontsize=9.2, color='#1b2631')
    # 反馈回路：右框底 → 左框底（复诊转归成新状态）
    ax.annotate('', xy=(1.7, 0.72), xytext=(9.7, 0.72),
                arrowprops=dict(arrowstyle='-|>', color='#b9770e', lw=1.8), zorder=3)
    ax.text(5.7, 0.18, '复诊转归 → 新状态 St+1（交互闭环）', ha='center',
            fontsize=9.2, color='#7d6608')
    fig.savefig(os.path.join(OUT, 'fig1-2.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('fig1-2 done')


def fig1_3():
    """图 1-3 辨证论治策略：每一证候一个方剂，处处有决策（聚焦左表右图，压缩尺寸）"""
    fig, (axL, axR) = plt.subplots(1, 2, figsize=(10.2, 5.6))
    # 左：策略表
    axL.axis('off')
    axL.set_title('策略表：状态（证候）→ 动作（方剂）', fontsize=9.5)
    cols = ['状态', '证候（示意）', '动作', '方剂（示意）']
    rows = [
        ['s1', '风寒表证', 'a3（↓）', '麻黄汤（辛温解表）'],
        ['s2', '风热犯表', 'a3（↓）', '银翘散（辛凉解表）'],
        ['s3', '寒湿困脾', 'a4（←）', '藿香正气散（芳香化湿）'],
        ['s4', '脾虚气弱', 'a3（↓）', '四君子汤（益气健脾）'],
        ['s5', '食积中阻', 'a3（↓）', '保和丸（消食导滞）'],
        ['s6', '湿热蕴结（禁区）', 'a4（←）', '茵陈蒿汤（清热利湿）'],
        ['s7', '肾阳不足', 'a2（→）', '金匮肾气丸（温补肾阳）'],
        ['s8', '气血两虚', 'a2（→）', '八珍汤（益气养血）'],
        ['s9', '向愈恢复', 'a5（静止）', '静观调护（效不更方）'],
    ]
    tbl = axL.table(cellText=rows, colLabels=cols, loc='center', cellLoc='center')
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(7.6)
    tbl.scale(1, 1.38)
    for j in range(4):
        c = tbl[0, j]
        c.set_facecolor('#1f4e79')
        c.set_text_props(color='white', fontweight='bold')
    for i in range(1, 10):
        for j in range(4):
            c = tbl[i, j]
            if i == 6:
                c.set_facecolor('#fde9d9')   # 禁区行
            elif i == 9:
                c.set_facecolor('#e8f8f5')   # 目标行
    # 右：九宫格 + 三条轨迹（聚焦网格中心）
    axR.set_xlim(-0.7, 3.4)
    axR.set_ylim(2.7, -0.7)
    axR.set_aspect('equal')
    axR.axis('off')
    axR.set_title('九宫格轨迹：起点不同、终点相同（殊途同归）', fontsize=9.5)
    draw_grid(axR, with_act=True, with_zheng=True)
    paths = [
        (['s1', 's4', 's7', 's8', 's9'], '#2e86c1'),
        (['s2', 's5', 's8', 's9'], '#229954'),
        (['s3', 's6', 's9'], '#a93226'),
    ]
    for p, c in paths:
        for i in range(len(p) - 1):
            x1, y1 = state_xy(p[i])
            x2, y2 = state_xy(p[i + 1])
            axR.annotate('', xy=(x2, y2), xytext=(x1, y1),
                         arrowprops=dict(arrowstyle='-|>', color=c, lw=2.8), zorder=2)
    # 红圈提示：改一格、看全局（s5 改走 a2 进禁区）
    axR.add_patch(Circle((0.66, 1.42), 0.15, facecolor='none',
                         edgecolor='#c0392b', lw=1.6, zorder=4))
    handles = [
        Line2D([0], [0], color='#2e86c1', lw=3, label='从 s1 出发'),
        Line2D([0], [0], color='#229954', lw=3, label='从 s2 出发'),
        Line2D([0], [0], color='#a93226', lw=3, label='从 s3 出发（穿禁区）'),
    ]
    fig.legend(handles=handles, loc='lower center', bbox_to_anchor=(0.5, 0.02),
               ncol=3, fontsize=8.2, frameon=True)
    fig.text(0.5, -0.015,
             '红圈：若把 s5 的动作改为 a2（向右），将进入禁区 s6 —— "改一格、看全局"（正文 1.4.2 练习）',
             ha='center', fontsize=7.6, color='#c0392b')
    fig.subplots_adjust(bottom=0.15, wspace=0.06)
    fig.savefig(os.path.join(OUT, 'fig1-3.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('fig1-3 done')


def fig1_5():
    """图 1-5 诊疗全过程：状态—动作—奖励链与回报时间线（聚焦 0-5 步主链，去除对照链与折扣框）"""
    fig, ax = plt.subplots(figsize=(9.8, 3.3))
    ax.set_xlim(-0.2, 13.9)    # 聚焦：主链 0-5 步 + 回报框
    ax.set_ylim(3.45, 6.0)     # 聚焦：仅主链带（状态盒 + 动作/奖励标注）
    ax.set_aspect('equal')
    ax.axis('off')

    # 主链（1.6.1 轨迹示例）
    y = 4.6
    xs = [0.8, 3.2, 5.6, 8.0, 10.4]
    main = [('s1', '初诊\n症状组合'), ('s2', '辨证\n风寒表证'), ('s5', '首方\n麻黄汤'),
            ('s8', '复诊\n表证渐解'), ('s9', '痊愈\n目标 +1')]
    acts = ['a2 向右', 'a3 向下', 'a3 向下', 'a2 向右']
    rwds = ['r = 0', 'r = 0', 'r = 0', 'r = +1']
    for k, (s, txt) in enumerate(main):
        fc = '#82e0aa' if s == 's9' else 'white'
        ax.add_patch(FancyBboxPatch((xs[k], y - 0.5), 1.7, 1.0,
                                    boxstyle='round,pad=0.03', facecolor=fc,
                                    edgecolor='#1f618d', lw=1.4, zorder=2))
        ax.text(xs[k] + 0.85, y + 0.12, s, ha='center', va='center',
                fontsize=12, fontweight='bold', zorder=3)
        ax.text(xs[k] + 0.85, y - 0.25, txt, ha='center', va='center',
                fontsize=7.8, color='#444444', zorder=3, linespacing=1.3)
        if k < 4:
            xa1, xa2 = xs[k] + 1.7, xs[k + 1]
            ax.annotate('', xy=(xa2, y), xytext=(xa1, y),
                        arrowprops=dict(arrowstyle='-|>', color='#1f618d', lw=2.0), zorder=3)
            ax.text((xa1 + xa2) / 2, y + 0.38, acts[k], ha='center',
                    fontsize=8.5, color='#1f618d')
            ax.text((xa1 + xa2) / 2, y - 0.48, rwds[k], ha='center',
                    fontsize=8.5, color=('#1e8449' if k == 3 else '#444444'),
                    fontweight=('bold' if k == 3 else 'normal'))
    # 回报框
    ax.add_patch(FancyBboxPatch((12.25, 4.15), 1.3, 0.85,
                                boxstyle='round,pad=0.04', facecolor='#e8f8f5',
                                edgecolor='#1e8449', lw=1.4, zorder=2))
    ax.text(12.9, 4.55, '回报\n0+0+0+1\nG = 1', ha='center', va='center',
            fontsize=9.2, color='#1e8449', zorder=3, fontweight='bold', linespacing=1.35)
    fig.savefig(os.path.join(OUT, 'fig1-5.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('fig1-5 done')


def fig1_6():
    """图 1-6 中医临床元素与强化学习概念：双向映射环（聚焦环体，去除图内大标题）"""
    fig, ax = plt.subplots(figsize=(9.6, 9.2))
    ax.set_xlim(-6.6, 6.6)
    ax.set_ylim(-6.5, 6.5)
    ax.set_aspect('equal')
    ax.axis('off')

    # 五组配对（角度按顺时针=临床流程：四诊→辨证→方剂→疗效→传变→再四诊）
    pairs = [
        (90, '四诊症状', '状态', 'state'),
        (18, '辨证论治', '策略', 'policy'),
        (-54, '治法方剂', '动作', 'action'),
        (-126, '疗效反馈', '奖励', 'reward'),
        (162, '病邪传变', '状态转移', 'state\ntransition'),
    ]
    R_RL, R_TCM = 2.45, 5.05
    for deg, tcm, rl, en in pairs:
        a = math.radians(deg)
        # 内环 RL 概念（浅蓝，两行：中文 + 英文）
        cx_rl, cy_rl = R_RL * math.cos(a), R_RL * math.sin(a)
        ax.add_patch(FancyBboxPatch((cx_rl - 1.0, cy_rl - 0.475), 2.0, 0.95,
                                    boxstyle='round,pad=0.06', facecolor='#d6eaf8',
                                    edgecolor='#1f618d', lw=1.6, zorder=3))
        ax.text(cx_rl, cy_rl + 0.13, rl, ha='center', va='center', fontsize=10.5,
                fontweight='bold', color='#1f618d', zorder=4)
        ax.text(cx_rl, cy_rl - 0.20, en, ha='center', va='center', fontsize=7.2,
                color='#566573', fontstyle='italic', zorder=4, linespacing=1.1)
        # 外环中医临床元素（浅绿）
        cx_tm, cy_tm = R_TCM * math.cos(a), R_TCM * math.sin(a)
        ax.add_patch(FancyBboxPatch((cx_tm - 1.05, cy_tm - 0.425), 2.1, 0.85,
                                    boxstyle='round,pad=0.06', facecolor='#d5f5e3',
                                    edgecolor='#1e8449', lw=1.6, zorder=3))
        ax.text(cx_tm, cy_tm, tcm, ha='center', va='center', fontsize=10.5,
                fontweight='bold', color='#1e8449', zorder=4)
        # 双向箭头：映射（TCM→RL，蓝）与反哺（RL→TCM，红）各一支，微错开
        a1, a2 = a + 0.14, a - 0.14
        x1, y1 = 3.62 * math.cos(a1), 3.62 * math.sin(a1)
        x2, y2 = 3.82 * math.cos(a1), 3.82 * math.sin(a1)
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle='-|>', color='#c0392b', lw=2.2), zorder=3)  # 反哺：RL→TCM
        x3, y3 = 3.82 * math.cos(a2), 3.82 * math.sin(a2)
        x4, y4 = 3.62 * math.cos(a2), 3.62 * math.sin(a2)
        ax.annotate('', xy=(x4, y4), xytext=(x3, y3),
                    arrowprops=dict(arrowstyle='-|>', color='#1f618d', lw=2.2), zorder=3)  # 映射：TCM→RL

    # 中央：映射 ⇄ 反哺（两条反向箭头 + 两词，避免生僻字形）
    ax.add_patch(Circle((0, 0), 1.18, fc='#fdebd0', ec='#c0392b', lw=2.2, zorder=4))
    ax.text(0, 0.28, '映射', ha='center', va='center', fontsize=15,
            fontweight='bold', color='#c0392b', zorder=5)
    ax.text(0, -0.30, '反哺', ha='center', va='center', fontsize=15,
            fontweight='bold', color='#1f618d', zorder=5)
    ax.annotate('', xy=(0.52, 0.12), xytext=(0.52, -0.12),
                arrowprops=dict(arrowstyle='-|>', color='#1f618d', lw=2.2), zorder=5)   # 临床→算法（映射）
    ax.annotate('', xy=(-0.52, -0.12), xytext=(-0.52, 0.12),
                arrowprops=dict(arrowstyle='-|>', color='#c0392b', lw=2.2), zorder=5)   # 算法→临床（反哺）
    ax.text(0, -0.72, '互译互哺', ha='center', va='center', fontsize=8.5,
            color='#7f8c8d', zorder=5)

    # 临床流程环走向标注
    flow = '临床流程环向：四诊（观察）→ 辨证（决策）→ 开方（行动）→ 随访（反馈）→ 传变（转归）→ 再四诊'
    ax.text(0, -5.6, flow, ha='center', va='center', fontsize=9.5,
            color='#515a5a', zorder=3)
    fig.savefig(os.path.join(OUT, 'fig1-6.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('fig1-6 done')


if __name__ == '__main__':
    fig1_1()
    fig1_2()
    fig1_3()
    fig1_5()
    fig1_6()
    print('ALL DONE ->', OUT)
