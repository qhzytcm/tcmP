# -*- coding: utf-8 -*-
"""《中医场景强化学习》第10章 费曼图标准重构脚本（图表工程师）

重构依据【费曼图标准】：节点(圆圈/小方块=状态或概念)+连线(直线/箭头/虚线/弧线
=关系/转移/流程)，黑白灰线稿为主，1-2 种低饱和色点缀(灰蓝#4a6785/灰绿#5d7a5e)，
禁止大面积填充色块，极简去装饰，方向明确(箭头)，信息密度高(数值/符号标注在
节点与线上)，聚焦图段延续(ch10 沿用 v2 聚焦：10-2 数轴 40-80、10-7 阈值跃升段)，
中医场景语义保留（10-3/10-6 六者闭环：医患药械规法；tcmP 平台一句话带过）。
输出：figures/ch10/fig10-1.png ~ fig10-7.png（覆盖）
数值口径：10.2.1（基线 60、实际 75→+15 效如桴鼓 / 45→-15 效改其方 / 60→0 效不更方）；
  10.1.1（α_θ=0.01、α_w=0.1）；10.7.1（S 形跃升、阈值 x=70）
"""
import os
import math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Circle, Rectangle, FancyArrowPatch, Polygon

plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'figures', 'ch10')
os.makedirs(OUT, exist_ok=True)

BLACK = '#1a1a1a'
DARK = '#333333'
GRAY = '#666666'
LGRAY = '#999999'
PALE = '#c9c9c9'
BLUE = '#4a6785'    # 蓝（低饱和灰蓝）
GREEN = '#5d7a5e'   # 绿（低饱和灰绿）
RED = '#a0514e'     # 红（低饱和砖红）
ORANGE = '#a86f3f'  # 橙（低饱和土橙）
GOLD = '#a8833a'    # 金（低饱和金黄）
YELLOW = '#b3a24f'  # 黄（低饱和土黄）
PURPLE = '#7a6787'  # 紫（低饱和灰紫）
CYAN = '#5d8a88'    # 青（低饱和青灰）
# 浅底色（区域/背景带/浅底框，均为低饱和淡色）
BG_GRAY = '#e8e8e8'
BG_BLUE = '#e4e8ee'
BG_GREEN = '#e5eae3'
BG_ORANGE = '#f0e6d8'
BG_YELLOW = '#f0ecd9'
BG_RED = '#f0e5e4'
BG_GOLD = '#f0e8d6'


def nbox(ax, cx, cy, w, h, txt, ec=BLACK, fc='white', fs=10.5, lw=1.3,
         tc=BLACK, ls=1.4, bold=False, z=3):
    """节点：圆角小方块（白底、黑/灰描边，细框线）"""
    ax.add_patch(FancyBboxPatch((cx - w / 2, cy - h / 2), w, h,
                                boxstyle='round,pad=0.04',
                                facecolor=fc, edgecolor=ec, lw=lw, zorder=z))
    ax.text(cx, cy, txt, ha='center', va='center', fontsize=fs, color=tc,
            zorder=z + 1, fontweight='bold' if bold else 'normal', linespacing=ls)


def ncirc(ax, cx, cy, r, txt, ec=BLACK, fc='white', fs=10.5, lw=1.3,
          tc=BLACK, ls=1.35, z=3, bold=False):
    """节点：圆圈（白底、黑/灰描边，细框线）"""
    ax.add_patch(Circle((cx, cy), r, facecolor=fc, edgecolor=ec, lw=lw, zorder=z))
    ax.text(cx, cy, txt, ha='center', va='center', fontsize=fs, color=tc,
            zorder=z + 1, fontweight='bold' if bold else 'normal', linespacing=ls)


def ar(ax, x1, y1, x2, y2, color=BLACK, lw=1.4, style='-|>', rad=0.0, z=2):
    """连线：箭头（细线）"""
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle=style, color=color, lw=lw,
                                connectionstyle='arc3,rad=%s' % rad), zorder=z)


