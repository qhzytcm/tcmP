# -*- coding: utf-8 -*-
"""《中医场景强化学习》第7章 费曼图标准重构脚本（图表工程师）

重构依据【费曼图标准】：
  ① 主体结构——节点(圆圈/小方块=状态或概念) + 连线(直线/箭头/虚线/波浪线=关系/转移/流程)
  ② 黑白灰线稿为主，1-2 种低饱和色点缀(灰蓝#4a6785/灰绿#5d7a5e)，禁止大面积填充色块
  ③ 极简去装饰(去大标题、去背景色带、去冗余旁注)
  ④ 方向明确(流程/反馈方向一律用箭头)
  ⑤ 信息密度高(数值/符号直接标注在节点与线上)
  ⑥聚焦图段延续(ch07 沿用 v2 聚焦数轴：7-2 x∈[0.5,1.5]、7-4 γ∈[0,1])
  ⑦ 中医场景语义保留
输出：figures/ch07/fig7-1.png ~ fig7-4.png（覆盖）
数值口径：正文 7.1.1/7.1.2（0.76 加权算例、随访三分数）、7.2.2（收缩压 90-130、
  步数 6000-10000/>15000）、7.3.1（退休教师画像）、7.5.1（甲(6,3,1) 总10 < 乙(1,3,9) 总13、γ*≈0.79）
"""
import os
import math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Circle
from matplotlib.lines import Line2D

plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ch07')
os.makedirs(OUT, exist_ok=True)

# ---- 费曼调色板：黑白灰 + 图注对齐的低饱和彩色 ----
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


def ar(ax, x1, y1, x2, y2, color=BLACK, lw=1.4, style='-|>', rad=0.0, ls='-', z=2):
    """连线：箭头（细线）"""
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle=style, color=color, lw=lw,
                                linestyle=ls, connectionstyle='arc3,rad=%s' % rad),
                zorder=z)


