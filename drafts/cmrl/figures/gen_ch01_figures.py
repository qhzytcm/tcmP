# -*- coding: utf-8 -*-
"""《中医场景强化学习》第1章 核心图生成脚本
生成：fig1-1 医院科室网格寻路 / fig1-2 四诊→治法方剂→疗效反馈
      fig1-3 辨证论治策略示意 / fig1-5 诊疗全过程轨迹与回报时间线
输出：drafts/cmrl/figures/ch01/*.png
"""
import os
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

# 医院科室映射（图1-1 / 图1-3 共用）
ROOMS = {
    's1': '挂号处', 's2': '内科诊室', 's3': '发热门诊',
    's4': '针灸科', 's5': '中药房', 's6': '手术区',
    's7': '检验科', 's8': '候诊区', 's9': '专家门诊',
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
                    fontsize=13, fontweight='bold', zorder=3)
            ax.text(col + 0.28, row - 0.15, f'{ACT[s][0]} {ACT[s][1]}', ha='center',
                    va='center', fontsize=9.5, color='#424949', zorder=3)
            if with_zheng:
                ax.text(col, row + 0.30, ZHENG[s], ha='center', va='center',
                        fontsize=7.5, color='#616a6b', zorder=3)
        else:  # 图1-1：编号偏上、科室名偏下，禁区/目标加标签
            ax.text(col, row - 0.15, s, ha='center', va='center',
                    fontsize=14, fontweight='bold', zorder=3)
            ax.text(col, row + 0.22, ROOMS[s], ha='center', va='center',
                    fontsize=9, color='#444444', zorder=3)
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
    """图 1-1 医院科室网格寻路：状态、禁区与目标"""
    fig, ax = plt.subplots(figsize=(7.4, 6.8))
    ax.set_xlim(-0.6, 2.6)
    ax.set_ylim(2.6, -0.6)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title('图 1-1 医院科室网格寻路：状态、禁区与目标\n'
                 '智能体：患者 / 导诊 · 动作：上 a1 右 a2 下 a3 左 a4 静止 a5\n'
                 '蓝色虚线箭头：示例路径 s1 → s2 → s5 → s8 → s9',
                 fontsize=11)
    draw_grid(ax)
    # 示例路径
    path = ['s1', 's2', 's5', 's8', 's9']
    for i in range(len(path) - 1):
        x1, y1 = state_xy(path[i])
        x2, y2 = state_xy(path[i + 1])
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle='-|>', color='#1a5276', lw=2.4,
                                    linestyle=(0, (4, 2))), zorder=4)
    handles = [
        Patch(facecolor='white', edgecolor='#999999', label='普通格：可自由进入，r = 0'),
        Patch(facecolor='#f5b041', edgecolor='#999999',
              label='禁区（手术区，forbidden area）：r = -1'),
        Patch(facecolor='#82e0aa', edgecolor='#999999',
              label='目标（专家门诊，target）：r = +1'),
        Line2D([0], [0], color='#333333', lw=3.2, label='越界弹回：r = -1'),
    ]
    ax.legend(handles=handles, loc='lower center', bbox_to_anchor=(0.5, -0.14),
              ncol=2, fontsize=8.8, frameon=True, handlelength=2.0)
    fig.savefig(os.path.join(OUT, 'fig1-1.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('fig1-1 done')


def fig1_2():
    """图 1-2 从四诊到疗效：状态—动作—奖励的临床映射"""
    fig, ax = plt.subplots(figsize=(10.8, 6.0))
    ax.set_xlim(-0.4, 11.6)
    ax.set_ylim(-1.1, 5.4)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title('图 1-2 从四诊到疗效：状态—动作—奖励的临床映射', fontsize=12.5, pad=16)
    boxes = [
        (0.2, 1.2, 3.0, 3.4, '#d6eaf8', '#1f618d',
         '状态 S：四诊信息\n（"此刻我在哪"）\n\n望 —— 神色形态\n闻 —— 声息气味\n问 —— 症候病史\n切 —— 脉象舌象\n\n辨证 = 读状态'),
        (4.2, 1.2, 3.0, 3.4, '#d5f5e3', '#1e8449',
         '动作 A：治法方剂\n（"可以怎么改变情形"）\n\n八法：汗·吐·下·和\n温·清·消·补\n具体到方：麻黄汤、\n银翘散、四君子汤……\n\n论治 = 选动作'),
        (8.2, 1.2, 3.0, 3.4, '#fdebd0', '#b9770e',
         '奖励 R：疗效反馈\n（"做得如何"）\n\n疗效良好 → 正奖励 + \n误诊、疗效不佳 → 负奖励 -\n信任、依从 → 正奖励 +\n\n复诊 = 看奖励'),
    ]
    for x, y, w, h, fc, ec, txt in boxes:
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.08',
                                    facecolor=fc, edgecolor=ec, lw=1.8, zorder=2))
        ax.text(x + w / 2, y + h / 2, txt, ha='center', va='center',
                fontsize=10.5, color='#1b2631', zorder=3, linespacing=1.5)
    # 主箭头 S→A 与 A→R
    ax.annotate('', xy=(4.05, 2.9), xytext=(3.35, 2.9),
                arrowprops=dict(arrowstyle='-|>', color='#1b2631', lw=2.2), zorder=3)
    ax.annotate('', xy=(8.05, 2.9), xytext=(7.35, 2.9),
                arrowprops=dict(arrowstyle='-|>', color='#1b2631', lw=2.2), zorder=3)
    ax.text(3.7, 3.30, '辨证 → 论治', ha='center', fontsize=9.5, color='#1b2631')
    ax.text(7.7, 3.30, '执行动作后收到 Rt+1', ha='center', fontsize=9.5, color='#1b2631')
    # 反馈回路：右框底 → 左框底（复诊转归成新状态）
    ax.annotate('', xy=(1.7, 0.95), xytext=(9.7, 0.95),
                arrowprops=dict(arrowstyle='-|>', color='#b9770e', lw=1.8), zorder=3)
    ax.text(5.7, 0.45, '复诊转归 → 新状态 St+1（交互闭环）', ha='center',
            fontsize=9.5, color='#7d6608')
    fig.savefig(os.path.join(OUT, 'fig1-2.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('fig1-2 done')


def fig1_3():
    """图 1-3 辨证论治策略：每一证候一个方剂，处处有决策"""
    fig, (axL, axR) = plt.subplots(1, 2, figsize=(12.8, 6.9))
    # 左：策略表
    axL.axis('off')
    axL.set_title('策略表：状态（证候）→ 动作（方剂）', fontsize=11)
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
    tbl.set_fontsize(8.6)
    tbl.scale(1, 1.45)
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
    # 右：九宫格 + 三条轨迹
    axR.set_xlim(-0.6, 3.4)
    axR.set_ylim(2.6, -0.6)
    axR.set_aspect('equal')
    axR.axis('off')
    axR.set_title('九宫格轨迹：起点不同、终点相同（殊途同归）', fontsize=11)
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
                         arrowprops=dict(arrowstyle='-|>', color=c, lw=3.0), zorder=2)
    # 红圈提示：改一格、看全局（s5 改走 a2 进禁区）
    axR.add_patch(Circle((0.66, 1.42), 0.15, facecolor='none',
                         edgecolor='#c0392b', lw=1.6, zorder=4))
    handles = [
        Line2D([0], [0], color='#2e86c1', lw=3, label='从 s1 出发'),
        Line2D([0], [0], color='#229954', lw=3, label='从 s2 出发'),
        Line2D([0], [0], color='#a93226', lw=3, label='从 s3 出发（穿禁区）'),
    ]
    fig.legend(handles=handles, loc='lower center', bbox_to_anchor=(0.5, 0.055),
               ncol=3, fontsize=9.5, frameon=True)
    fig.text(0.5, 0.015,
             '红色圈：若把 s5 的动作改为 a2（向右），将进入禁区 s6 —— "改一格、看全局"（正文 1.4.2 练习）',
             ha='center', fontsize=8.5, color='#c0392b')
    fig.subplots_adjust(bottom=0.13, wspace=0.06)
    fig.savefig(os.path.join(OUT, 'fig1-3.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('fig1-3 done')


def fig1_5():
    """图 1-5 诊疗全过程：状态—动作—奖励链与折扣回报时间线"""
    fig, ax = plt.subplots(figsize=(11.8, 6.8))
    ax.set_xlim(-0.4, 13.8)
    ax.set_ylim(-0.3, 5.7)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title('图 1-5 诊疗全过程：状态—动作—奖励链与折扣回报时间线', fontsize=12.5, pad=14)
    ax.text(6.4, 5.25, '状态 = 症状组合 / 证候 · 动作 = 诊疗决策 · 奖励 = 疗效反馈',
            ha='center', fontsize=9.5, color='#566573')

    # ---- 主链（1.6.1 轨迹示例）----
    y = 4.4
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
                fontsize=13, fontweight='bold', zorder=3)
        ax.text(xs[k] + 0.85, y - 0.25, txt, ha='center', va='center',
                fontsize=8.3, color='#444444', zorder=3, linespacing=1.3)
        if k < 4:
            xa1, xa2 = xs[k] + 1.7, xs[k + 1]
            ax.annotate('', xy=(xa2, y), xytext=(xa1, y),
                        arrowprops=dict(arrowstyle='-|>', color='#1f618d', lw=2.0), zorder=3)
            ax.text((xa1 + xa2) / 2, y + 0.40, acts[k], ha='center',
                    fontsize=9, color='#1f618d')
            ax.text((xa1 + xa2) / 2, y - 0.45, rwds[k], ha='center',
                    fontsize=9, color=('#1e8449' if k == 3 else '#444444'),
                    fontweight=('bold' if k == 3 else 'normal'))
    # 回报框
    ax.add_patch(FancyBboxPatch((12.25, 4.05), 1.25, 0.85,
                                boxstyle='round,pad=0.04', facecolor='#e8f8f5',
                                edgecolor='#1e8449', lw=1.4, zorder=2))
    ax.text(12.875, 4.45, '回报\n0+0+0+1\nG = 1', ha='center', va='center',
            fontsize=9.5, color='#1e8449', zorder=3, fontweight='bold', linespacing=1.35)

    # ---- 对照链（穿禁区：另一策略）----
    y2 = 2.0
    sub = [('s2', '误治\n误投寒凉', 3.2), ('s6', '邪陷危重\n（禁区）', 5.6),
           ('s9', '转愈\n终达目标', 8.0)]
    sub_acts = ['a2 向右', 'a3 向下']
    sub_rwds = ['r = -1', 'r = 0']
    for k, (s, txt, x0) in enumerate(sub):
        fc = '#f5b041' if s == 's6' else '#f2f3f4'
        ax.add_patch(FancyBboxPatch((x0, y2 - 0.45), 1.7, 0.9,
                                    boxstyle='round,pad=0.03', facecolor=fc,
                                    edgecolor='#7f8c8d', lw=1.2, zorder=2))
        ax.text(x0 + 0.85, y2 + 0.10, s, ha='center', va='center',
                fontsize=12, fontweight='bold', zorder=3, color='#566573')
        ax.text(x0 + 0.85, y2 - 0.28, txt, ha='center', va='center',
                fontsize=8, color='#566573', zorder=3, linespacing=1.3)
        if k < 2:
            xa1, xa2 = x0 + 1.7, sub[k + 1][2]
            ax.annotate('', xy=(xa2, y2), xytext=(xa1, y2),
                        arrowprops=dict(arrowstyle='-|>', color='#7f8c8d', lw=1.6), zorder=3)
            ax.text((xa1 + xa2) / 2, y2 + 0.32, sub_acts[k], ha='center',
                    fontsize=8.5, color='#566573')
            ax.text((xa1 + xa2) / 2, y2 - 0.40, sub_rwds[k], ha='center',
                    fontsize=8.5, color=('#c0392b' if k == 0 else '#566573'))
    ax.text(9.65, y2 + 0.62, '另一策略：G = 0 + (-1) + 0 = -1', ha='center',
            fontsize=9, color='#7f8c8d', fontweight='bold')

    # ---- 折扣框（1.6.2）----
    ax.add_patch(FancyBboxPatch((0.4, 0.30), 12.0, 1.45,
                                boxstyle='round,pad=0.05', facecolor='#fef9e7',
                                edgecolor='#b7950b', lw=1.4, zorder=2))
    ax.text(6.4, 1.42, '折扣率 γ：为远期奖励定价', ha='center', fontsize=10,
            fontweight='bold', color='#7d6608', zorder=3)
    ax.text(6.4, 1.00, 'Gt = Rt+1 + γRt+2 + γ^2 Rt+3 + …（γ ∈ (0,1)）　'
                       'γ 小 → 短视（只治标）；γ 大 → 远视（能治本）',
            ha='center', fontsize=9.5, color='#1b2631', zorder=3)
    ax.text(6.4, 0.55, '例：奖励序列 1, 1, 1, … 时，γ = 0.5 → G = 2；γ = 0.9 → G = 10　｜　'
                       '注意：Rt+1 是时刻 t 动作所得（下标错位，初学者易错）',
            ha='center', fontsize=9.5, color='#1b2631', zorder=3)

    fig.savefig(os.path.join(OUT, 'fig1-5.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('fig1-5 done')


if __name__ == '__main__':
    fig1_1()
    fig1_2()
    fig1_3()
    fig1_5()
    print('ALL DONE ->', OUT)