# ============================================================
# 图 10-1 行动者-评价者架构（10.1.1）
# 节点：行动者(方)、评价者(方)、环境(方)；连线：状态/动作/奖励环流 + 加权信号粗箭头
# 文字分层：节点内"精进/校准"长句移入图注 c；此处仅留角色名+职责
# ============================================================
def fig10_1():
    fig, ax = plt.subplots(figsize=(8.6, 5.4))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 5.6)
    ax.axis('off')

    nbox(ax, 2.7, 3.6, 3.6, 2.1, '医者\n辨证开方', fs=10.5, bold=True,
         ls=1.4, fc=BG_BLUE, ec=BLUE)
    nbox(ax, 7.3, 3.6, 3.6, 2.1, '规者与药者\n质控·审方', fs=10.5, bold=True,
         ls=1.4, fc=BG_ORANGE, ec=ORANGE)
    # 规者/药者 → 医者：疗效预判（红色粗箭头，图注）
    ar(ax, 5.42, 3.75, 4.58, 3.75, color=RED, lw=2.4)
    ax.text(5.0, 4.25, '疗效预判', ha='center', va='center',
            fontsize=11, color=RED, fontweight='bold')

    nbox(ax, 5.0, 0.85, 7.6, 1.0, '环境（患者与医院场景）', fs=10.5,
         ec=LGRAY, lw=1.2, fc=BG_GRAY)
    # 环流箭头（图注：蓝色细箭头=当前证候与治法方剂环流；橙色细箭头=复诊疗效回传）
    ar(ax, 2.30, 1.47, 2.25, 2.38, color=BLUE, lw=1.5)
    ax.text(1.60, 1.95, '当前证候', ha='center', va='center', fontsize=10,
            color=BLUE)
    ar(ax, 3.55, 1.47, 3.50, 2.38, color=BLUE, lw=1.5)
    ax.text(4.10, 1.95, '治法方剂', ha='center', va='center', fontsize=10,
            color=BLUE)
    ar(ax, 6.90, 1.47, 7.00, 2.38, color=ORANGE, lw=1.5)
    ax.text(7.90, 1.95, '复诊疗效', ha='center', va='center', fontsize=10,
            color=ORANGE)

    fig.savefig(os.path.join(OUT, 'fig10-1.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('fig10-1 done')


# ============================================================
# 图 10-2 优势函数与临床三判（10.2.1）——聚焦数轴 40-80、基线 60 ±15
# 节点：三个判定点(空心圆：75 灰绿 / 45 深灰 / 60 浅灰) + 基线(灰虚线)
# 连线：点→基线的虚线差 + 数轴箭头
# ============================================================
def fig10_2():
    fig, ax = plt.subplots(figsize=(8.8, 5.0))
    ax.set_xlim(0.4, 10.2)
    ax.set_ylim(0.2, 5.3)
    ax.axis('off')

    def px(score):
        return 1.0 + (score - 40) * 0.2

    # 正/负优势区浅底（图注：绿色浅底=正优势区、红色浅底=负优势区）
    ax.axvspan(px(60), px(75), color=BG_GREEN, zorder=0)
    ax.axvspan(px(45), px(60), color=BG_RED, zorder=0)

    # 数轴（灰色横轴，图注）
    ax.annotate('', xy=(9.0, 0.95), xytext=(1.0, 0.95),
                arrowprops=dict(arrowstyle='-|>', color=GRAY, lw=1.4))
    ax.text(9.35, 0.95, '得分', ha='center', va='center', fontsize=10, color=GRAY)
    for s in [40, 50, 60, 70, 80]:
        ax.plot([px(s), px(s)], [0.87, 1.03], color=GRAY, lw=1.1)
        ax.text(px(s), 0.72, str(s), ha='center', va='center', fontsize=9)

    # 基线 60（灰色虚线，图注）
    bx = px(60)
    ax.plot([bx, bx], [1.05, 4.35], color=GRAY, lw=1.6, linestyle='--')
    ax.text(bx + 0.15, 4.42, '预期平均 60 分', ha='left',
            va='center', fontsize=10, color=GRAY)

    # 三个判定点（节点：空心圆；连线：到基线的虚线差；关键数值 +15/-15/0 直接标注）
    # 图注：绿点 75 分=优势+15、红点 45 分=优势-15、灰点 60 分=优势0
    def mark(score, y, col, mfc, txt):
        x = px(score)
        ax.plot([x, x], [1.05, y - 0.18], color=col, lw=1.0, ls=':')
        ax.plot(x, y, 'o', ms=13, mfc=mfc, mec=col, mew=1.8, zorder=5)
        ax.text(x, y + 0.22, txt, ha='center', va='center', fontsize=11,
                color=col, fontweight='bold')

    mark(75, 3.75, GREEN, BG_GREEN, '优于预期 +15\n（效如桴鼓）')
    mark(45, 3.30, RED, BG_RED, '劣于预期 -15\n（效改其方）')
    mark(60, 2.85, GRAY, 'white', '与预期相当 0\n（效不更方）')

    fig.savefig(os.path.join(OUT, 'fig10-2.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('fig10-2 done')


# ============================================================
# 图 10-3 六者协同与幸福闭环（10.6.1）
# 节点：医/患/药/械/规/法（六方框）+ 中央幸福闭环（圆）；连线：外环 + 机制箭头
# ============================================================
def fig10_3():
    fig, ax = plt.subplots(figsize=(8.6, 7.6))
    ax.set_xlim(-1.95, 1.95)
    ax.set_ylim(-1.8, 1.9)
    ax.set_aspect('equal')
    ax.axis('off')

    roles = [
        (0.00, 1.05, '医者', '辨证开方', BG_BLUE, BLUE),
        (1.05, 0.61, '患者', '疗效与依从是最终裁判', BG_GREEN, GREEN),
        (1.05, -0.61, '药者', '审方与调剂', BG_ORANGE, ORANGE),
        (0.00, -1.05, '械者', '影像检验', BG_GRAY, CYAN),
        (-1.05, -0.61, '规者', '质控与流程监督', BG_GRAY, PURPLE),
        (-1.05, 0.61, '法者', '知情同意与责任认定', BG_RED, RED),
    ]
    ring = [(0.00, 1.05), (1.05, 0.61), (1.05, -0.61),
            (0.00, -1.05), (-1.05, -0.61), (-1.05, 0.61)]
    for i in range(len(ring)):
        x1, y1 = ring[i]
        x2, y2 = ring[(i + 1) % len(ring)]
        ax.plot([x1, x2], [y1, y2], color=GRAY, lw=0.8, zorder=1)

    # 中央暖色圆=幸福闭环（无文字，图注 c 指明）
    ncirc(ax, 0, 0, 0.40, '', fs=10.5, bold=True, fc=BG_ORANGE,
          ec=ORANGE, lw=2.0)
    for x, y, name, sub, fcol, ecol in roles:
        nbox(ax, x, y, 1.06, 0.95, name + '\n' + sub, fs=10.5, bold=True,
             ls=1.3, fc=fcol, ec=ecol)

    # 医—患：reward 双向粗箭头（无文字，图注 b 指明）
    ar(ax, 0.30, 0.95, 1.00, 0.75, color=RED, lw=2.4, rad=-0.25)
    ar(ax, 0.28, 0.68, 0.98, 0.50, color=RED, lw=2.4, rad=-0.25)

    def mech(x1, y1, x2, y2, label, color=GRAY, dx=0, dy=0, rad=0.12):
        ar(ax, x1, y1, x2, y2, color=color, lw=1.5, rad=rad)
        ax.text((x1 + x2) / 2 + dx, (y1 + y2) / 2 + dy, label,
                ha='center', va='center', fontsize=10, color=color,
                fontweight='bold')

    # 四机制连线（图注：绿、橙、紫、青细箭头）
    mech(0.25, 0.55, 0.85, -0.30, '责任分离', GREEN, dx=0.15, dy=0.02)
    mech(-0.25, 0.55, -0.85, -0.30, '独立评价', ORANGE, dx=-0.15, dy=0.02)
    mech(-0.20, 0.58, -0.95, 0.62, '全程留痕', PURPLE, dx=-0.05, dy=0.20)
    mech(0.10, 0.52, 0.18, -0.52, '状态观测', CYAN, dx=0.30, dy=0.0, rad=0.25)

    fig.savefig(os.path.join(OUT, 'fig10-3.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('fig10-3 done')


# ============================================================
# 图 10-4 全书三编与共同愿景三重图景（10.8.1/10.8.3）
# 节点：三编方框（上/中/下编）+ 三重图景金字塔（空心三角形）
# 连线：三编间“一脉相承”箭头、金字塔层间向上箭头
# ============================================================
def fig10_4():
    fig, ax = plt.subplots(figsize=(10.0, 6.8))
    ax.set_xlim(0, 11)
    ax.set_ylim(0, 7.2)
    ax.axis('off')

    vols = [
        (5.35, 7.0, '上编 · 提高认知（第 1-3 章）', BG_BLUE),
        (2.85, 4.5, '中编 · 确认信仰（第 4-6 章）', BG_GREEN),
        (0.35, 2.0, '下编 · 追求幸福（第 7-10 章）', BG_ORANGE),
    ]
    for y0, y1, title, fcol in vols:
        nbox(ax, 3.95, (y0 + y1) / 2, 6.9, y1 - y0, '', ec=DARK, lw=1.3,
             fc=fcol)
        ax.text(3.95, (y0 + y1) / 2, title, ha='center', va='center',
                fontsize=11, fontweight='bold', color=BLACK)

    # 三编之间：一脉相承箭头（图注：灰色上行箭头）
    ar(ax, 7.45, 5.30, 7.45, 4.60, color=GRAY, lw=1.2)
    ar(ax, 7.45, 2.80, 7.45, 2.10, color=GRAY, lw=1.2)
    ax.text(7.70, 4.95, '一脉相承', ha='center', va='center', fontsize=10,
            color=GRAY, fontweight='bold', rotation=90)
    ax.text(7.70, 2.45, '一脉相承', ha='center', va='center', fontsize=10,
            color=GRAY, fontweight='bold', rotation=90)

    # 右侧：共同愿景三重图景（空心三角形节点）
    ax.text(9.55, 6.85, '共同愿景三重图景', ha='center', va='center', fontsize=11,
            fontweight='bold', color=BLACK)
    tri = [
        ([(8.2, 3.5), (10.8, 3.5), (10.45, 4.2), (8.55, 4.2)],
         '幸福医院（基层）', DARK),
        ([(8.6, 4.4), (10.4, 4.4), (10.1, 5.1), (8.9, 5.1)],
         '和谐社会（中层）', GRAY),
        ([(9.0, 5.3), (10.0, 5.3), (9.85, 6.0), (9.15, 6.0)],
         '人类命运共同体（顶层）', LGRAY),
    ]
    for pts, label, col in tri:
        ax.add_patch(Polygon(pts, closed=True, fc='white', ec=col, lw=1.2))
        ax.text(9.55, (pts[0][1] + pts[2][1]) / 2, label, ha='center',
                va='center', fontsize=10, color=col, fontweight='bold')
    ar(ax, 9.55, 4.28, 9.55, 4.38, color=LGRAY, lw=1.0)
    ar(ax, 9.55, 5.18, 9.55, 5.28, color=LGRAY, lw=1.0)

    fig.savefig(os.path.join(OUT, 'fig10-4.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('fig10-4 done')


# ============================================================
# 图 10-5 Agent 自主循环（10.6.2）：感知→决策→行动→反馈→学习 五环
# 节点：五个方框（白底黑框）；连线：环形箭头（灰蓝）+ 中心说明
# ============================================================
def fig10_5():
    fig, ax = plt.subplots(figsize=(8.8, 6.2))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6.6)
    ax.axis('off')

    nodes = [
        (5.0, 5.4, '感知', '四诊信息与械者观测'),
        (8.2, 3.5, '决策', '辨证论治，LLM 推理'),
        (6.6, 1.2, '行动', '开具处方与医嘱，工具调用'),
        (3.4, 1.2, '反馈', '疗效随访与依从观察'),
        (1.8, 3.5, '学习', '经验沉淀与医案整理'),
    ]
    for i in range(len(nodes)):
        x1, y1 = nodes[i][0], nodes[i][1]
        x2, y2 = nodes[(i + 1) % len(nodes)][0], nodes[(i + 1) % len(nodes)][1]
        ar(ax, x1, y1, x2, y2, color=DARK, lw=1.8, rad=0.18)
    for x, y, name, sub in nodes:
        nbox(ax, x, y, 2.2, 1.35, name + '\n\n' + sub, fs=10.5, bold=True, ls=1.3)

    ax.text(5.0, 2.65, '每一次诊疗即一圈', ha='center', va='center', fontsize=11,
            fontweight='bold', color=DARK)
    fig.savefig(os.path.join(OUT, 'fig10-5.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('fig10-5 done')


# ============================================================
# 图 10-6 六者与 AI 平台：人机闭环 + CI/CD 进化（10.8.2）
# 节点：中央 tcmP 平台（一句话带过）+ 六者环绕 + 底部 CI/CD 链
# 连线：六方↔平台双向箭头（浅灰）、CI/CD 链箭头（灰绿）
# ============================================================
def fig10_6():
    fig, ax = plt.subplots(figsize=(9.0, 7.6))
    ax.set_xlim(0, 10)
    ax.set_ylim(-1.4, 8.0)
    ax.axis('off')

    # 中央 tcmP 平台（中央蓝框，图注）
    nbox(ax, 5.0, 5.0, 3.0, 1.6, 'tcmP AI 平台', fs=11, bold=True,
         ec=BLUE, lw=1.6, fc=BG_BLUE)

    actors = [
        (5.0, 7.1, '医者', '辨证经验', BG_BLUE, BLUE),
        (8.4, 5.6, '患者', '疗效依从', BG_GREEN, GREEN),
        (8.4, 2.5, '药者', '审方数据', BG_ORANGE, ORANGE),
        (6.2, 1.2, '械者', '检验数据', BG_GRAY, CYAN),
        (3.8, 1.2, '规者', '质控指标', BG_GRAY, PURPLE),
        (1.6, 2.5, '法者', '合规规则', BG_RED, RED),
    ]
    for x, y, name, sub, fcol, ecol in actors:
        ar(ax, 5.0, 5.2, x, y, color=LGRAY, lw=1.2, style='<|-|>', rad=0.06)
        nbox(ax, x, y, 1.8, 1.15, name + '\n' + sub, fs=10, bold=True, ls=1.25,
             fc=fcol, ec=ecol)

    # 底部 CI/CD 进化闭环（金色闭环链，图注；六个环节盒无字、序列由一条标注承担）
    steps = ['对话', '日志', '图谱', '调优', '自动上线', '服务']
    xs = [1.2, 2.85, 4.5, 6.15, 7.8, 9.45]
    for i in range(len(xs) - 1):
        ar(ax, xs[i] + 0.55, -0.5, xs[i + 1] - 0.55, -0.5, color=GOLD, lw=1.5)
    for x, st in zip(xs, steps):
        nbox(ax, x, -0.5, 1.1, 0.5, '', fs=10, bold=True, ec=GOLD, lw=1.2)
    ar(ax, 9.7, -0.5, 1.2, -0.5, color=GOLD, lw=1.5, rad=-0.30)
    ax.text(5.0, 0.18, 'CI/CD：对话→日志→图谱→调优→自动上线→服务→对话',
            ha='center', va='center', fontsize=10, color=GOLD, fontweight='bold')

    fig.savefig(os.path.join(OUT, 'fig10-6.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('fig10-6 done')


# ============================================================
# 图 10-7 算力与智能特征（10.7.1）——聚焦“足够算力阈值”跃升段 x∈[40,100]
# 曲线：S 形（灰蓝实线）；关键点：(70,0.5) 阈值点（空心圆+数值）
# ============================================================
def fig10_7():
    fig, ax = plt.subplots(figsize=(8.8, 5.0))
    ax.set_xlim(36, 106)
    ax.set_ylim(-0.45, 1.18)
    ax.axis('off')

    xs = [x for x in range(38, 102, 1)]
    ys = [1.0 / (1.0 + math.exp(-(x - 70) / 4.0)) for x in xs]

    # 区域浅底（图注：阈值左侧浅灰底=平台期、右侧浅黄底=跃升期）
    ax.axvspan(38, 70, color=BG_GRAY, zorder=0)
    ax.axvspan(70, 100, color=BG_YELLOW, zorder=0)

    ax.plot(xs, ys, color=BLUE, lw=2.4)

    # 阈值竖虚线（灰色虚线，图注；关键数值锚点 0.5）
    ax.plot([70, 70], [-0.06, 1.06], color=GRAY, lw=1.6, linestyle='--')
    ax.text(70, 1.12, '“足够算力阈值”', ha='center', va='center', fontsize=11,
            color=GRAY, fontweight='bold')
    ax.plot(70, 0.5, 'o', ms=8, mfc='white', mec=GRAY, mew=1.6, zorder=5)
    ax.text(71.5, 0.42, '0.5', fontsize=11, color=GRAY, fontweight='bold')

    # 区域标注（短词；阶段特征移入图注 c）
    ax.text(54, 0.22, '平台期', ha='center', va='center',
            fontsize=10, color=GRAY)
    ax.text(86, 0.88, '跃升期', ha='center', va='center',
            fontsize=10, color=GRAY, fontweight='bold')

    # 数轴（对数刻度示意，只标数量级）
    ax.annotate('', xy=(98, -0.06), xytext=(40, -0.06),
                arrowprops=dict(arrowstyle='-|>', color=BLACK, lw=1.3))
    ax.text(99.0, -0.10, '计算量/算力（对数示意）', ha='center', va='center',
            fontsize=11)
    for x in [40, 55, 70, 85, 100]:
        ax.plot([x, x], [-0.09, -0.03], color=BLACK, lw=1.1)
        ax.text(x, -0.18, str(x), ha='center', va='center', fontsize=9)
    ax.annotate('', xy=(38.5, 1.0), xytext=(38.5, -0.02),
                arrowprops=dict(arrowstyle='-|>', color=BLACK, lw=1.3))
    ax.text(37.2, 0.52, '智能能力', ha='center', va='center', fontsize=11,
            rotation=90)
    for y in [0.0, 0.5, 1.0]:
        ax.plot([38.0, 38.6], [y, y], color=BLACK, lw=1.1)
        ax.text(37.6, y, '%g' % y, ha='right', va='center', fontsize=9)

    fig.savefig(os.path.join(OUT, 'fig10-7.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('fig10-7 done')


if __name__ == '__main__':
    fig10_1()
    fig10_2()
    fig10_3()
    fig10_4()
    fig10_5()
    fig10_6()
    fig10_7()
    print('ALL DONE ->', OUT)
