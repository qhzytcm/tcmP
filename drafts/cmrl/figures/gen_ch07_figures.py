# -*- coding: utf-8 -*-
"""《中医场景强化学习》第7章 核心图生成脚本 v2（图表工程师·聚焦重绘版）

生成（覆盖 figures/ch07/）：
      fig7-1 奖励函数设计示意（给健康结果打分的一把尺子，失眠算例 0.76）
      fig7-2 四个最适度雷达图（生理/心理/社会/环境，均衡 vs 失衡）
      fig7-3 适度而非最优化曲线（钟形，聚焦最适度区间段）
      fig7-4 奖励设计权衡（即时奖励 vs 长期健康，γ 权衡曲线）
聚焦原则：图体只保留"能代表含义的图段"——调节数轴起止刻度与步长，
      砍掉空白与冗余标注（详细说明移入图注四要素）。
范式：SimHei / unicode_minus=False / Agg / dpi=200 / bbox_inches='tight' /
      图题入图（ax.set_title / fig.suptitle）。
数值一致性：正文 7.1.2（0.76 加权算例）、7.1.1（随访 +1/+0.5/-0.3）、
      7.2.2（收缩压 90-130 mmHg、步数 6000-10000/>15000）、7.3.1（退休教师画像）、
      7.5.1（平均住院日剧本）——凡正文有定值的数字一律与正文一致。
"""
import os
import math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle
from matplotlib import font_manager

plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ch07')
os.makedirs(OUT, exist_ok=True)


def box(ax, x, y, w, h, fc, ec, txt, fs=10.5, tc='#1b2631', lw=1.6,
        style='round,pad=0.06', bold=False, ls=1.45):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=style,
                                facecolor=fc, edgecolor=ec, lw=lw, zorder=2))
    ax.text(x + w / 2, y + h / 2, txt, ha='center', va='center',
            fontsize=fs, color=tc, zorder=3,
            fontweight='bold' if bold else 'normal', linespacing=ls)