# ============================================================
# 图 7-1 奖励函数设计示意：输入→函数→输出 + 关键锚点 0.76 + 随访三分数
# 节点：状态s(圆)、动作a(圆)、奖励函数r(s,a)(方)、评分(圆)、
#       综合健康评分0.76(圆)、三分数卡(方)
# 连线：s→r、a→r（输入）、r→评分（输出）、评分→0.76（呼应）
# 文字分层：加权算例行、旁注句全部移入图注（图注①-④已含算式 0.76）
# ============================================================
def fig7_1():
    fig, ax = plt.subplots(figsize=(11.6, 6.2))
    ax.set_xlim(0, 11.6)
    ax.set_ylim(0, 6.4)
    ax.axis('off')

    # -- 左：输入-函数-输出（核心映射）--
    ncirc(ax, 1.05, 4.85, 0.72, '证候\n四诊信息', fs=10.5)
    ncirc(ax, 1.05, 2.75, 0.72, '治法方剂', fs=10.5)
    nbox(ax, 3.35, 3.80, 2.30, 2.00, '疗效打分\nr(s, a)', fs=11, bold=True)
    ar(ax, 1.79, 4.70, 2.36, 4.40, lw=1.4)
    ar(ax, 1.79, 2.90, 2.36, 3.20, lw=1.4)
    ncirc(ax, 5.95, 3.80, 0.72, '评分\n（一个数）', fs=10.5, ec=DARK)
    ar(ax, 4.62, 3.80, 5.20, 3.80, lw=1.6)

    # -- 中右：关键数值锚点 0.76（正文 7.1.2 加权算例结果，图注④）--
    ar(ax, 6.75, 3.80, 7.90, 4.05, lw=1.2, color=GRAY)
    ncirc(ax, 8.90, 4.15, 0.95, '综合健康评分\n0.76', fs=11, bold=True,
          ec=DARK, lw=1.8)

    # -- 下右：随访三分数（尺子的刻度，正文 7.1.1；图注②）--
    cards = [
        ('+1', '表解身和', DARK),
        ('+0.5', '余邪未清', GRAY),
        ('-0.3', '汗出太过', LGRAY),
    ]
    for i, (score, desc, ec) in enumerate(cards):
        cx = 7.30 + i * 1.60
        nbox(ax, cx, 1.30, 1.50, 1.10, score + '\n' + desc, fs=10.5,
             ec=ec, lw=1.3, bold=(i == 0))

    fig.savefig(os.path.join(OUT, 'fig7-1.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('fig7-1 done')


# ============================================================
# 图 7-3 四个最适度雷达图：生理/心理/社会/环境——均衡 vs 失衡（正文 7.3.1）
# 节点：四维轴线顶点（失衡=红色多边形、均衡=绿色多边形、及格线=灰色虚线）
# 文字分层：四维画像旁注与目标向量句移入图注；图内仅保留关键锚点 0.75
# ============================================================
def fig7_2():
    fig, ax = plt.subplots(figsize=(8.6, 6.8), subplot_kw={'projection': 'polar'})
    cats = ['生理潜能', '心理潜能', '社会潜能', '环境潜能']
    angles = np.linspace(0, 2 * np.pi, len(cats), endpoint=False).tolist()
    ok = [0.80, 0.75, 0.70, 0.70]
    bad = [0.75, 0.35, 0.30, 0.25]

    def close(a):
        return a + [a[0]]

    ang = close(angles)
    ax.plot(ang, close(ok), color=GREEN, lw=2.0, label='健康者（均衡）')
    ax.plot(ang, close(bad), color=RED, lw=1.8, ls='--', label='退休教师（失衡）')
    ax.plot(ang, [0.6] * 5, color=GRAY, lw=1.2, ls='--',
            label='及格线 0.6')

    # 关键数值锚点：退休教师"生理 0.75"顶点（图注④指向）
    ax.text(0.0, bad[0] - 0.16, '0.75', ha='center', va='center',
            fontsize=11, color=RED, fontweight='bold')

    ax.set_xticks(angles)
    ax.set_xticklabels(cats, fontsize=11)
    ax.set_ylim(0, 1.12)
    ax.set_yticks([0.2, 0.4, 0.6, 0.8, 1.0])
    ax.set_yticklabels(['0.2', '0.4', '0.6', '0.8', '1.0'], fontsize=9,
                       color=LGRAY)
    ax.set_theta_offset(0.0)

    fig.legend(loc='lower center', ncol=3, fontsize=10, frameon=True,
               bbox_to_anchor=(0.5, 0.0))
    fig.subplots_adjust(top=0.90, bottom=0.14)
    fig.savefig(os.path.join(OUT, 'fig7-3.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('fig7-3 done')


# ============================================================
# 图 7-2 适度而非最优化曲线（钟形）——聚焦 x∈[0.5,1.5]（正文 7.2.1、7.2.2）
# 曲线：适度设计（整体健康潜能，绿色实线）vs 最大化设计（表面奖励，红色虚线）
# 关键点/线：适度区间边界 x=0.75/1.25（绿色浅底阴影）、峰值 (1.0,1.0)
# 文字分层：临床刻度句、冲顶解释句移入图注；去网格、去装饰箭头
# ============================================================
def fig7_3():
    fig, ax = plt.subplots(figsize=(10.0, 6.0))
    x = np.linspace(0.5, 1.5, 400)
    y_bell = np.exp(-((x - 1.0) / 0.40) ** 2)
    y_max = 0.30 + 0.60 * x

    # 适度区间绿色浅底 [0.75, 1.25]（图注：绿色阴影为适度区间）
    ax.axvspan(0.75, 1.25, color=BG_GREEN, zorder=0)

    ax.plot(x, y_bell, color=GREEN, lw=2.2, zorder=3,
            label='适度设计（整体健康潜能）')
    ax.plot(x, y_max, color=RED, lw=1.8, ls='--', zorder=3,
            label='最大化设计（表面成绩）')

    # 适度区间：竖点线 + 顶部标注（无背景色带）
    ax.axvline(0.75, color=PALE, lw=1.0, ls=':', zorder=2)
    ax.axvline(1.25, color=PALE, lw=1.0, ls=':', zorder=2)
    ax.plot(1.0, 1.0, 'o', ms=7, mfc='white', mec=GREEN, mew=1.4, zorder=5)
    ax.text(1.0, 1.12, '适度区间（满分区）', ha='center', va='bottom',
            fontsize=11, color=GREEN, fontweight='bold')
    ax.text(1.10, 0.84, '峰值 (1.0, 1.0)', ha='left', va='center',
            fontsize=11, color=GREEN, fontweight='bold')

    ax.text(0.62, 0.28, '不足区', ha='center', va='center',
            fontsize=10, color=GRAY)
    ax.text(1.40, 0.28, '过度区', ha='center', va='center',
            fontsize=10, color=GRAY)

    ax.set_xlabel('对单一指标的追求强度 x', fontsize=11)
    ax.set_ylabel('整体健康潜能', fontsize=11)
    ax.set_xlim(0.5, 1.5)
    ax.set_ylim(0, 1.4)
    ax.set_xticks([0.5, 0.75, 1.0, 1.25, 1.5])
    ax.set_yticks([0.0, 0.4, 0.8, 1.2])
    ax.legend(loc='upper left', fontsize=10, frameon=True)
    fig.subplots_adjust(bottom=0.15)
    fig.savefig(os.path.join(OUT, 'fig7-2.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('fig7-2 done')


# ============================================================
# 图 7-4 奖励设计权衡：即时奖励 vs 长期健康——γ 决定治标还是治本（正文 7.1.2、7.5.1）
# 曲线：方案甲(6,3,1) 蓝色实线 vs 方案乙(1,3,9) 绿色实线（图注：蓝=甲、绿=乙）
# 关键点：γ*≈0.79 分水岭、甲10<乙13（端点数值与解释句移入图注）
# ============================================================
def fig7_4():
    fig, ax = plt.subplots(figsize=(10.0, 6.0))
    g = np.linspace(0, 1, 300)
    gA = 6 + 3 * g + g ** 2
    gB = 1 + 3 * g + 9 * g ** 2
    gstar = math.sqrt(5.0 / 8.0)

    ax.plot(g, gA, color=BLUE, lw=2.2, zorder=3,
            label='方案甲（治标）：随访评分 (6,3,1)')
    ax.plot(g, gB, color=GREEN, lw=2.2, zorder=3,
            label='方案乙（治本）：随访评分 (1,3,9)')

    # 分水岭（无背景色带，用虚线+文字分区）
    ax.axvline(gstar, color=DARK, lw=1.4, ls='--', zorder=3)
    ax.text(gstar, 13.4, 'γ* ≈ 0.79\n治标/治本分水岭', ha='center', va='top',
            fontsize=11, color=DARK, fontweight='bold', linespacing=1.3)

    ax.text(0.13, 2.6, '短视区（只治标）', ha='center', va='center',
            fontsize=10, color=GRAY)
    ax.text(0.88, 2.6, '远视区（能治本）', ha='center', va='center',
            fontsize=10, color=GREEN)

    # 关键数值锚点：甲 10 < 乙 13（图注④）
    ax.text(0.70, 12.9, '甲 10 < 乙 13', fontsize=11, color=GREEN,
            fontweight='bold')

    ax.set_xlabel('远近权衡系数 γ', fontsize=11)
    ax.set_ylabel('长期总疗效 G', fontsize=11)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 14)
    ax.set_xticks([0.0, 0.2, 0.4, 0.6, 0.8, 1.0])
    ax.set_yticks([0, 4, 8, 12])
    ax.legend(loc='upper left', fontsize=10, frameon=True)
    fig.subplots_adjust(bottom=0.15)
    fig.savefig(os.path.join(OUT, 'fig7-4.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('fig7-4 done')


if __name__ == '__main__':
    fig7_1()
    fig7_2()
    fig7_3()
    fig7_4()
    print('ALL DONE ->', OUT)
