# -*- coding: utf-8 -*-
"""《中医场景强化学习》第10章 聚焦图段重绘脚本（v2 聚焦模式，ch03 同款）
7 幅图：fig10-1 AC 架构 / fig10-2 优势函数 / fig10-3 六者闭环
       fig10-4 三编地图 / fig10-5 Agent 循环 / fig10-6 人机闭环 / fig10-7 算力智能曲线
聚焦原则：
  - 图内不画大标题（图题由 Excel 图题行承担：图体上方一行居中黑体）
  - 收紧 xlim/ylim/xticks/yticks，只保留能代表含义的图段（如算力曲线聚焦"足够算力阈值"跃升段）
  - 图内底部说明行/横幅移除，并入图注四要素版（a.对接正文提示 b.线注释 c.符号注释 d.指针图段）
规范：SimHei + axes.unicode_minus=False + dpi=200；数学符号用 mathtext；负号用 ASCII '-'
输出：drafts/cmrl/figures/ch10/*.png（覆盖旧图）
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

# 与正文一致的数值自检
def assert_numbers():
    pa1 = math.exp(0.5) / (math.exp(0.5) + math.exp(0.3))
    pa2 = math.exp(0.3) / (math.exp(0.5) + math.exp(0.3))
    assert abs(pa1 - 0.5498) < 1e-4 and abs(pa2 - 0.4502) < 1e-4
    assert 75 - 60 == 15 and 45 - 60 == -15 and 60 - 60 == 0     # 10.2.1 优势例
    assert abs(1 + 0.9 * 10 - 10 - 0.0) < 1e-9                   # 10.2.3 δ_t=0 例
    assert abs((0.1 / 0.01) - 10.0) < 1e-9                       # 10.2.2 α_w/α_θ
    print('[assert] ch10 关键数值一致 OK')


# ================= fig10-1 行动者-评价者架构（聚焦：决策与评价分离三角） =================
def fig10_1():
    fig, ax = plt.subplots(figsize=(8.2, 5.2))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 5.2)
    ax.axis('off')

    # 左：行动者（浅蓝）
    ax.add_patch(FancyBboxPatch((0.6, 2.7), 3.5, 2.05, boxstyle='round,pad=0.07',
                                fc='#d6eaf8', ec='#1f618d', lw=1.8))
    ax.text(2.35, 4.42, '医者', ha='center', va='center',
            fontsize=12, fontweight='bold', color='#1f618d')
    ax.text(2.35, 3.98, '辨证开方', ha='center', va='center', fontsize=10)
    ax.text(2.35, 3.50, '处方水平随', ha='center', va='center', fontsize=10, color='#424949')
    ax.text(2.35, 3.02, '临证积累而精进', ha='center', va='center', fontsize=9)

    # 右：评价者（浅橙）
    ax.add_patch(FancyBboxPatch((5.9, 2.7), 3.5, 2.05, boxstyle='round,pad=0.07',
                                fc='#fdebd0', ec='#a04000', lw=1.8))
    ax.text(7.65, 4.42, '规者与药者', ha='center', va='center',
            fontsize=12, fontweight='bold', color='#a04000')
    ax.text(7.65, 3.98, '质控·审方', ha='center', va='center', fontsize=10)
    ax.text(7.65, 3.50, '评价标准随', ha='center', va='center', fontsize=10, color='#424949')
    ax.text(7.65, 3.02, '随访数据而校准', ha='center', va='center', fontsize=9)

    # 中央粗箭头：评价者 → 行动者（加权信号）
    ax.annotate('', xy=(4.15, 3.72), xytext=(5.85, 3.72),
                arrowprops=dict(arrowstyle='-|>', color='#c0392b', lw=3.0))
    ax.text(5.0, 4.05, '疗效预判', ha='center', va='center',
            fontsize=10, color='#c0392b', fontweight='bold')

    # 底部环境框（浅灰）
    ax.add_patch(FancyBboxPatch((1.4, 0.4), 7.2, 1.25, boxstyle='round,pad=0.07',
                                fc='#f2f3f4', ec='#616a6b', lw=1.5))
    ax.text(5.0, 1.28, '环境（患者与医院场景）', ha='center', va='center',
            fontsize=11, fontweight='bold', color='#424949')
    ax.text(5.0, 0.78, '当前证候（四诊信息）→ 治法方剂 → 复诊疗效（随访反馈）',
            ha='center', va='center', fontsize=9.5)

    # 环流箭头：环境 ↔ 行动者、环境 → 评价者
    ax.annotate('', xy=(2.0, 2.7), xytext=(1.8, 1.65),
                arrowprops=dict(arrowstyle='-|>', color='#1a5276', lw=2.0))
    ax.text(0.95, 2.15, '当前证候', ha='center', va='center', fontsize=9, color='#1a5276')
    ax.annotate('', xy=(4.15, 1.65), xytext=(3.9, 2.7),
                arrowprops=dict(arrowstyle='-|>', color='#1a5276', lw=2.0))
    ax.text(4.75, 2.15, '治法方剂', ha='center', va='center', fontsize=9, color='#1a5276')
    ax.annotate('', xy=(7.1, 2.7), xytext=(6.9, 1.65),
                arrowprops=dict(arrowstyle='-|>', color='#935116', lw=2.0))
    ax.text(8.15, 2.15, '复诊疗效、后继证候', ha='center', va='center',
            fontsize=8.5, color='#935116')

    fig.savefig(os.path.join(OUT, 'fig10-1.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('fig10-1 done')


# ================= fig10-2 优势函数与临床三判（聚焦：60 分基线 ±15 判定带） =================
def fig10_2():
    fig, ax = plt.subplots(figsize=(8.8, 4.9))
    ax.set_xlim(0.4, 10.2)
    ax.set_ylim(0.2, 5.15)
    ax.axis('off')

    # 数轴聚焦 40-80 分：px = 1.0 + (score-40)*0.2  (40→1.0, 60→5.0, 80→9.0)
    def px(score):
        return 1.0 + (score - 40) * 0.2

    # 正/负优势背景区（基线 60 两侧）
    ax.add_patch(Rectangle((px(45), 0.75), px(60) - px(45), 3.9, fc='#fdedec', ec='none', alpha=0.55))
    ax.add_patch(Rectangle((px(60), 0.75), px(75) - px(60), 3.9, fc='#eafaf1', ec='none', alpha=0.55))
    ax.text((px(45) + px(60)) / 2, 4.42, '劣于预期区：效改其方', ha='center', va='center',
            fontsize=10, color='#b03a2e', fontweight='bold')
    ax.text((px(60) + px(75)) / 2, 4.42, '优于预期区：效如桴鼓', ha='center', va='center',
            fontsize=10, color='#1e8449', fontweight='bold')

    # 数轴
    ax.annotate('', xy=(9.0, 0.95), xytext=(1.0, 0.95),
                arrowprops=dict(arrowstyle='-|>', color='#333333', lw=1.6))
    ax.text(9.35, 0.95, '得分', ha='center', va='center', fontsize=10)
    for s in [40, 50, 60, 70, 80]:
        ax.plot([px(s), px(s)], [0.87, 1.03], color='#333333', lw=1.2)
        ax.text(px(s), 0.72, str(s), ha='center', va='center', fontsize=9)

    # 基线 60（灰色虚线）
    bx = px(60)
    ax.plot([bx, bx], [1.05, 4.35], color='#7f8c8d', lw=2.0, linestyle='--')
    ax.text(bx + 0.12, 4.62, '预期平均水平 60 分', ha='left', va='center',
            fontsize=9.5, color='#7f8c8d')

    # 三个判定点：75 / 45 / 60
    def mark(score, y, color, txt, sub):
        x = px(score)
        ax.plot([x, x], [1.05, y - 0.18], color=color, lw=1.3, linestyle=':')
        ax.scatter([x], [y], s=150, color=color, zorder=5, edgecolors='white', linewidths=1.3)
        ax.text(x, y + 0.18, txt, ha='center', va='center', fontsize=10, color=color, fontweight='bold')
        ax.text(x, y - 0.42, sub, ha='center', va='center', fontsize=8.2, color=color)

    mark(75, 3.75, '#1e8449', '实际 75 分 → 优于预期 +15', '效如桴鼓：显著优于预期，值得沿用强化')
    mark(45, 3.30, '#b03a2e', '实际 45 分 → 劣于预期 -15', '效改其方：劣于预期，应调整治法')
    mark(60, 2.85, '#515a5a', '实际 60 分 → 与预期相当 0', '效不更方：与预期相当，维持原方')

    # 底部个体化评价提示（细节并入图注）
    ax.text(5.0, 0.42, '同一首方剂、两个证候相近的患者：药后症减脉和者优于预期，药后如故纳差者劣于预期',
            ha='center', va='center', fontsize=8.8, color='#515a5a')

    fig.savefig(os.path.join(OUT, 'fig10-2.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('fig10-2 done')


# ================= fig10-3 六者协同与幸福闭环（聚焦：六方环 + 中央闭环 + 机制连线） =================
def fig10_3():
    fig, ax = plt.subplots(figsize=(8.6, 7.9))
    ax.set_xlim(-1.85, 1.85)
    ax.set_ylim(-1.72, 1.82)
    ax.set_aspect('equal')
    ax.axis('off')

    # 规则六边形布局（相邻框间距保证不重叠）
    roles = [
        (0.00, 1.05, '医者', '辨证开方', '#d6eaf8', '#1f618d'),
        (1.05, 0.61, '患者', '疗效与依从\n是最终裁判', '#fadbd8', '#943126'),
        (1.05, -0.61, '药者', '审方与调剂\n处方守门人', '#d5f5e3', '#1e8449'),
        (0.00, -1.05, '械者', '影像检验\n诊疗的眼睛与手脚', '#d1f2eb', '#148f77'),
        (-1.05, -0.61, '规者', '质控与流程监督', '#fdebd0', '#a04000'),
        (-1.05, 0.61, '法者', '知情同意\n责任认定', '#e8daef', '#6c3483'),
    ]
    ring = [(0.00, 1.05), (1.05, 0.61), (1.05, -0.61), (0.00, -1.05), (-1.05, -0.61), (-1.05, 0.61)]
    for i in range(len(ring)):
        x1, y1 = ring[i]
        x2, y2 = ring[(i + 1) % len(ring)]
        ax.plot([x1, x2], [y1, y2], color='#b2babb', lw=1.0, alpha=0.7, zorder=1)

    # 中央幸福闭环
    ax.add_patch(Circle((0, 0), 0.44, fc='#fdebd0', ec='#c0392b', lw=2.0, zorder=4))
    ax.text(0, 0.13, '幸福闭环', ha='center', va='center', fontsize=13,
            fontweight='bold', color='#c0392b', zorder=5)
    ax.text(0, -0.22, '健康共同体', ha='center', va='center', fontsize=10, color='#c0392b', zorder=5)

    for x, y, name, sub, fc, ec in roles:
        ax.add_patch(FancyBboxPatch((x - 0.56, y - 0.46), 1.12, 0.92,
                                    boxstyle='round,pad=0.06', fc=fc, ec=ec, lw=1.5, zorder=3))
        ax.text(x, y + 0.19, name, ha='center', va='center', fontsize=9.5,
                fontweight='bold', color=ec, zorder=4)
        ax.text(x, y - 0.16, sub, ha='center', va='center', fontsize=7.2,
                color='#2c3e50', zorder=4, linespacing=1.2)

    # 医—患：reward 双向粗箭头
    ax.annotate('', xy=(1.05, 0.61), xytext=(0.25, 0.95),
                arrowprops=dict(arrowstyle='-|>', color='#c0392b', lw=3.0,
                                connectionstyle='arc3,rad=-0.25'), zorder=2)
    ax.annotate('', xy=(0.30, 0.98), xytext=(1.05, 0.75),
                arrowprops=dict(arrowstyle='-|>', color='#c0392b', lw=3.0,
                                connectionstyle='arc3,rad=-0.25'), zorder=2)
    ax.text(0.75, 1.24, '疗效回路：信任→依从→疗效→信任', ha='center', va='center',
            fontsize=8.2, color='#c0392b', fontweight='bold', zorder=4)

    def mech_line(x1, y1, x2, y2, label, color, dx=0, dy=0, fs=8):
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle='-|>', color=color, lw=2.0,
                                    connectionstyle='arc3,rad=0.12'), zorder=2)
        ax.text((x1 + x2) / 2 + dx, (y1 + y2) / 2 + dy, label, ha='center', va='center',
                fontsize=fs, color=color, fontweight='bold', zorder=4)

    mech_line(0.25, 0.60, 0.85, -0.30, '责任分离', '#1e8449', dx=0.14, dy=0.02)    # 医—药
    mech_line(-0.25, 0.60, -0.85, -0.30, '独立评价', '#a04000', dx=-0.14, dy=0.02)   # 医—规
    mech_line(-0.20, 0.62, -1.00, 0.62, '全程留痕', '#6c3483', dx=0.0, dy=0.22)      # 医—法
    mech_line(0.10, 0.55, 0.15, -0.55, '状态观测', '#148f77', dx=0.30, dy=0.0)       # 医—械（弧线绕中央圆）

    fig.savefig(os.path.join(OUT, 'fig10-3.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('fig10-3 done')


# ================= fig10-4 全书三编与共同愿景（聚焦：三编路线 + 三重图景金字塔） =================
def fig10_4():
    fig, ax = plt.subplots(figsize=(10.0, 6.9))
    ax.set_xlim(0, 11)
    ax.set_ylim(0, 7.1)
    ax.axis('off')

    vols = [
        (5.35, 6.85, '#d6eaf8', '#1f618d', '上编 · 提高认知（第 1-3 章）',
         '第1章 认知的起点 → 第2章 认知的结构 → 第3章 认知的深化',
         '核心：状态观测 · 健康建模 · 统计学习', '问题：AI 如何认识中医医院？'),
        (2.75, 4.30, '#d5f5e3', '#1e8449', '中编 · 确认信仰（第 4-6 章）',
         '第4章 信仰的量化 → 第5章 信仰的择优 → 第6章 信仰的检验',
         '核心：价值量化 · 辨证择优 · 临床检验', '问题：中医药的疗效如何确认？'),
        (0.30, 1.75, '#fdebd0', '#a04000', '下编 · 追求幸福（第 7-10 章）',
         '第7章 幸福的表达 → 第8章 幸福的实现 → 第9章 幸福的探索 → 第10章 幸福的闭环',
         '核心：个人定位 · 场景生存最适度 · 环境共荣最适度', '问题：为了什么而优化？'),
    ]
    for y0, y1, fc, ec, title, chapters, core, question in vols:
        ax.add_patch(FancyBboxPatch((0.5, y0), 6.7, y1 - y0, boxstyle='round,pad=0.08',
                                    fc=fc, ec=ec, lw=1.8))
        ax.text(3.85, y1 - 0.28, title, ha='center', va='center', fontsize=11,
                fontweight='bold', color=ec)
        ax.text(3.85, (y0 + y1) / 2 + 0.10, chapters, ha='center', va='center',
                fontsize=8.6, color='#2c3e50')
        ax.text(3.85, (y0 + y1) / 2 - 0.28, core, ha='center', va='center',
                fontsize=9, color='#2c3e50', fontweight='bold')
        ax.text(3.85, y0 + 0.24, question, ha='center', va='center', fontsize=8.6,
                color=ec, fontstyle='italic')

    # 三编之间：一脉相承箭头
    ax.annotate('', xy=(7.45, 6.75), xytext=(7.45, 5.20),
                arrowprops=dict(arrowstyle='-|>', color='#7f8c8d', lw=1.6))
    ax.annotate('', xy=(7.45, 4.20), xytext=(7.45, 2.65),
                arrowprops=dict(arrowstyle='-|>', color='#7f8c8d', lw=1.6))
    ax.text(7.68, 5.98, '一脉相承', ha='center', va='center', fontsize=9,
            color='#7f8c8d', fontweight='bold', rotation=90)
    ax.text(7.68, 3.43, '一脉相承', ha='center', va='center', fontsize=9,
            color='#7f8c8d', fontweight='bold', rotation=90)

    # 右侧三重图景金字塔
    ax.text(9.55, 6.85, '共同愿景三重图景', ha='center', va='center', fontsize=10.5,
            fontweight='bold', color='#2c3e50')
    ax.add_patch(Polygon([(8.35, 4.15), (10.75, 4.15), (10.45, 4.75), (8.65, 4.75)],
                         closed=True, fc='#fadbd8', ec='#943126', lw=1.4))
    ax.text(9.55, 4.45, '幸福医院（基层）', ha='center', va='center', fontsize=9,
            color='#943126', fontweight='bold')
    ax.add_patch(Polygon([(8.75, 4.95), (10.35, 4.95), (10.10, 5.55), (9.00, 5.55)],
                         closed=True, fc='#d5f5e3', ec='#1e8449', lw=1.4))
    ax.text(9.55, 5.25, '和谐社会（中层）', ha='center', va='center', fontsize=9,
            color='#1e8449', fontweight='bold')
    ax.add_patch(Polygon([(9.15, 5.75), (9.95, 5.75), (9.82, 6.35), (9.28, 6.35)],
                         closed=True, fc='#d6eaf8', ec='#1f618d', lw=1.4))
    ax.text(9.55, 6.05, '人类命运\n共同体（顶层）', ha='center', va='center', fontsize=8,
            color='#1f618d', fontweight='bold')
    ax.text(9.55, 3.85, '同一愿景的不同尺度投影', ha='center', va='center', fontsize=8,
            color='#515a5a')

    fig.savefig(os.path.join(OUT, 'fig10-4.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('fig10-4 done')


# ================= fig10-5 Agent 自主循环（聚焦：五环节首尾相接闭环） =================
def fig10_5():
    fig, ax = plt.subplots(figsize=(8.8, 6.3))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6.6)
    ax.axis('off')

    nodes = [
        (5.0, 5.35, '感知', '四诊信息与械者观测', '#d6eaf8', '#1f618d'),
        (8.15, 3.55, '决策', '辨证论治，LLM 推理', '#d5f5e3', '#1e8449'),
        (6.65, 1.30, '行动', '开具处方与医嘱，工具调用', '#fdebd0', '#a04000'),
        (3.35, 1.30, '反馈', '疗效随访与依从观察', '#fadbd8', '#943126'),
        (1.85, 3.55, '学习', '经验沉淀与医案整理', '#e8daef', '#6c3483'),
    ]
    # 环：感知 → 决策 → 行动 → 反馈 → 学习 → 感知
    for i in range(len(nodes)):
        x1, y1 = nodes[i][0], nodes[i][1]
        x2, y2 = nodes[(i + 1) % len(nodes)][0], nodes[(i + 1) % len(nodes)][1]
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle='-|>', color='#2c3e50', lw=2.4,
                                    connectionstyle='arc3,rad=0.18'), zorder=2)

    for x, y, name, sub, fc, ec in nodes:
        ax.add_patch(FancyBboxPatch((x - 1.05, y - 0.62), 2.1, 1.24,
                                    boxstyle='round,pad=0.07', fc=fc, ec=ec, lw=1.8, zorder=3))
        ax.text(x, y + 0.30, name, ha='center', va='center', fontsize=12,
                fontweight='bold', color=ec, zorder=4)
        ax.text(x, y - 0.18, sub, ha='center', va='center', fontsize=8.6,
                color='#2c3e50', zorder=4, linespacing=1.25)

    # 中心说明：外回路快/内回路慢（细节并入图注，仅保留提示）
    ax.text(5.0, 2.65, '每一次诊疗即一圈', ha='center', va='center', fontsize=10,
            fontweight='bold', color='#c0392b')

    fig.savefig(os.path.join(OUT, 'fig10-5.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('fig10-5 done')


# ================= fig10-6 六者与 AI 平台：人机闭环 + CI/CD 进化（聚焦：中央平台六方交互 + 进化链） =================
def fig10_6():
    fig, ax = plt.subplots(figsize=(9.0, 7.8))
    ax.set_xlim(0, 10)
    ax.set_ylim(-1.0, 8.0)
    ax.axis('off')

    # 中央 tcmP 平台
    ax.add_patch(FancyBboxPatch((3.6, 4.2), 2.8, 2.0, boxstyle='round,pad=0.08',
                                fc='#d6eaf8', ec='#1f618d', lw=2.0, zorder=3))
    ax.text(5.0, 5.72, 'tcmP AI 平台', ha='center', va='center', fontsize=12,
            fontweight='bold', color='#1f618d', zorder=4)
    ax.text(5.0, 5.05, '大模型 + 疗效反馈学习', ha='center', va='center', fontsize=9.5,
            color='#2c3e50', zorder=4)
    ax.text(5.0, 4.55, '辨证引擎 · 疗效评价 · 质控规则', ha='center', va='center',
            fontsize=8.5, color='#2c3e50', zorder=4)

    # 六者环绕（六边形，与底部 CI/CD 链分离）
    actors = [
        (5.0, 7.0, '医者', '辨证经验\n获得推荐支持', '#d6eaf8', '#1f618d'),
        (8.3, 5.6, '患者', '疗效依从\n获得健康服务', '#fadbd8', '#943126'),
        (8.3, 2.6, '药者', '审方与不良反应\n获得用药知识', '#d5f5e3', '#1e8449'),
        (6.3, 1.3, '械者', '检验影像数据\n获得分析工具', '#d1f2eb', '#148f77'),
        (3.7, 1.3, '规者', '质控指标\n获得监督报表', '#fdebd0', '#a04000'),
        (1.7, 2.6, '法者', '合规规则\n获得留痕证据', '#e8daef', '#6c3483'),
    ]
    # 六方 → 平台 双向箭头
    for x, y, name, sub, fc, ec in actors:
        ax.annotate('', xy=(x, y), xytext=(5.0, 5.2),
                    arrowprops=dict(arrowstyle='<|-|>', color='#7f8c8d', lw=1.5,
                                    connectionstyle='arc3,rad=0.06'), zorder=2)
        ax.add_patch(FancyBboxPatch((x - 0.85, y - 0.55), 1.7, 1.1,
                                    boxstyle='round,pad=0.06', fc=fc, ec=ec, lw=1.5, zorder=3))
        ax.text(x, y + 0.18, name, ha='center', va='center', fontsize=10,
                fontweight='bold', color=ec, zorder=4)
        ax.text(x, y - 0.22, sub, ha='center', va='center', fontsize=7.2,
                color='#2c3e50', zorder=4, linespacing=1.15)

    # 底部 CI/CD 进化闭环：对话→日志→图谱→调优→自动上线→服务→对话
    steps = ['对话', '日志', '图谱', '调优', '自动上线']
    xs = [1.2, 2.9, 4.6, 6.3, 8.0]
    for i in range(len(xs) - 1):
        ax.annotate('', xy=(xs[i + 1] - 0.55, -0.35), xytext=(xs[i] + 0.55, -0.35),
                    arrowprops=dict(arrowstyle='-|>', color='#b7950b', lw=2.0), zorder=2)
    for i, (x, st) in enumerate(zip(xs, steps)):
        ax.add_patch(FancyBboxPatch((x - 0.55, -0.58), 1.1, 0.46, boxstyle='round,pad=0.05',
                                    fc='#fef9e7', ec='#b7950b', lw=1.4, zorder=3))
        ax.text(x, -0.35, st, ha='center', va='center', fontsize=8.5,
                color='#7d6608', fontweight='bold', zorder=4)
    # 服务节点（回折）→ 对话，形成闭环
    ax.add_patch(FancyBboxPatch((3.45, -0.98), 1.1, 0.46, boxstyle='round,pad=0.05',
                                fc='#fef9e7', ec='#b7950b', lw=1.4, zorder=3))
    ax.text(4.0, -0.75, '服务', ha='center', va='center', fontsize=8.5,
            color='#7d6608', fontweight='bold', zorder=4)
    ax.annotate('', xy=(8.0, -0.35), xytext=(4.05, -0.60),
                arrowprops=dict(arrowstyle='-|>', color='#b7950b', lw=2.0), zorder=2)
    ax.annotate('', xy=(1.2, -0.35), xytext=(3.95, -0.60),
                arrowprops=dict(arrowstyle='-|>', color='#b7950b', lw=2.0), zorder=2)
    ax.text(6.0, 0.45, 'CI/CD 进化闭环：服务 → 数据 → 共识 → 服务', ha='center', va='center',
            fontsize=8.6, color='#7d6608', fontweight='bold')

    fig.savefig(os.path.join(OUT, 'fig10-6.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('fig10-6 done')


# ================= fig10-7 算力与智能特征（聚焦：'足够算力阈值' 跃升段） =================
def fig10_7():
    fig, ax = plt.subplots(figsize=(8.8, 5.0))
    # 聚焦阈值附近：x 40-100，阈值 x=70
    ax.set_xlim(36, 106)
    ax.set_ylim(-0.35, 1.18)
    ax.axis('off')

    xs = [x for x in range(38, 102, 1)]
    ys = [1.0 / (1.0 + math.exp(-(x - 70) / 4.0)) for x in xs]

    # 平台期 / 跃升期 底色
    ax.add_patch(Rectangle((38, -0.08), 32, 1.2, fc='#f2f3f4', ec='none', alpha=0.6))
    ax.add_patch(Rectangle((70, -0.08), 32, 1.2, fc='#fef9e7', ec='none', alpha=0.7))

    # 阈值竖虚线
    ax.plot([70, 70], [-0.06, 1.06], color='#7f8c8d', lw=2.2, linestyle='--')
    ax.text(70, 1.10, '“足够算力阈值”', ha='center', va='center', fontsize=10.5,
            color='#7f8c8d', fontweight='bold')

    # S 形曲线（聚焦跃升段）
    ax.plot(xs, ys, color='#1f618d', lw=2.8)

    # 区域标注
    ax.text(54, 0.16, '平台期：规则系统与\n人工特征工程为主', ha='center', va='center',
            fontsize=9, color='#515a5a')
    ax.text(86, 0.86, '跃升期：自主学习·泛化\n自适应·涌现相继显现', ha='center', va='center',
            fontsize=9, color='#1e8449', fontweight='bold')

    # 数轴（对数刻度示意，只标数量级）
    ax.annotate('', xy=(98, -0.06), xytext=(40, -0.06),
                arrowprops=dict(arrowstyle='-|>', color='#333333', lw=1.5))
    ax.text(99.0, -0.08, '计算量/算力（对数刻度示意）', ha='center', va='center', fontsize=9.5)
    for x in [40, 55, 70, 85, 100]:
        ax.plot([x, x], [-0.09, -0.03], color='#333333', lw=1.2)
        ax.text(x, -0.16, str(x), ha='center', va='center', fontsize=8.5)
    # 纵轴
    ax.annotate('', xy=(38.5, 1.0), xytext=(38.5, -0.02),
                arrowprops=dict(arrowstyle='-|>', color='#333333', lw=1.5))
    ax.text(37.2, 0.52, '智能能力', ha='center', va='center', fontsize=9.5, rotation=90)
    for y in [0.0, 0.5, 1.0]:
        ax.plot([38.0, 38.6], [y, y], color='#333333', lw=1.2)
        ax.text(37.6, y, f'{y:g}', ha='right', va='center', fontsize=8.5)

    fig.savefig(os.path.join(OUT, 'fig10-7.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('fig10-7 done')


if __name__ == '__main__':
    assert_numbers()
    fig10_1()
    fig10_2()
    fig10_3()
    fig10_4()
    fig10_5()
    fig10_6()
    fig10_7()
    print('== 聚焦重绘完成：figures/ch10/fig10-1.png ~ fig10-7.png ==')