def fig7_1():
    """图 7-1 奖励函数设计示意：给健康结果打分的一把尺子（正文 7.1.1、7.1.2）
    聚焦图段：输入(s,a)→r(s,a)→一个数值 的映射 + 四项加权算例(0.76) + 随访三分数刻度卡。"""
    fig, ax = plt.subplots(figsize=(11.8, 6.8))
    ax.set_xlim(0, 11.8)
    ax.set_ylim(0, 7.4)
    ax.axis('off')
    ax.set_title('图7-1 奖励函数设计示意：给健康结果打分的一把尺子',
                 fontsize=13.5, pad=12)

    # —— 左：输入——函数——输出（核心图段：映射关系）——
    box(ax, 0.30, 5.55, 2.15, 1.25, '#d6eaf8', '#1f618d',
        '证候 / 四诊信息', fs=10)
    box(ax, 0.30, 3.55, 2.15, 1.25, '#d6eaf8', '#1f618d',
        '治法方剂', fs=10)
    box(ax, 3.15, 4.05, 2.60, 2.30, '#fdebd0', '#b9770e',
        '疗效打分\n健康全要素打分\n\n输入 → 一个数值', fs=10)
    ax.annotate('', xy=(3.15, 5.90), xytext=(2.50, 6.10),
                arrowprops=dict(arrowstyle='-|>', color='#1b2631', lw=1.8), zorder=3)
    ax.annotate('', xy=(3.15, 4.90), xytext=(2.50, 4.40),
                arrowprops=dict(arrowstyle='-|>', color='#1b2631', lw=1.8), zorder=3)
    ax.annotate('', xy=(6.60, 5.15), xytext=(5.90, 5.15),
                arrowprops=dict(arrowstyle='-|>', color='#b9770e', lw=2.0), zorder=3)
    ax.text(6.25, 5.62, '评分\n（一个数）', ha='center', va='center',
            fontsize=9, color='#7d6608', linespacing=1.3)

    # —— 中右：健康全要素加权打分（失眠诊疗随访算例，正文 7.1.2，聚焦图段）——
    ax.text(7.05, 6.95, '健康全要素加权打分：失眠诊疗随访（正文 7.1.2）',
            ha='center', fontsize=10.5, fontweight='bold', color='#1b2631')
    items = [
        ('症状缓解', 0.4, 0.8, '#2e86c1'),
        ('日间功能', 0.2, 0.7, '#229954'),
        ('情志舒展', 0.2, 0.6, '#b7950b'),
        ('信任依从', 0.2, 0.9, '#8e44ad'),
    ]
    y0, dh = 6.10, 0.98
    for i, (name, w, score, color) in enumerate(items):
        yy = y0 - i * dh
        ax.text(7.05, yy, name, ha='center', va='center', fontsize=10, color='#1b2631')
        contrib = w * score
        ax.add_patch(Rectangle((7.95, yy - 0.28), contrib * 10.0, 0.56,
                               facecolor=color, edgecolor='none', alpha=0.85, zorder=2))
        ax.add_patch(Rectangle((7.95, yy - 0.28), 3.2, 0.56, facecolor='none',
                               edgecolor='#b3b6b7', lw=0.9, zorder=3))
        ax.text(11.30, yy, f'权重 {w} × 得分 {score} = {contrib:.2f}',
                ha='left', va='center', fontsize=10, color='#424949')

    # —— 总分框：0.76（指针图段：与正文实算一致）——
    box(ax, 6.75, 1.30, 4.75, 1.05, '#e8f8f5', '#1e8449',
        '综合健康评分 = 0.4×0.8 + 0.2×0.7 + 0.2×0.6 + 0.2×0.9\n'
        '= 0.32 + 0.14 + 0.12 + 0.18 = 0.76', fs=10.5, bold=True, ls=1.4)
    ax.text(9.12, 0.72, '权重即价值观：权重偏疗效还是偏体验，塑造出不同的诊疗风格',
            ha='center', fontsize=9, color='#566573')

    # —— 下左：随访三分数刻度（正文 7.1.1，聚焦图段：尺子的刻度）——
    ax.text(3.00, 0.62, '尺子的刻度例（随访三分数，正文 7.1.1）：',
            ha='center', fontsize=9.5, color='#1b2631')
    cards = [
        ('+1', '表解身和、诸症悉除', '#d5f5e3', '#1e8449'),
        ('+0.5', '余邪未清、微有咳嗽', '#eafaf1', '#229954'),
        ('-0.3', '汗出太过、气短乏力', '#fadbd8', '#c0392b'),
    ]
    for i, (score, desc, fc, ec) in enumerate(cards):
        x0 = 0.30 + i * 2.62
        box(ax, x0, 0.10, 2.45, 1.22, fc, ec,
            score + '\n' + desc, fs=9.5, ls=1.35)
    ax.text(3.00, 0.02, '同样的发汗动作，分寸不同则价值迥异——中病即止、微似有汗',
            ha='center', fontsize=9, color='#7d6608')

    fig.savefig(os.path.join(OUT, 'fig7-1.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('fig7-1 done')


def fig7_2():
    """图 7-2 四个最适度雷达图：生理/心理/社会/环境——均衡 vs 失衡（正文 7.3.1）
    聚焦图段：红色失衡多边形（仅生理一维及格） vs 绿色均衡多边形 + 及格线。"""
    fig, ax = plt.subplots(figsize=(9.0, 7.4), subplot_kw={'projection': 'polar'})
    cats = ['生理潜能', '心理潜能', '社会潜能', '环境潜能']
    angles = np.linspace(0, 2 * np.pi, len(cats), endpoint=False).tolist()

    # 均衡（健康者，绿色）vs 失衡（退休教师，红色；数值为示意，语义与正文 7.3.1 一致）
    ok = [0.80, 0.75, 0.70, 0.70]
    bad = [0.75, 0.35, 0.30, 0.25]

    def close(a):
        return a + [a[0]]

    ang = close(angles)
    ax.plot(ang, close(ok), color='#1e8449', lw=2.2, label='健康者（均衡）')
    ax.fill(ang, close(ok), color='#1e8449', alpha=0.14)
    ax.plot(ang, close(bad), color='#c0392b', lw=2.2, label='退休教师（失衡）')
    ax.fill(ang, close(bad), color='#c0392b', alpha=0.14)
    ax.plot(ang, [0.6] * 5, color='#7f8c8d', lw=1.4, ls='--', label='及格线 0.6')

    ax.set_xticks(angles)
    ax.set_xticklabels(cats, fontsize=12.5)
    ax.set_ylim(0, 1.0)
    ax.set_yticks([0.2, 0.4, 0.6, 0.8, 1.0])          # 聚焦：0.2 起、步长 0.2
    ax.set_yticklabels(['0.2', '0.4', '0.6', '0.8', '1.0'], fontsize=8.5)
    ax.set_theta_offset(0.0)

    # 低维注释（退休教师画像，正文 7.3.1）
    notes = [
        (np.deg2rad(90), 0.52, '丧偶后情绪低落、睡眠浅\n（心理低）'),
        (np.deg2rad(180), 0.47, '子女在外、社交萎缩\n（社会低）'),
        (np.deg2rad(270), 0.42, '冬季畏寒、居室阴冷\n（环境低）'),
        (np.deg2rad(0), 0.90, '血压血糖平稳\n（生理较高）'),
    ]
    for th, r, txt in notes:
        ax.text(th, r, txt, ha='center', va='center', fontsize=9,
                color='#c0392b', linespacing=1.35)

    fig.suptitle('图7-2 四个最适度雷达图：生理、心理、社会、环境——均衡与失衡对比\n'
                 '目标向量 F = (f生, f心, f社, f环)（正文 7.3.1）',
                 fontsize=13, y=0.98)
    fig.legend(loc='lower center', ncol=3, fontsize=10.5,
               bbox_to_anchor=(0.5, -0.02), frameon=True)
    fig.text(0.5, 0.02,
             '指针图段：红色多边形仅“生理”一维在及格线(0.6)之上，整体明显失衡——'
             '只治失眠不问孤寂、只调情绪不管居室，都是只见一维的疗法',
             ha='center', fontsize=9.5, color='#566573')
    fig.subplots_adjust(top=0.82, bottom=0.18)

    fig.savefig(os.path.join(OUT, 'fig7-2.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('fig7-2 done')


def fig7_3():
    """图 7-3 适度而非最优化曲线（钟形）——聚焦最适度区间段（正文 7.2.1、7.2.2）
    数轴聚焦：x∈[0.5,1.5]（步长 0.25），y∈[0,1.4]（步长 0.2）；
    核心图段：适度区间满分区 + 冲顶后整体下降段。"""
    fig, ax = plt.subplots(figsize=(10.6, 6.8))
    x = np.linspace(0.5, 1.5, 400)
    y_bell = np.exp(-((x - 1.0) / 0.40) ** 2)      # 整体健康潜能（钟形）
    y_max = 0.30 + 0.60 * x                         # 最大化设计的表面奖励（单调上升）

    ax.axvspan(0.75, 1.25, color='#d5f5e3', alpha=0.55, zorder=0)
    ax.plot(x, y_bell, color='#1e8449', lw=2.6, zorder=3,
            label='适度设计：整体健康潜能（钟形）')
    ax.plot(x, y_max, color='#c0392b', lw=2.0, ls='--', zorder=3,
            label='最大化设计：表面成绩（单调上升）')

    ax.axvline(0.75, color='#1e8449', lw=1.0, ls=':', zorder=2)
    ax.axvline(1.25, color='#1e8449', lw=1.0, ls=':', zorder=2)
    ax.text(1.0, 1.08, '适度区间（满分区）\n恰到好处最好', ha='center', va='bottom',
            fontsize=10.5, color='#1e8449', fontweight='bold', linespacing=1.35)
    ax.text(0.62, 0.30, '不足区\n（潜能未展开）', ha='center', va='center',
            fontsize=9.5, color='#566573', linespacing=1.35)
    ax.text(1.40, 0.30, '过度区\n（指标冲顶 → 整体下降）', ha='right', va='center',
            fontsize=9.5, color='#c0392b', linespacing=1.35)

    # 冲顶后整体下降：箭头指向钟形右降段（指针图段）
    ax.annotate('', xy=(1.42, 0.20), xytext=(1.18, 0.62),
                arrowprops=dict(arrowstyle='->', color='#c0392b', lw=1.6), zorder=4)
    ax.text(1.20, 0.76, '拆东墙补西墙：\n冲顶时整体反而下降\n'
                        '（步数>15000 伤膝、\n血糖过低致低血糖）',
            ha='left', va='center', fontsize=9, color='#c0392b', linespacing=1.35)

    # 最大化虚线右端：报表一路走高
    ax.annotate('', xy=(1.47, 1.17), xytext=(1.30, 1.32),
                arrowprops=dict(arrowstyle='->', color='#c0392b', lw=1.3), zorder=4)
    ax.text(1.28, 1.36, '报表一路走高（指标冲顶的承诺）', ha='right', va='center',
            fontsize=9, color='#c0392b')

    ax.set_xlabel('对单一指标的追求强度 x（如“血糖越低越好”“步数越多越好”）', fontsize=10.5)
    ax.set_ylabel('整体健康潜能（整体奖励 R）', fontsize=10.5)
    # 聚焦数轴：起止与步长
    ax.set_xlim(0.5, 1.5)
    ax.set_ylim(0, 1.4)
    ax.set_xticks([0.5, 0.75, 1.0, 1.25, 1.5])
    ax.set_yticks([0.0, 0.2, 0.4, 0.6, 0.8, 1.0, 1.2, 1.4])
    ax.legend(loc='upper left', fontsize=9.5, frameon=True)
    ax.set_title('图7-3 适度而非最优化曲线：过度追求单目标，整体健康先升后降\n'
                 '“阴平阳秘，精神乃治”——不是越高越好，而是恰到好处最好（正文 7.2.1）',
                 fontsize=13, pad=10)
    fig.text(0.5, 0.015,
             '临床刻度（正文 7.2.2）：收缩压最适区间 90–130 mmHg，过低过高都按距离扣分；'
             '每日步数 6000–10000 步给满分，超过 15000 步奖励回落——对中老年人，越多越好是害人的直觉',
             ha='center', fontsize=9.5, color='#566573')
    fig.subplots_adjust(bottom=0.13)
    fig.savefig(os.path.join(OUT, 'fig7-3.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('fig7-3 done')


def fig7_4():
    """图 7-4 奖励设计权衡：即时奖励 vs 长期健康——γ 权衡曲线（正文 7.1.2、7.5.1）
    数轴聚焦：γ∈[0,1]（步长 0.2）、G∈[0,14]（步长 2）；
    核心图段：γ*≈0.79 分水岭两侧——短视区甲胜出、远视区乙胜出。"""
    fig, ax = plt.subplots(figsize=(10.2, 6.9))
    g = np.linspace(0, 1, 300)
    gA = 6 + 3 * g + g ** 2          # 方案甲（即时满足/治标）：奖励序列 (6, 3, 1)
    gB = 1 + 3 * g + 9 * g ** 2      # 方案乙（长期健康/治本）：奖励序列 (1, 3, 9)
    gstar = math.sqrt(5.0 / 8.0)     # 交叉点 γ* ≈ 0.79（5 = 8γ²）

    ax.axvspan(0, gstar, color='#fadbd8', alpha=0.45, zorder=0)
    ax.axvspan(gstar, 1, color='#d5f5e3', alpha=0.45, zorder=0)
    ax.plot(g, gA, color='#2e86c1', lw=2.4, zorder=3,
            label='方案甲（即时满足/治标）：随访评分 (6, 3, 1)')
    ax.plot(g, gB, color='#1e8449', lw=2.4, zorder=3,
            label='方案乙（长期健康/治本）：随访评分 (1, 3, 9)')
    ax.axvline(gstar, color='#7d6608', lw=1.6, ls='--', zorder=3)
    ax.text(gstar, 13.2, 'γ* ≈ 0.79\n治标 / 治本分水岭', ha='center', va='top',
            fontsize=9.5, color='#7d6608', linespacing=1.35)

    ax.text(0.12, 3.0, '短视区：考核周期短 → 只治标\n→ 指标异化（平均住院日剧本）',
            ha='center', va='center', fontsize=9.5, color='#c0392b', linespacing=1.4)
    ax.text(0.90, 3.0, '远视区：评价覆盖长期转归 → 能治本\n→ 长期健康胜出',
            ha='center', va='center', fontsize=9.5, color='#1e8449', linespacing=1.4)

    # 端点标注（指针图段：γ=0 甲胜、γ=1 乙胜）
    ax.plot(0, 6, 'o', color='#2e86c1', ms=6, zorder=4)
    ax.plot(1, 10, 'o', color='#2e86c1', ms=6, zorder=4)
    ax.plot(0, 1, 'o', color='#1e8449', ms=6, zorder=4)
    ax.plot(1, 13, 'o', color='#1e8449', ms=6, zorder=4)
    ax.text(0.03, 6.4, 'γ=0（只看眼前）：甲 6 完胜乙 1', ha='left', va='bottom',
            fontsize=9, color='#2e86c1')
    ax.text(0.62, 13.2, 'γ=1（完整评价）：甲 10 < 乙 13，治本胜出',
            ha='left', va='bottom', fontsize=9, color='#1e8449')

    ax.set_xlabel('远近权衡系数 γ（0 = 只看当下，1 = 完整看待长期）', fontsize=10.5)
    ax.set_ylabel('长期总疗效 G', fontsize=10.5)
    # 聚焦数轴：起止与步长
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 14)
    ax.set_xticks([0.0, 0.2, 0.4, 0.6, 0.8, 1.0])
    ax.set_yticks([0, 2, 4, 6, 8, 10, 12, 14])
    ax.legend(loc='upper left', fontsize=9.5, frameon=True)
    ax.set_title('图7-4 奖励设计权衡：即时奖励 vs 长期健康——γ 决定治标还是治本',
                 fontsize=13, pad=10)
    fig.text(0.5, 0.015,
             '甲总收益 10 < 乙总收益 13：只有足够看重未来（γ 足够大），治本方案才会被选择；'
             'γ 过小正是平均住院日剧本等奖励陷阱的制度根源（正文 7.5.1）',
             ha='center', fontsize=9.5, color='#566573')
    fig.subplots_adjust(bottom=0.13)
    fig.savefig(os.path.join(OUT, 'fig7-4.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('fig7-4 done')


if __name__ == '__main__':
    fig7_1()
    fig7_2()
    fig7_3()
    fig7_4()
    print('ALL DONE ->', OUT)
