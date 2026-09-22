# -*- coding: utf-8 -*-
"""《中医场景强化学习》全书性概念图生成脚本（图表工程师交付·第二轮·v2 几何修正版）

生成 5 幅全书性概念图（对应任务 1-3、5-6 的迭代-循环-AgentLoop-映射循环-人机闭环）：
  fig1-6   映射循环：中医临床元素 ⇄ 强化学习概念 双向映射环（ch01/06-1.6.md 1.6.3 节）
  fig5-5   迭代-循环：统一算法循环 评估→改进→再评估（价值迭代/策略迭代/时序差分，ch05/06-1.6.md 5.6.2 节）
  fig10-5  AgentLoop：Agent 自主循环 感知→决策→行动→反馈→学习（ch10/06-1.6.md 10.6.2 节）
  fig10-6  人机闭环：六者与 AI 平台双向交互 + CI/CD 进化闭环（ch10/08-1.8.md 10.8.2 节）
  fig10-7  算力与智能特征：足够算力阈值前后的智能能力曲线（ch10/07-1.7.md 10.7.1 节）

技术规范：matplotlib、SimHei、axes.unicode_minus=False、dpi=200、PNG 输出 figures/chNN/。
风格：与 figures/gen_ch05_figures.py / ch10/make_figures_ch10.py 一致——
  FancyBboxPatch 圆角框、浅色系（#d6eaf8/#fdebd0/#d5f5e3/#fef9e7）、图内标题、底部引语、bbox_inches='tight'。
字形坑：图片内一律不用 ⇄/↔ 等生僻箭头（SimHei 覆盖不确定），双向用两条 FancyArrowPatch 表示；
        希腊字母与数学符号用 mathtext（$\\gamma$、$\\pi$、$\\alpha$、$\\delta$）；负号用 ASCII '-'。
v2 修正：逐坐标复核盒体重叠（图1-6 内外环径向分离加大、英文对照移入内环盒；
        图5-5 循环徽章下移入三角空隙、共性带/实例卡下移；
        图10-5 能力标注移入节点盒、节点半径外扩；
        图10-6 六角色位避开平台与 CI/CD 条、交互标注移入角色盒、回环线置于盒下）。
数值一致性：脚本内 assert 校验正文关键数值（γ=0.9 达 1% 精度 44 轮、0.9^k≤0.01、策略总数 |A|^|S| 等）。
"""
import os
import math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Circle

plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = {
    'ch01': os.path.join(HERE, 'ch01'),
    'ch05': os.path.join(HERE, 'ch05'),
    'ch10': os.path.join(HERE, 'ch10'),
}
for d in OUT.values():
    os.makedirs(d, exist_ok=True)


# ---------- 数值一致性自检（与正文 / check 脚本口径一致） ----------
def assert_numbers():
    # 5.6.2：γ=0.9 误差按 0.9^k 衰减，达 1% 精度约需 44 轮；γ=0.5 约 7 轮
    k44 = next(k for k in range(1, 200) if 0.9 ** k <= 0.01)
    k7 = next(k for k in range(1, 200) if 0.5 ** k <= 0.01)
    assert k44 == 44 and k7 == 7, (k44, k7)
    # 5.5.3：确定性策略总数 ≤ |A|^|S|
    assert 5 ** 9 == 1953125
    # 图10-7 逻辑曲线单调且过阈值前后形态正确（低算力平台期 / 高算力跃升期）
    xs = [i / 10 for i in range(121)]
    ys = [1.3 + 7.0 / (1 + math.exp(-1.6 * (x - 7.0))) for x in xs]
    assert all(ys[i] <= ys[i + 1] for i in range(len(ys) - 1))          # 单调不减
    assert ys[0] < 1.5 and ys[40] < 1.8 and ys[70] > 4.0                # 阈值前平台期
    assert ys[110] > 8.0 and (ys[75] - ys[70]) > 5 * (ys[25] - ys[20])   # 阈值后跃升期斜率 ≫ 平台期
    print('[assert] 5.6.2 收敛轮数 / 策略总数 / 图10-7 曲线形态 全部一致 OK')


