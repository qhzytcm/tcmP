# -*- coding: utf-8 -*-
"""《中医场景强化学习》第10章 核心图生成脚本
生成：fig10-1 行动者-评价者架构 / fig10-2 优势函数与临床三判
      fig10-3 六者协同与幸福闭环 / fig10-4 全书三编与共同愿景
输出：drafts/cmrl/figures/ch10/*.png
规范：SimHei + axes.unicode_minus=False，dpi=200，与 figures/ch01/ 同风格。
字形坑：数学符号一律用 mathtext（$...$）；负号用 ASCII '-'；不用 U+2081-2084 下标。
数值一致性：脚本内 assert 校验正文 10.1-10.5 节关键数值。
"""
import os
import math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Circle, Rectangle, FancyArrowPatch, Polygon
from matplotlib.lines import Line2D

plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'figures', 'ch10')
os.makedirs(OUT, exist_ok=True)

# ---------- 数值一致性自检（与正文 10.1-10.5 节 / check_ch10.py 口径一致） ----------
def assert_numbers():
    pa1 = math.exp(0.5) / (math.exp(0.5) + math.exp(0.3))   # softmax π(a1)
    pa2 = math.exp(0.3) / (math.exp(0.5) + math.exp(0.3))   # softmax π(a2)
    assert abs(pa1 - 0.5498) < 1e-4 and abs(pa2 - 0.4502) < 1e-4, (pa1, pa2)
    assert abs(pa1 + pa2 - 1.0) < 1e-6
    assert abs(0.8 / 0.5 - 1.6) < 1e-9                       # 10.4.2 ρ(a1)
    assert abs(0.2 / 0.5 - 0.4) < 1e-9                       # 10.4.2 ρ(a2)
    assert abs(pa2 / 0.5 - 0.9004) < 1e-4                    # 10.4.2 修正例
    assert abs(0.9 / 0.5 - 1.8) < 1e-9                       # 10.4.2 放大例
    assert abs(1 + 0.9 * 10 - 10 - 0.0) < 1e-9               # 10.2.3 δ_t=0 例
    assert 75 - 60 == 15 and 45 - 60 == -15 and 60 - 60 == 0  # 10.2.1 优势例
    assert abs((0.1 / 0.01) - 10.0) < 1e-9                   # 10.2.2 α_w/α_θ
    assert abs(0.192 / 0.24 - 0.8) < 1e-9                    # 10.5.1 自然梯度例
    print('[assert] 10.1-10.5 关键数值全部一致 OK')