# ---------- 通用绘制辅助 ----------
def box(ax, cx, cy, w, h, text, fc, ec, fs=9.5, lw=1.6, tc='#1b2631',
        bold=False, zorder=3, style='round,pad=0.06'):
    ax.add_patch(FancyBboxPatch((cx - w / 2, cy - h / 2), w, h,
                                boxstyle=style, facecolor=fc, edgecolor=ec,
                                lw=lw, zorder=zorder))
    ax.text(cx, cy, text, ha='center', va='center', fontsize=fs, color=tc,
            zorder=zorder + 1, linespacing=1.45,
            fontweight='bold' if bold else 'normal')


def arrow(ax, xy1, xy2, color='#1b2631', lw=2.0, ls='-', rad=0.0, zorder=3):
    ax.annotate('', xy=xy2, xytext=xy1,
                arrowprops=dict(arrowstyle='-|>', color=color, lw=lw,
                                linestyle=ls, connectionstyle=f'arc3,rad={rad}'),
                zorder=zorder)


def line(ax, xy1, xy2, color='#b2babb', lw=1.0, ls='--', zorder=1):
    ax.plot([xy1[0], xy2[0]], [xy1[1], xy2[1]], color=color, lw=lw,
            linestyle=ls, zorder=zorder)


# =====================================================================
# 图 1-6 映射循环：中医临床元素 ⇄ 强化学习概念 双向映射环（ch01/06-1.6.md 1.6.3）
# v2：R_RL=2.45 / R_TCM=5.05，径向分离加大；英文对照移入内环盒两行排布
# =====================================================================
def fig1_6():
    fig, ax = plt.subplots(figsize=(12.8, 11.6))
    ax.set_xlim(-6.4, 6.4)
    ax.set_ylim(-5.9, 6.1)
    ax.set_aspect('equal')
    ax.axis('off')
    fig.suptitle('图 1-6 中医临床元素与强化学习概念：双向映射环\n'
                 '四诊症状—状态、治法方剂—动作、疗效反馈—奖励、病邪传变—状态转移、辨证论治—策略',
                 fontsize=12.5, y=0.965)

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
        arrow(ax, (x1, y1), (x2, y2), color='#c0392b', lw=2.2)   # 反哺：RL→TCM
        x3, y3 = 3.82 * math.cos(a2), 3.82 * math.sin(a2)
        x4, y4 = 3.62 * math.cos(a2), 3.62 * math.sin(a2)
        arrow(ax, (x3, y3), (x4, y4), color='#1f618d', lw=2.2)   # 映射：TCM→RL

    # 中央：映射 ⇄ 反哺（两条反向箭头 + 两词，避免生僻字形）
    ax.add_patch(Circle((0, 0), 1.18, fc='#fdebd0', ec='#c0392b', lw=2.2, zorder=4))
    ax.text(0, 0.28, '映射', ha='center', va='center', fontsize=16,
            fontweight='bold', color='#c0392b', zorder=5)
    ax.text(0, -0.30, '反哺', ha='center', va='center', fontsize=16,
            fontweight='bold', color='#1f618d', zorder=5)
    arrow(ax, (0.52, -0.12), (0.52, 0.12), color='#1f618d', lw=2.2)   # 临床→算法（映射）
    arrow(ax, (-0.52, 0.12), (-0.52, -0.12), color='#c0392b', lw=2.2)  # 算法→临床（反哺）
    ax.text(0, -0.72, '互译互哺', ha='center', va='center', fontsize=8.5,
            color='#7f8c8d', zorder=5)

    # 临床流程环走向标注
    flow = '临床流程环向：四诊（观察）→ 辨证（决策）→ 开方（行动）→ 随访（反馈）→ 传变（转归）→ 再四诊'
    ax.text(0, -5.05, flow, ha='center', va='center', fontsize=9.5,
            color='#515a5a', zorder=3)

    fig.text(0.5, 0.012,
             '同一个诊疗过程的两套话语：临床话语给出问题的语义，算法话语给出求解的结构——'
             '“映射”把辨证经验翻译成可计算的对象，“反哺”把计算结果翻译回临床改进诊疗',
             ha='center', va='center', fontsize=9.5, color='#515a5a')
    fig.subplots_adjust(top=0.90, bottom=0.03)
    fig.savefig(os.path.join(OUT['ch01'], 'fig1-6.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('fig1-6 done')


# =====================================================================
# 图 5-5 迭代-循环：统一算法循环 评估→改进→再评估（ch05/06-1.6.md 5.6.2）
# v2：循环徽章移入上两盒与再评估盒之间的空隙；共性带/实例卡下移
# =====================================================================
def fig5_5():
    fig, ax = plt.subplots(figsize=(12.4, 9.8))
    ax.set_xlim(0, 12.4)
    ax.set_ylim(0, 10)
    ax.axis('off')
    fig.suptitle('图 5-5 统一算法循环：评估 → 改进 → 再评估\n'
                 '价值迭代、策略迭代、时序差分——三类算法共用同一循环骨架，差异只在评估深度与收敛判据',
                 fontsize=12.5, y=0.965)

    # 主循环三角形
    box(ax, 2.9, 8.35, 3.5, 1.15, '① 评估（价值估计）\n算出当前策略下每个状态的价值',
        '#eaf2f8', '#1f618d', fs=9.6)
    box(ax, 7.3, 8.35, 3.6, 1.15, '② 改进（策略更新）\n按价值最优方向更新策略',
        '#eaf2f8', '#1f618d', fs=9.6)
    box(ax, 5.1, 5.55, 3.9, 1.15, '③ 再评估（检验收敛）\n检查是否达到收敛判据',
        '#fdebd0', '#a04000', fs=9.6)
    # 循环箭头
    arrow(ax, (4.65, 8.35), (5.5, 8.35), rad=-0.25)          # 评估→改进
    arrow(ax, (6.7, 7.78), (6.25, 6.20), rad=-0.35)          # 改进→再评估
    arrow(ax, (4.05, 6.20), (3.55, 7.78), rad=-0.35)         # 再评估→评估（否，回环）
    ax.text(3.62, 6.95, '否（未收敛）：回到①再评估', ha='center', va='center',
            fontsize=8.4, color='#c0392b')
    # 循环中心徽章（置于再评估盒之上、上两盒之下的空隙，r=0.75）
    ax.add_patch(Circle((5.1, 6.95), 0.75, fc='#fef9e7', ec='#b7950b', lw=1.8, zorder=4))
    ax.text(5.1, 6.95, '统一算法循环\n评估—改进—再评估', ha='center', va='center',
            fontsize=8.6, color='#7d6608', fontweight='bold', zorder=5, linespacing=1.4)

    # 收敛出口（绿色）
    box(ax, 9.9, 6.6, 3.7, 1.6, r'收敛出口' '\n' r'满足判据（$\max_s|\Delta v| < \varepsilon$ 或 $\pi_{k+1} = \pi_k$）' '\n' r'→ 输出最优策略 / 价值',
        '#d5f5e3', '#1e8449', fs=9.2)
    arrow(ax, (7.05, 5.95), (8.05, 6.45), color='#1e8449', lw=2.2, rad=0.1)
    ax.text(7.5, 6.02, '判据成立', ha='center', va='center', fontsize=8.5,
            color='#1e8449', fontweight='bold')
    ax.text(9.9, 5.25, '收敛性由 γ < 1 的收缩性保证（5.2.2、5.6.2）', ha='center',
            va='center', fontsize=8.5, color='#515a5a')

    # 共性带（下移至再评估盒之下）
    box(ax, 6.2, 4.3, 11.0, 0.95,
        '三类算法的循环共性：评估 → 改进 → 再评估；差异仅在“评估到什么程度、如何判断收敛”\n'
        '——价值迭代与策略迭代要求模型已知（5.6.2 模型边界），时序差分以数据逼近，火候不同，殊途同归',
        '#fef9e7', '#b7950b', fs=8.8)

    # 三个实例卡片（下移）
    box(ax, 2.0, 2.25, 3.85, 2.7,
        r'价值迭代（5.4 节）' '\n' r'评估一步：$v_{k+1} = \max_a q_k$' '\n' r'改进即下一轮评估' '\n'
        r'判据：$\max_s |v_{k+1} - v_k| < \varepsilon$' '\n' r'例5.4：γ = 0.9 约 44 轮达 1% 精度',
        '#eaf2f8', '#1f618d', fs=8.9)
    box(ax, 6.2, 2.25, 3.85, 2.7,
        r'策略迭代（5.5 节）' '\n' r'评估到底：解 $v_\pi = (I - \gamma P_\pi)^{-1} r_\pi$' '\n'
        r'改进：$\pi \leftarrow \arg\max_a q$（贪婪）' '\n'
        r'判据：$\pi_{k+1} = \pi_k$ 对一切 $s$ 成立' '\n' r'定理5.2 单调不降 / 定理5.3 有限步终止',
        '#d5f5e3', '#1e8449', fs=8.9)
    box(ax, 10.4, 2.25, 3.85, 2.7,
        r'时序差分（第 6 章）' '\n' r'评估一步：$v \leftarrow v + \alpha \delta$（样本替代期望）' '\n'
        r'无模型：从轨迹数据直接学习' '\n' r'判据：更新量 < $\varepsilon$ 或轮数上限' '\n' r'把期望换成样本平均（5.6.2）',
        '#f4f6f7', '#85929e', fs=8.9)
    ax.text(2.0, 0.72, '“每尝一口就改配方”', ha='center', va='center', fontsize=8.2, color='#566573')
    ax.text(6.2, 0.72, '“整锅尝明白再改配方”', ha='center', va='center', fontsize=8.2, color='#566573')
    ax.text(10.4, 0.72, '“尝一口、改一口、再尝一口”', ha='center', va='center', fontsize=8.2, color='#566573')

    fig.text(0.5, 0.012,
             '评估不准则改进失据，改进不准则择优失当（5.1.2）；价值迭代“评估一步一改进”、'
             '策略迭代“评估到底再改进”（5.5.3 PDCA），时序差分把“期望”换成“样本平均”（5.6.2）——'
             '三类算法共用一个循环，收敛出口由 γ < 1 保证',
             ha='center', va='center', fontsize=9.0, color='#515a5a')
    fig.subplots_adjust(top=0.90, bottom=0.05)
    fig.savefig(os.path.join(OUT['ch05'], 'fig5-5.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('fig5-5 done')


# =====================================================================
# 图 10-5 AgentLoop：Agent 自主循环（ch10/06-1.6.md 10.6.2）
# v2：节点半径 3.25、能力标注（LLM 推理/工具调用/记忆）移入节点盒、算力支撑条带下移
# =====================================================================
def fig10_5():
    fig, ax = plt.subplots(figsize=(11.6, 9.8))
    ax.set_xlim(-5.9, 5.9)
    ax.set_ylim(-5.6, 5.8)
    ax.set_aspect('equal')
    ax.axis('off')
    fig.suptitle('图 10-5 Agent 自主循环：感知 → 决策 → 行动 → 反馈 → 学习 → 感知\n'
                 '诊疗回路的算法形态——外回路每次诊疗即一圈，内回路平台定期学习（10.6.2 双回路）',
                 fontsize=12.5, y=0.965)

    # 五节点（感知/决策/行动/反馈/学习），顺时针环；学习→感知 为闭合回环
    nodes = [
        (90, '感知', '四诊信息（械者观测）', '', '#d6eaf8', '#1f618d'),
        (18, '决策', '辨证论治', 'LLM 推理', '#fdebd0', '#a04000'),
        (-54, '行动', '处方·医嘱', '工具调用', '#d5f5e3', '#1e8449'),
        (-126, '反馈', '疗效随访', '奖励信号', '#fadbd8', '#943126'),
        (162, '学习', '策略更新', '记忆（经验池·医案）', '#e8daef', '#6c3483'),
    ]
    R = 3.25
    pos = {}
    for deg, name, sub, tag, fc, ec in nodes:
        a = math.radians(deg)
        cx, cy = R * math.cos(a), R * math.sin(a)
        pos[name] = (cx, cy)
        txt = f'{name}\n{sub}' if not tag else f'{name}\n{sub}\n{tag}'
        box(ax, cx, cy, 3.3, 1.3, txt, fc, ec, fs=9.4, bold=True)
    # 顺时针箭头：感知→决策→行动→反馈→学习
    order = ['感知', '决策', '行动', '反馈', '学习']
    for i in range(len(order) - 1):
        (x1, y1), (x2, y2) = pos[order[i]], pos[order[i + 1]]
        arrow(ax, (x1, y1), (x2, y2), color='#1a5276', lw=2.4, rad=-0.22)
    # 学习 → 感知（闭合回环，走左上方大弧）
    (x1, y1), (x2, y2) = pos['学习'], pos['感知']
    arrow(ax, (x1, y1), (x2, y2), color='#c0392b', lw=2.4, rad=-0.55)
    ax.text(-4.1, 3.15, '回到感知（下一轮）', ha='center', va='center', fontsize=8.6,
            color='#c0392b', rotation=38)

    # 中央徽章
    ax.add_patch(Circle((0, 0), 1.42, fc='#fef9e7', ec='#b7950b', lw=2.0, zorder=4))
    ax.text(0, 0.30, 'Agent 自主循环', ha='center', va='center', fontsize=12,
            fontweight='bold', color='#7d6608', zorder=5)
    ax.text(0, -0.18, '诊疗回路', ha='center', va='center', fontsize=9.5,
            color='#7d6608', zorder=5)
    ax.text(0, -0.62, '（优势行动者-评价者）', ha='center', va='center', fontsize=7.5,
            color='#7d6608', zorder=5)

    # 算力支撑条带（下移，含两条上指虚线）
    box(ax, 0, -4.6, 10.8, 0.85,
        '算力支撑：大模型训练与推理 + 强化学习在线更新——足够算力是自主学习与智能涌现的前提（10.7 节）',
        '#f2f3f4', '#616a6b', fs=9.2, tc='#2c3e50')
    arrow(ax, (0.8, -4.17), (1.2, -3.80), color='#616a6b', lw=1.8, ls='--', rad=0.1)
    arrow(ax, (-0.9, -4.17), (-0.9, -3.82), color='#616a6b', lw=1.8, ls='--', rad=0.0)

    fig.text(0.5, 0.012,
             '感知、决策、行动、反馈、学习——五个环节首尾相接构成 Agent 的自主循环（诊疗回路的算法形态）；'
             'LLM 推理负责辨证、工具调用负责执行、记忆负责积累，算力支撑让循环持续运转、智能随数据生长（10.6.2 双回路）',
             ha='center', va='center', fontsize=9.0, color='#515a5a')
    fig.subplots_adjust(top=0.90, bottom=0.04)
    fig.savefig(os.path.join(OUT['ch10'], 'fig10-5.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('fig10-5 done')


# =====================================================================
# 图 10-6 人机闭环：六者与 AI 平台 + CI/CD 进化闭环（ch10/08-1.8.md 10.8.2）
# v2：角色盒外移避开平台（医上/患右上/械右下/药下/规左下/法左上）、
#     交互标注移入角色盒三行、CI/CD 条与回环线分层
# =====================================================================
def fig10_6():
    fig, ax = plt.subplots(figsize=(12.6, 10.4))
    ax.set_xlim(0, 12.6)
    ax.set_ylim(0, 10.6)
    ax.axis('off')
    fig.suptitle('图 10-6 六者与 AI 平台：人机闭环与 CI/CD 进化\n'
                 '医者、患者、药者、械者、规者、法者与平台双向交互；对话→日志→图谱→调优→自动上线→服务——闭环即进化',
                 fontsize=12.5, y=0.972)

    # 中央 AI 平台
    box(ax, 6.3, 5.0, 5.3, 2.25, 'tcmP AI 平台\n大模型 + 强化学习\n（辨证引擎 · 疗效评价 · 质控规则）',
        '#d6eaf8', '#1f618d', fs=11.0, bold=True)

    # 六角色（含双向交互短标注，三行）
    roles = [
        ('医者', '辨证开方', '经验 → 推荐', 6.3, 8.35),
        ('患者', '疗效反馈', '反馈 → 服务', 9.5, 6.85),
        ('械者', '检验数据', '数据 → 工具', 9.6, 3.15),
        ('药者', '审方安全', '审方 → 知识', 6.3, 2.15),
        ('规者', '质控评价', '指标 → 报表', 2.9, 3.15),
        ('法者', '合规留痕', '规则 → 留痕', 3.1, 6.85),
    ]
    for name, sub, inter, x, y in roles:
        box(ax, x, y, 2.35, 1.35, f'{name}\n{sub}\n{inter}', '#f4f6f7', '#85929e',
            fs=8.8, bold=True)

    # 六组双向箭头（角色 ↔ 平台，贴近平台边缘的短双向线）
    def duo(x1, y1, x2, y2):
        arrow(ax, (x1, y1), (x2, y2), color='#1a5276', lw=2.0, rad=0.10)   # 角色→平台
        arrow(ax, (x2, y2), (x1, y1), color='#c0392b', lw=2.0, rad=-0.10)  # 平台→角色

    duo(6.30, 7.70, 6.30, 6.20)    # 医者（纵向）
    duo(8.90, 6.20, 8.45, 6.32)    # 患者（横向）
    duo(9.00, 3.85, 9.25, 3.75)    # 械者（斜向）
    duo(6.30, 2.80, 6.30, 3.80)    # 药者（纵向）
    duo(3.65, 3.85, 3.90, 3.75)    # 规者（斜向）
    duo(3.55, 6.20, 4.00, 6.32)    # 法者（横向）

    # CI/CD 进化闭环（六个盒子 + 回环虚线）
    cd_boxes = [
        ('对话', '人机协同采集需求'),
        ('日志', '行为与疗效留痕'),
        ('图谱', '知识沉淀与更新'),
        ('调优', '奖励与参数调优'),
        ('自动上线', '模型发布与灰度'),
        ('服务', '回到临床服务'),
    ]
    cy = 1.0
    centers = [1.15, 3.15, 5.15, 7.15, 9.15, 11.15]
    for (name, sub), cx in zip(cd_boxes, centers):
        box(ax, cx, cy, 1.75, 0.85, f'{name}\n{sub}', '#fef9e7', '#b7950b', fs=8.2)
    for i in range(5):
        arrow(ax, (centers[i] + 0.88, cy), (centers[i + 1] - 0.88, cy), color='#b7950b', lw=2.2)
    # 回环：服务 → 对话（直线虚线，走盒子下方）
    line(ax, (11.15, 0.30), (1.15, 0.30), color='#b7950b', lw=1.6, ls='--')
    ax.annotate('', xy=(1.30, 0.30), xytext=(11.15, 0.30),
                arrowprops=dict(arrowstyle='-|>', color='#b7950b', lw=1.6, linestyle='--'))
    ax.text(6.3, 0.44, '进化闭环：数据回流驱动模型迭代', ha='center', va='center',
            fontsize=8.4, color='#7d6608', fontweight='bold')

    fig.text(0.5, 0.012,
             '人机闭环：六者供给经验与数据，平台回馈支持与服务；对话→日志→图谱→调优→自动上线→服务，'
             '循环往复——平台在服务中收集数据、在数据中更新共识、在共识中改进服务，正是 10.8.2 节制度化共识机制的工程形态',
             ha='center', va='center', fontsize=9.0, color='#515a5a')
    fig.subplots_adjust(top=0.90, bottom=0.03)
    fig.savefig(os.path.join(OUT['ch10'], 'fig10-6.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('fig10-6 done')


# =====================================================================
# 图 10-7 算力与智能特征：足够算力阈值前后的智能能力曲线（ch10/07-1.7.md 10.7.1）
# =====================================================================
def fig10_7():
    fig, ax = plt.subplots(figsize=(11.6, 8.2))
    x_th = 7.0
    xs = [i / 10 for i in range(121)]           # 0..12
    ys = [1.3 + 7.0 / (1 + math.exp(-1.6 * (x - x_th))) for x in xs]

    # 区域底色：低算力平台期（灰）/ 高算力跃升期（暖）
    ax.axvspan(0, x_th, color='#f4f6f7', zorder=0)
    ax.axvspan(x_th, 12, color='#fef9e7', zorder=0)
    # 阈值虚线
    ax.axvline(x_th, color='#c0392b', lw=2.0, linestyle='--', zorder=3)
    ax.text(x_th, 8.6, '足够算力阈值', ha='center', va='center', fontsize=11.5,
            color='#c0392b', fontweight='bold')
    # 曲线
    ax.plot(xs, ys, color='#1f618d', lw=2.8, zorder=4)
    # 平台期 / 跃升期标注
    ax.text(2.6, 7.1, '低算力平台期\n规则与人工特征工程', ha='center', va='center',
            fontsize=10.5, color='#7f8c8d', linespacing=1.5)
    ax.text(10.2, 7.1, '高算力跃升期\n智能特征涌现', ha='center', va='center',
            fontsize=10.5, color='#b7950b', fontweight='bold', linespacing=1.5)
    # 智能特征标注（曲线上四点）
    feats = [
        (7.7, '自主学习'),
        (8.4, '泛化'),
        (9.1, '自适应'),
        (9.9, '涌现（emergence）'),
    ]
    for fx, lab in feats:
        fy = 1.3 + 7.0 / (1 + math.exp(-1.6 * (fx - x_th)))
        ax.scatter([fx], [fy], s=55, color='#1f618d', zorder=5, edgecolors='white', linewidths=1.0)
        ax.annotate(lab, xy=(fx, fy), xytext=(fx + 0.25, fy + 0.65), fontsize=9.5,
                    color='#1f618d', fontweight='bold',
                    arrowprops=dict(arrowstyle='-', color='#1f618d', lw=1.0))
    # 涌现点（阈值处）
    fy_th = 1.3 + 7.0 / (1 + math.exp(-1.6 * (x_th - x_th)))
    ax.scatter([x_th], [fy_th], s=120, marker='*', color='#c0392b', zorder=6,
               edgecolors='white', linewidths=1.0)
    ax.annotate('量变积累，阈值之后质变——\n整体大于部分之和（10.7 节）',
                xy=(x_th, fy_th), xytext=(3.1, 2.1), fontsize=9.5, color='#c0392b',
                arrowprops=dict(arrowstyle='->', color='#c0392b', lw=1.2))

    # 坐标与刻度（定性）
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 9.4)
    ax.set_xlabel('计算量 / 算力（对数刻度示意）', fontsize=11)
    ax.set_ylabel('智能能力', fontsize=11)
    ax.set_xticks([1.5, 4, 7, 9.5])
    ax.set_xticklabels(['早期规则系统', '统计机器学习', '深度神经网络', '大模型·多模态'], fontsize=9.5)
    ax.set_yticks([])
    for s in ['top', 'right']:
        ax.spines[s].set_visible(False)
    ax.set_title('图 10-7 计算机足够算力下的 AI 智能特征（示意曲线，非实测数据）',
                 fontsize=12.5, pad=12)

    fig.text(0.5, 0.012,
             '低算力平台期只见规则与人工特征，算力越过足够阈值后，自主学习、泛化、自适应与涌现等智能特征质变显现——'
             '恰如强化学习需要 γ < 1 的收缩性才保证收敛（5.2.2）：足够算力是智能特征的前提，足够反馈是学习收敛的前提',
             ha='center', va='center', fontsize=9.0, color='#515a5a')
    fig.subplots_adjust(bottom=0.09)
    fig.savefig(os.path.join(OUT['ch10'], 'fig10-7.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('fig10-7 done')


if __name__ == '__main__':
    assert_numbers()
    fig1_6()
    fig5_5()
    fig10_5()
    fig10_6()
    fig10_7()
    print('== 全部完成：fig1-6 / fig5-5 / fig10-5 / fig10-6 / fig10-7 ==')