def fig10_1():
    """图 10-1 做事的与评事的：行动者-评价者架构（10.1.1 节）"""
    fig, ax = plt.subplots(figsize=(9.6, 6.6))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6.8)
    ax.axis('off')
    ax.set_title('图 10-1 做事的与评事的：行动者-评价者架构\n'
                 '决策与评价分离：行动者负责做什么，评价者负责评估好不好',
                 fontsize=12.5, pad=14)

    # 左：行动者（浅蓝）
    ax.add_patch(FancyBboxPatch((0.7, 3.0), 3.6, 2.7, boxstyle='round,pad=0.08',
                                fc='#d6eaf8', ec='#1f618d', lw=1.8))
    ax.text(2.5, 5.35, '行动者（actor）', ha='center', va='center',
            fontsize=12.5, fontweight='bold', color='#1f618d')
    ax.text(2.5, 4.85, '策略参数 $\\theta$：决定做什么', ha='center', va='center', fontsize=10.5)
    ax.text(2.5, 4.15, '策略更新', ha='center', va='center', fontsize=10.5, color='#424949')
    ax.text(2.5, 3.55, r'$\theta \leftarrow \theta + \alpha_\theta \nabla \ln \pi(a|s,\theta)\, \hat{q}(s,a,w)$',
            ha='center', va='center', fontsize=10.5)

    # 右：评价者（浅橙）
    ax.add_patch(FancyBboxPatch((5.7, 3.0), 3.6, 2.7, boxstyle='round,pad=0.08',
                                fc='#fdebd0', ec='#a04000', lw=1.8))
    ax.text(7.5, 5.35, '评价者（critic）', ha='center', va='center',
            fontsize=12.5, fontweight='bold', color='#a04000')
    ax.text(7.5, 4.85, '价值参数 $w$：评估做得好不好', ha='center', va='center', fontsize=10.5)
    ax.text(7.5, 4.15, '价值更新（Sarsa 式）', ha='center', va='center', fontsize=10.5, color='#424949')
    ax.text(7.5, 3.55, r'$w \leftarrow w + \alpha_w \delta_t\, \nabla_w \hat{q}(s,a,w)$',
            ha='center', va='center', fontsize=10.5)

    # 中央粗箭头：评价者 → 行动者（加权信号）
    ax.annotate('', xy=(4.25, 4.35), xytext=(5.85, 4.35),
                arrowprops=dict(arrowstyle='-|>', color='#c0392b', lw=3.2))
    ax.text(5.05, 4.62, '加权信号 $\\hat{q}(s,a,w)$', ha='center', va='center',
            fontsize=10.5, color='#c0392b', fontweight='bold')

    # 底部环境框（浅灰）
    ax.add_patch(FancyBboxPatch((1.2, 0.35), 7.6, 1.5, boxstyle='round,pad=0.08',
                                fc='#f2f3f4', ec='#616a6b', lw=1.5))
    ax.text(5.0, 1.52, '环境（患者与医院场景）', ha='center', va='center',
            fontsize=11.5, fontweight='bold', color='#424949')
    ax.text(5.0, 1.05, '状态 $s_t$（四诊信息）→ 动作 $a_t$（治法方剂）→ 奖励 $r_{t+1}$（疗效反馈）',
            ha='center', va='center', fontsize=10.5)

    # 环流箭头：环境 ↔ 行动者、环境 → 评价者
    ax.annotate('', xy=(1.9, 3.0), xytext=(1.6, 1.85),
                arrowprops=dict(arrowstyle='-|>', color='#1a5276', lw=2.2))
    ax.text(1.05, 2.42, '状态 $s_t$', ha='center', va='center', fontsize=9.5, color='#1a5276')
    ax.annotate('', xy=(4.3, 1.85), xytext=(4.05, 3.0),
                arrowprops=dict(arrowstyle='-|>', color='#1a5276', lw=2.2))
    ax.text(5.0, 2.42, '动作 $a_t$', ha='center', va='center', fontsize=9.5, color='#1a5276')
    ax.annotate('', xy=(7.3, 3.0), xytext=(7.0, 1.85),
                arrowprops=dict(arrowstyle='-|>', color='#935116', lw=2.2))
    ax.text(8.55, 2.42, '奖励 $r_{t+1}$、状态 $s_{t+1}$', ha='center', va='center',
            fontsize=9.5, color='#935116')

    # 中医对照栏
    ax.text(5.0, 0.10, '中医对照：医者（行动者）辨证开方　/　规者、药者（评价者）质控审方',
            ha='center', va='center', fontsize=10.5, color='#1a5276')
    fig.text(0.5, 0.015, '开方的人不管评方，评方的人不插手开方——行动者只管演好戏，评价者只管说真话，二者都不越位、不缺位',
             ha='center', va='center', fontsize=10, color='#515a5a')

    fig.savefig(os.path.join(OUT, 'fig10-1.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('fig10-1 done')


def fig10_2():
    """图 10-2 相对平均水平的评价：优势函数与临床三判（10.2.1 节）"""
    fig, ax = plt.subplots(figsize=(10.2, 6.4))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6.6)
    ax.axis('off')
    ax.set_title('图 10-2 相对平均水平的评价：优势函数与临床三判\n'
                 r'$A_\pi(s,a) = q_\pi(s,a) - v_\pi(s)$：实际得分 - 预期基线 = 比平均水平好多少',
                 fontsize=12.5, pad=14)

    # 主图区数轴：0-100
    ax.annotate('', xy=(9.6, 3.6), xytext=(0.8, 3.6),
                arrowprops=dict(arrowstyle='-|>', color='#333333', lw=1.6))
    ax.text(9.75, 3.6, '得分', ha='center', va='center', fontsize=10)
    for x, lab in [(0, '0'), (20, '20'), (40, '40'), (60, '60'), (80, '80'), (100, '100')]:
        ax.plot([x * 0.086 + 0.8, x * 0.086 + 0.8], [3.52, 3.68], color='#333333', lw=1.2)
        ax.text(x * 0.086 + 0.8, 3.38, lab, ha='center', va='center', fontsize=9)

    # 基线 60：灰色虚线
    bx = 60 * 0.086 + 0.8
    ax.plot([bx, bx], [0.8, 3.5], color='#7f8c8d', lw=2.0, linestyle='--')
    ax.text(bx + 0.12, 3.05, '基线 $v(s) = 60$（预期平均水平）', ha='left', va='center',
            fontsize=10, color='#7f8c8d')

    def mark(x, y, color, label):
        px = x * 0.086 + 0.8
        ax.plot([px, px], [0.8, y - 0.25], color=color, lw=1.4, linestyle=':')
        ax.scatter([px], [y], s=130, color=color, zorder=5, edgecolors='white', linewidths=1.2)
        ax.text(px, y + 0.12, label, ha='center', va='center', fontsize=10, color=color)

    mark(75, 4.55, '#1e8449', '实际 75 分 → 优势 +15\n效如桴鼓：显著优于预期\n值得强化沿用')
    mark(45, 4.05, '#b03a2e', '实际 45 分 → 优势 -15\n效改其方：劣于预期\n应调整治法')
    mark(60, 3.55, '#515a5a', '实际 60 分 → 优势 0\n效不更方：与预期相当\n维持原方')
    # 三个优势区间箭头
    ax.annotate('', xy=(75 * 0.086 + 0.8, 4.55), xytext=(bx, 4.55),
                arrowprops=dict(arrowstyle='-|>', color='#1e8449', lw=1.8))
    ax.annotate('', xy=(45 * 0.086 + 0.8, 4.05), xytext=(bx, 4.05),
                arrowprops=dict(arrowstyle='-|>', color='#b03a2e', lw=1.8))

    # 两张患者卡片
    ax.add_patch(FancyBboxPatch((0.55, 1.0), 4.1, 1.55, boxstyle='round,pad=0.08',
                                fc='#eafaf1', ec='#1e8449', lw=1.5))
    ax.text(2.6, 2.18, '患者甲：药后症减、脉和', ha='center', va='center', fontsize=10.5,
            color='#1e8449', fontweight='bold')
    ax.text(2.6, 1.72, '→ 正优势（效如桴鼓）', ha='center', va='center', fontsize=10.5, color='#1e8449')
    ax.text(2.6, 1.28, '同一首方剂，同一证候相近', ha='center', va='center', fontsize=9, color='#515a5a')

    ax.add_patch(FancyBboxPatch((5.35, 1.0), 4.1, 1.55, boxstyle='round,pad=0.08',
                                fc='#fdedec', ec='#b03a2e', lw=1.5))
    ax.text(7.4, 2.18, '患者乙：药后如故、纳差', ha='center', va='center', fontsize=10.5,
            color='#b03a2e', fontweight='bold')
    ax.text(7.4, 1.72, '→ 负优势（效改其方）', ha='center', va='center', fontsize=10.5, color='#b03a2e')
    ax.text(7.4, 1.28, '评价截然不同', ha='center', va='center', fontsize=9, color='#515a5a')

    ax.text(5.0, 0.68, '辨证论治个体化评价的数学化表达', ha='center', va='center',
            fontsize=9.5, color='#515a5a')
    fig.text(0.5, 0.015, '评价一个治法，不能脱离患者的具体基线——同一首补中益气汤，对素体虚弱者可能效如桴鼓，对壮实外感者则可能火上浇油',
             ha='center', va='center', fontsize=10, color='#515a5a')

    fig.savefig(os.path.join(OUT, 'fig10-2.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('fig10-2 done')


def fig10_3():
    """图 10-3 医、患、药、械、规、法：六者协同与幸福闭环（10.6.1 节）"""
    fig, ax = plt.subplots(figsize=(10.0, 9.2))
    ax.set_xlim(-1.55, 1.55)
    ax.set_ylim(-1.45, 1.55)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title('图 10-3 医、患、药、械、规、法：六者协同与幸福闭环',
                 fontsize=13, pad=16)

    # 六角色布局：医上 / 患右下 / 药下右 / 械下左 / 规左上 / 法上左
    roles = [
        (0.00, 1.18, '医者（行动者）', '辨证开方', '#d6eaf8', '#1f618d'),
        (0.98, 0.42, '患者（环境奖励信号）', '疗效与依从\n是最终裁判', '#fadbd8', '#943126'),
        (0.62, -0.82, '药者（安全评价）', '审方与调剂\n处方守门人', '#d5f5e3', '#1e8449'),
        (-0.62, -0.86, '械者（状态观测）', '影像检验\n诊疗的眼睛与手脚', '#d1f2eb', '#148f77'),
        (-1.00, 0.20, '规者（评价）', '质控与流程监督', '#fdebd0', '#a04000'),
        (-0.85, 0.78, '法者（轨迹留痕）', '知情同意\n责任认定', '#e8daef', '#6c3483'),
    ]
    # 相邻角色六边形环线（环环相扣）
    ring = [(0.00, 1.18), (0.98, 0.42), (0.62, -0.82), (-0.62, -0.86), (-1.00, 0.20), (-0.85, 0.78)]
    for i in range(len(ring)):
        x1, y1 = ring[i]
        x2, y2 = ring[(i + 1) % len(ring)]
        ax.plot([x1, x2], [y1, y2], color='#b2babb', lw=1.0, linestyle='-', alpha=0.7, zorder=1)

    # 中心暖色圆：幸福闭环
    ax.add_patch(Circle((0, 0), 0.46, fc='#fdebd0', ec='#c0392b', lw=2.0, zorder=4))
    ax.text(0, 0.12, '幸福闭环', ha='center', va='center', fontsize=13,
            fontweight='bold', color='#c0392b', zorder=5)
    ax.text(0, -0.22, '健康共同体', ha='center', va='center', fontsize=10,
            color='#c0392b', zorder=5)

    for x, y, name, sub, fc, ec in roles:
        ax.add_patch(FancyBboxPatch((x - 0.62, y - 0.52), 1.24, 1.04,
                                    boxstyle='round,pad=0.06', fc=fc, ec=ec, lw=1.6, zorder=3))
        ax.text(x, y + 0.22, name, ha='center', va='center', fontsize=10.5,
                fontweight='bold', color=ec, zorder=4)
        ax.text(x, y - 0.15, sub, ha='center', va='center', fontsize=8.5,
                color='#2c3e50', zorder=4, linespacing=1.25)

    # 四条机制连线（医者为中心的加粗标注）
    def mech_line(x1, y1, x2, y2, label, color, dx=0, dy=0, fs=8.5):
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle='-|>', color=color, lw=2.2,
                                    connectionstyle='arc3,rad=0.12'), zorder=2)
        mx, my = (x1 + x2) / 2 + dx, (y1 + y2) / 2 + dy
        ax.text(mx, my, label, ha='center', va='center', fontsize=fs,
                color=color, fontweight='bold', zorder=4)

    # 医—患：双向粗箭头（reward 回路）
    ax.annotate('', xy=(0.98, 0.42), xytext=(0.12, 0.75),
                arrowprops=dict(arrowstyle='-|>', color='#c0392b', lw=3.0,
                                connectionstyle='arc3,rad=-0.25'), zorder=2)
    ax.annotate('', xy=(0.12, 0.85), xytext=(0.98, 0.55),
                arrowprops=dict(arrowstyle='-|>', color='#c0392b', lw=3.0,
                                connectionstyle='arc3,rad=-0.25'), zorder=2)
    ax.text(0.68, 0.98, 'reward：信任→依从→疗效→信任', ha='center', va='center',
            fontsize=8.8, color='#c0392b', fontweight='bold', zorder=4)
    mech_line(0.00, 0.66, 0.62, -0.30, '责任分离', '#1e8449', dx=0.30, dy=0.05)   # 医—药
    mech_line(-0.10, 0.68, -1.00, 0.30, '独立评价', '#a04000', dx=-0.30, dy=0.05)  # 医—规
    mech_line(-0.10, 0.68, -0.85, 0.78, '全程留痕', '#6c3483', dx=-0.30, dy=0.20)  # 医—法
    mech_line(0.00, 0.66, -0.62, -0.34, '状态观测', '#148f77', dx=0.30, dy=-0.25)  # 医—械

    # 右下角小图例：四大机制
    ax.add_patch(FancyBboxPatch((0.92, -1.38), 0.62, 0.46, boxstyle='round,pad=0.04',
                                fc='white', ec='#b2babb', lw=1.0))
    ax.text(1.23, -1.26, '四大机制', ha='center', va='center', fontsize=8, fontweight='bold')
    ax.text(1.23, -1.44, '奖励共识·回路透明\n责任分离·全程留痕', ha='center', va='center',
            fontsize=7.2, color='#515a5a')

    fig.text(0.5, 0.012, '和而不同：六者在差异中互补、在互补中平衡——如同五味调和成佳肴；六方环环相扣，每一次诊疗都是一个完整的闭环周期',
             ha='center', va='center', fontsize=10, color='#515a5a')

    fig.savefig(os.path.join(OUT, 'fig10-3.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('fig10-3 done')


def fig10_4():
    """图 10-4 从网格世界到六者协同：全书三编与共同愿景（10.8.3 节）"""
    fig, ax = plt.subplots(figsize=(11.2, 7.6))
    ax.set_xlim(0, 11)
    ax.set_ylim(0, 7.8)
    ax.axis('off')
    ax.set_title('图 10-4 从网格世界到六者协同：全书三编与共同愿景',
                 fontsize=13, pad=14)

    # 左栏三编横条
    vols = [
        (5.2, 6.9, '#d6eaf8', '#1f618d', '上编 · 提高认知（第 1–3 章）',
         '第1章 认知的起点 → 第2章 认知的结构 → 第3章 认知的深化',
         '核心：状态观测 · 健康建模 · 统计学习', '问题：AI 如何认识中医医院？'),
        (2.7, 4.4, '#d5f5e3', '#1e8449', '中编 · 确认信仰（第 4–6 章）',
         '第4章 信仰的量化 → 第5章 信仰的择优 → 第6章 信仰的检验',
         '核心：价值量化 · 辨证择优 · 临床检验', '问题：中医药的疗效如何确认？'),
        (0.3, 2.0, '#fdebd0', '#a04000', '下编 · 追求幸福（第 7–10 章）',
         '第7章 幸福的表达 → 第8章 幸福的实现 → 第9章 幸福的探索 → 第10章 幸福的闭环',
         '核心：个人定位 · 场景生存最适度 · 环境共荣最适度', '问题：为了什么而优化？'),
    ]
    for y0, y1, fc, ec, title, chapters, core, question in vols:
        ax.add_patch(FancyBboxPatch((0.5, y0), 7.3, y1 - y0, boxstyle='round,pad=0.08',
                                    fc=fc, ec=ec, lw=1.8))
        ax.text(4.15, y1 - 0.34, title, ha='center', va='center', fontsize=12,
                fontweight='bold', color=ec)
        ax.text(4.15, (y0 + y1) / 2 - 0.02, chapters, ha='center', va='center',
                fontsize=9.5, color='#2c3e50')
        ax.text(4.15, (y0 + y1) / 2 - 0.52, core, ha='center', va='center',
                fontsize=10, color='#2c3e50', fontweight='bold')
        ax.text(4.15, y0 + 0.26, question, ha='center', va='center', fontsize=9.5,
                color=ec, fontstyle='italic')

    # 三编之间：一脉相承箭头
    ax.annotate('', xy=(8.05, 6.8), xytext=(8.05, 5.2),
                arrowprops=dict(arrowstyle='-|>', color='#7f8c8d', lw=1.6))
    ax.annotate('', xy=(8.05, 4.35), xytext=(8.05, 2.75),
                arrowprops=dict(arrowstyle='-|>', color='#7f8c8d', lw=1.6))
    ax.text(8.28, 6.0, '一脉相承', ha='center', va='center', fontsize=9.5,
            color='#7f8c8d', fontweight='bold', rotation=90)
    ax.text(8.28, 3.55, '一脉相承', ha='center', va='center', fontsize=9.5,
            color='#7f8c8d', fontweight='bold', rotation=90)

    # 右侧三重图景金字塔（幸福医院→和谐社会→人类命运共同体）
    ax.text(9.6, 7.35, '共同愿景三重图景', ha='center', va='center', fontsize=10.5,
            fontweight='bold', color='#2c3e50')
    # 底：幸福医院（最宽）
    ax.add_patch(Polygon([(8.35, 4.55), (10.85, 4.55), (10.55, 5.15), (8.65, 5.15)],
                         closed=True, fc='#fadbd8', ec='#943126', lw=1.4))
    ax.text(9.6, 4.85, '幸福医院（基层）', ha='center', va='center', fontsize=9.5,
            color='#943126', fontweight='bold')
    # 中：和谐社会
    ax.add_patch(Polygon([(8.75, 5.35), (10.45, 5.35), (10.2, 5.95), (9.0, 5.95)],
                         closed=True, fc='#d5f5e3', ec='#1e8449', lw=1.4))
    ax.text(9.6, 5.65, '和谐社会（中层）', ha='center', va='center', fontsize=9.5,
            color='#1e8449', fontweight='bold')
    # 顶：人类命运共同体
    ax.add_patch(Polygon([(9.15, 6.15), (10.05, 6.15), (9.9, 6.75), (9.3, 6.75)],
                         closed=True, fc='#d6eaf8', ec='#1f618d', lw=1.4))
    ax.text(9.6, 6.45, '人类命运\n共同体（顶层）', ha='center', va='center', fontsize=8.5,
            color='#1f618d', fontweight='bold')
    ax.text(9.6, 4.18, '同一愿景的不同尺度投影', ha='center', va='center', fontsize=8.5,
            color='#515a5a')

    # 底部全书一句话横幅
    ax.add_patch(FancyBboxPatch((0.5, 0.42), 10.0, 0.62, boxstyle='round,pad=0.08',
                                fc='#fef9e7', ec='#b7950b', lw=1.5))
    ax.text(5.5, 0.73, '提高认知让 AI 学会看病，确认信仰让疗效可以量化，追求幸福让优化指向适度。',
            ha='center', va='center', fontsize=11, color='#7d6608', fontweight='bold')

    fig.savefig(os.path.join(OUT, 'fig10-4.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('fig10-4 done')


if __name__ == '__main__':
    assert_numbers()
    fig10_1()
    fig10_2()
    fig10_3()
    fig10_4()
    print('== 全部完成：figures/ch10/fig10-1.png ~ fig10-4.png ==')
