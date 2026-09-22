# -*- coding: utf-8 -*-
"""《中医场景强化学习》结构类教材图 Graphviz 重绘（费曼式节点-连线风格）

重绘 5 幅结构类图：
  fig1-6 双向映射环（ch01，外环中医五元素 ⇄ 内环 RL 五概念，红蓝径向双向箭头）
  fig2-1 MDP 五元组环（ch02，五元组环 + 中心诊疗循环 + 底部轨迹链）
  fig5-3 策略迭代循环（ch05，①初始化→②评估→③改进→④判敛，红回环/绿出口）
  fig5-5 统一算法循环（ch05，三角主循环 + 中央徽章 + 底部三实例卡，绿收敛出口）
  fig6-4 进化闭环（ch06，①对话→②日志→③更新→④服务闭环 + 中央圆 + 底部四条实现路径）

风格约束（与正文图注四要素一致）：
  - 节点=状态/概念（白底黑框为主，浅绿/浅蓝低饱和填充仅用于图注指定的盒）
  - 边=转移/关系，箭头定方向；关键数值/符号标注在节点与边上
  - 黑白灰线稿为主，1-2 种低饱和色点缀，且颜色与图注颜色词一致
    （fig1-6 浅绿盒/浅蓝盒/红蓝箭头；fig5-3 红回环/绿出口；fig5-5 绿出口；
     fig6-4 四条彩色实线箭头）
  - 中文 fontname='SimHei'；避免 SimHei 缺字形（U+2212 −、U+2081 下标、U+21C4 ⇄、
    U+207B ⁻¹），用 ASCII '-' 与直写下标（vπk、πk+1、^-1）
  - label 一律纯文本（\n 换行），不用 HTML-like label（Graphviz 16 以 XML 解析，
    含标签 label 必须以合法标签开头，纯文本最稳）
  - 环类图用 neato 固定坐标（pos 带 !），流程类图用 dot rankdir
输出：figures/chNN/figN-X.png（覆盖旧图），dpi=200。
"""
import os
import math

# 关键：Graphviz 绑定查找 dot 依赖 PATH，必须前置 dot 目录
os.environ['PATH'] = (r'C:\Tools\graphviz\Graphviz-16.0.0-win64\bin'
                      + os.pathsep + os.environ.get('PATH', ''))

import graphviz

BASE = os.path.dirname(os.path.abspath(__file__))  # .../drafts/cmrl/figures
FONT = 'SimHei'

# ---------- 费曼风格调色板（黑白灰 + 低饱和点缀，与图注颜色词对齐） ----------
INK    = '#111111'   # 主黑（文字/主框）
GRAY   = '#666666'   # 次灰（次要线/次要文字）
LGRAY  = '#999999'   # 浅灰（虚线/辅助）
RED    = '#a35555'   # 低饱和红（fig1-6 映射箭头 / fig5-3 回环）
BLUE   = '#5b7d9e'   # 低饱和蓝（fig1-6 反哺箭头 / fig2-1 环边）
GREEN  = '#6b8e6b'   # 低饱和绿（fig5-3 / fig5-5 收敛出口）
ORANGE = '#b07a4f'   # 低饱和橙（fig6-4 服务→对话边）
GREEN_FILL = '#eef5ee'  # 浅绿（sat≈0.03 < 0.10，不计彩）
BLUE_FILL  = '#edf2f8'  # 浅蓝（sat≈0.04 < 0.10，不计彩）
GRAY_FILL  = '#f5f5f5'  # 浅灰（通用）

DPI = '200'

BASE_NODE = dict(fontname=FONT, fontsize='11', shape='box', style='filled',
                 fillcolor='white', color=INK, penwidth='1.5',
                 margin='0.16,0.09')
BASE_EDGE = dict(fontname=FONT, fontsize='9.5', color=GRAY, penwidth='1.3')


def deg2xy(radius, deg):
    """极坐标→笛卡尔坐标（度，0°=右，逆时针），返回 'x,y!' 字符串"""
    a = math.radians(deg)
    return f'{radius * math.cos(a):.3f},{radius * math.sin(a):.3f}!'


def new_graph(engine, name):
    g = graphviz.Digraph(name, engine=engine, format='png')
    g.graph_attr.update(bgcolor='white', dpi=DPI, splines='line',
                        nodesep='0.35', ranksep='0.45')
    g.node_attr.update(**BASE_NODE)
    g.edge_attr.update(**BASE_EDGE)
    return g


def render(g, outpath):
    g.render(outfile=outpath, cleanup=True)
    from PIL import Image
    im = Image.open(outpath)
    print(f'  {os.path.basename(outpath)} -> {im.size[0]}x{im.size[1]}px')
    return im.size


# =====================================================================
# fig1-6 中医临床元素与强化学习概念：双向映射环（ch01）
#   图注 b：外环五个浅绿盒=中医临床元素，内环五个浅蓝盒=RL 概念，
#           红蓝径向双向箭头为"映射⇄反哺"；c：S 状态(四诊症状)、π 策略(辨证论治)、
#           A 动作(治法方剂)、R 奖励(疗效反馈)、P 状态转移(病邪传变)
# =====================================================================
def fig1_6():
    g = new_graph('neato', 'fig1-6')
    g.graph_attr.update(splines='line', overlap='false')

    # 外环：中医临床元素（浅绿盒）
    tcm = [  # (id, label, deg)
        ('T1', '四诊症状\n(S 状态)', 90),
        ('T2', '辨证论治\n(π 策略)', 162),
        ('T3', '治法方剂\n(A 动作)', 234),
        ('T4', '疗效反馈\n(R 奖励)', 306),
        ('T5', '病邪传变\n(P 状态转移)', 18),
    ]
    # 内环：强化学习概念（浅蓝盒）
    rl = [  # (id, label, deg)
        ('S', 'S\n状态 state', 90),
        ('PI', 'π\n策略 policy', 162),
        ('A', 'A\n动作 action', 234),
        ('R', 'R\n奖励 reward', 306),
        ('P', 'P\n状态转移\nstate transition', 18),
    ]
    for nid, lab, deg in tcm:
        g.node(nid, label=lab, pos=deg2xy(3.7, deg),
               fillcolor=GREEN_FILL, color='#5f8f6a')
    for nid, lab, deg in rl:
        g.node(nid, label=lab, pos=deg2xy(2.0, deg),
               fillcolor=BLUE_FILL, color=BLUE, fontsize='10.5')

    # 红蓝径向双向箭头：中医→RL 红（映射），RL→中医 蓝（反哺）
    pairs = [('T1', 'S'), ('T2', 'PI'), ('T3', 'A'), ('T4', 'R'), ('T5', 'P')]
    for ti, ri in pairs:
        g.edge(ti, ri, color=RED, penwidth='1.6')   # 映射（红）
        g.edge(ri, ti, color=BLUE, penwidth='1.6')  # 反哺（蓝）
    return g


# =====================================================================
# fig2-1 健康演化决策过程模型：五元组环图与诊疗循环（ch02）
#   图注：②环向箭头线=诊疗循环（观察—决策—反馈—再观察），底部轨迹链=病程推进 s1→s2→s3；
#         ③S 状态集/A 动作集/P 转移概率/R 奖励函数/γ 折扣率，
#           St 此刻证候、At 此刻处方、Rt+1 复诊疗效；④中心诊疗循环框与五元组环对应
# =====================================================================
def fig2_1():
    g = new_graph('neato', 'fig2-1')
    g.graph_attr.update(splines='line', overlap='false')

    ring = [  # (id, label, deg)
        ('S', 'S 状态集\nSt=此刻证候', 90),
        ('A', 'A 动作集\nAt=此刻处方', 162),
        ('P', 'P 转移概率\n证候传变', 234),
        ('R', 'R 奖励函数\nRt+1=复诊疗效', 306),
        ('G', 'γ 折扣率\nγ = 0.9', 18),
    ]
    for nid, lab, deg in ring:
        g.node(nid, label=lab, pos=deg2xy(2.9, deg), fillcolor=GRAY_FILL)

    # 中心诊疗循环框（图注④：一次完整诊疗=一次决策过程）
    g.node('CYC', '诊疗循环\n观察—决策—反馈—再观察',
           pos='0,0!', fillcolor='white', color=GREEN, style='filled,dashed',
           fontsize='10.5')
    # 中心框 ↔ 环节点 对应虚线（观察/决策/反馈）
    g.edge('CYC', 'S', style='dashed', color=LGRAY, label='观察')
    g.edge('CYC', 'A', style='dashed', color=LGRAY, label='决策')
    g.edge('CYC', 'R', style='dashed', color=LGRAY, label='反馈')

    # 五元组环向边（顺时针：诊疗循环方向）
    ring_order = ['S', 'A', 'P', 'R', 'G']
    for i in range(5):
        g.edge(ring_order[i], ring_order[(i + 1) % 5],
               color=BLUE, penwidth='1.5')

    # 底部轨迹链：病程推进 s1 → s2 → s3（a=动作, r=奖励）
    g.node('s1', 's1', pos='-1.5,-4.4!', fillcolor='white',
           fontsize='11', shape='circle', style='filled', penwidth='1.5')
    g.node('s2', 's2', pos='0,-4.4!', fillcolor='white',
           fontsize='11', shape='circle', style='filled', penwidth='1.5')
    g.node('s3', 's3', pos='1.5,-4.4!', fillcolor='white',
           fontsize='11', shape='circle', style='filled', penwidth='1.5')
    g.edge('s1', 's2', label='a1, r2', color=INK)
    g.edge('s2', 's3', label='a2, r3', color=INK)
    g.node('TR', '轨迹链：病程推进', pos='0,-4.05!', shape='plaintext',
           fontsize='9', fontcolor=GRAY)
    return g


# =====================================================================
# fig5-3 策略迭代循环（ch05，dot rankdir=TB 流程）
#   图注：纵向实线箭头 ①→②→③→④；红色回环箭头=否（πk+1≠πk）→回②再评估；
#         绿色箭头=是→输出最优策略（终止）；右侧徽章 定理5.2/5.3
# =====================================================================
def fig5_3():
    g = new_graph('dot', 'fig5-3')
    g.graph_attr.update(rankdir='TB', splines='spline', nodesep='0.45',
                        ranksep='0.55')

    g.node('init', '① 初始化\n任取策略 π0', fillcolor='white')
    g.node('eval', '② 策略评估\nvπk = (I - γPπk)^-1 rπk', fillcolor='white')
    g.node('impr', "③ 策略改进\nπk+1(s) = argmax_a [r(s,a) + γΣ p(s'|s,a) vπk(s')]",
           fillcolor='white')
    g.node('judge', '④ πk+1 = πk\n对一切 s 成立？',
           shape='diamond', fillcolor='white', fontsize='10.5')
    g.node('out', '输出最优策略 π*', fillcolor='white', color=GREEN,
           penwidth='1.8')

    # 主链 ①→②→③→④
    g.edge('init', 'eval', color=INK, penwidth='1.6')
    g.edge('eval', 'impr', color=INK, penwidth='1.6')
    g.edge('impr', 'judge', color=INK, penwidth='1.6')
    # 红色回环：否 → 回②再评估
    g.edge('judge', 'eval', label='否：πk+1 ≠ πk',
           color=RED, penwidth='1.6', constraint='false')
    # 绿色出口：是 → 输出最优策略
    g.edge('judge', 'out', label='是', color=GREEN, penwidth='1.8')

    # 右侧徽章：定理5.2 / 定理5.3（灰色虚线簇，与 judge 同行）
    with g.subgraph(name='cluster_badges') as c:
        c.attr(label='', style='dashed', color=LGRAY, fontname=FONT, penwidth='1.0')
        c.node('th52', '定理5.2\n价值单调不降', fillcolor=GRAY_FILL,
               color=LGRAY, fontsize='9.5')
        c.node('th53', '定理5.3\n有限步终止', fillcolor=GRAY_FILL,
               color=LGRAY, fontsize='9.5')
        c.edge('th52', 'th53', style='invis')
    g.edge('judge', 'th52', style='invis')
    return g


# =====================================================================
# fig5-5 统一算法循环：评估 → 改进 → 再评估（ch05，neato 三角 + 三卡）
#   图注：三角形三条弧线箭头=主循环（①评估→②改进→③再评估→否回①）；
#         绿色实线箭头=收敛出口（判据成立→输出最优策略/价值）；
#         中央圆徽章"统一算法循环：评估—改进—再评估"；底部三实例卡
# =====================================================================
def fig5_5():
    g = new_graph('neato', 'fig5-5')
    g.graph_attr.update(splines='curved', overlap='false')

    g.node('eval', '① 评估\n按当前价值估计\n每个状态/动作的好坏',
           pos='-2.4,1.35!', fillcolor=GRAY_FILL)
    g.node('impr', '② 改进\n向价值最大的方向\n更新策略或价值',
           pos='2.4,1.35!', fillcolor=GRAY_FILL)
    g.node('reval', '③ 再评估\n检验是否达到\n收敛判据',
           pos='0,-1.55!', fillcolor=GRAY_FILL)

    # 中央圆徽章
    g.node('BADGE', '统一算法循环\n评估—改进—再评估',
           pos='0,0!', shape='circle', fillcolor='white', color=INK,
           fontsize='9.5', penwidth='1.6')

    # 三角主循环（弧线）
    g.edge('eval', 'impr', label='①', color=INK, penwidth='1.6')
    g.edge('impr', 'reval', label='②', color=INK, penwidth='1.6')
    g.edge('reval', 'eval', label='③ 否：未达判据', color=INK, penwidth='1.6')

    # 绿色收敛出口
    g.node('out', '输出最优策略/价值', pos='3.1,-1.9!', fillcolor='white',
           color=GREEN, penwidth='1.8')
    g.edge('reval', 'out', label='是：判据成立', color=GREEN, penwidth='1.8')

    # 底部三张实例卡（对应正文 5.4/5.5/第6章；黑白灰线稿为主，卡仅浅色底+灰框）
    g.node('VI', '价值迭代（5.4）\n评估一步即改进\nvk+1 = max_a qk\n判据：max_s |vk+1 - vk| < ε\nγ=0.9 时约 44 轮达 1% 精度',
           pos='-4.2,-3.7!', fillcolor=BLUE_FILL, color=BLUE, fontsize='9.5')
    g.node('PI', '策略迭代（5.5）\n评估到底再改进\nvπ = (I - γPπ)^-1 rπ\n判据：πk+1 = πk 对一切 s\n定理5.2 单调不降 / 定理5.3 有限步终止',
           pos='0,-3.7!', fillcolor=GREEN_FILL, color='#5f8f6a', fontsize='9.5')
    g.node('TD', '时序差分（第6章）\n把"期望"换成"样本平均"\nv ← v + αδ\n无模型地从轨迹数据学习',
           pos='4.2,-3.7!', fillcolor='white', color=LGRAY, fontsize='9.5')
    return g


# =====================================================================
# fig6-4 在线学习进化闭环：系统自适应（ch06）
#   图注 b：顺时针四条彩色实线箭头 ①对话→②日志→③更新→④服务→回①；
#          c：①对话/②日志/③更新(TD v←v+α(目标-旧值))/④服务；中央圆"在线进化"；
#          底部横带四条实现路径（增量更新、探索-利用平衡、基线校准、反馈校准）
# =====================================================================
def fig6_4():
    g = new_graph('neato', 'fig6-4')
    g.graph_attr.update(splines='curved', overlap='false')

    # 四节点（正方形四角，顺时针）
    g.node('D', '① 对话\n患者与医者 Agent 交互\n产生"症状—辨证—反馈"\n一步经验',
           pos='-3.0,1.9!', fillcolor=GRAY_FILL)
    g.node('L', '② 日志\n状态、动作、奖励、误差\n写入进化记录\n每一步都有账可查',
           pos='3.0,1.9!', fillcolor=GRAY_FILL)
    g.node('U', '③ 更新\nTD 增量更新\nv ← v + α(目标 - 旧值)\n无需等待批量积累',
           pos='3.0,-1.9!', fillcolor=GRAY_FILL)
    g.node('S', '④ 服务\n价值表刷新\n改进后的辨证与推荐\n反哺临床',
           pos='-3.0,-1.9!', fillcolor=GRAY_FILL)

    # 顺时针四条彩色实线箭头（红→蓝→绿→橙）
    g.edge('D', 'L', color=RED, penwidth='1.7')
    g.edge('L', 'U', color=BLUE, penwidth='1.7')
    g.edge('U', 'S', color=GREEN, penwidth='1.7')
    g.edge('S', 'D', color=ORANGE, penwidth='1.7')

    # 中央圆：在线进化
    g.node('EVO', '在线进化\n走一步看一步\n边走边修正',
           pos='0,0!', shape='circle', fillcolor='white', color=INK,
           fontsize='10', penwidth='1.6')

    # 底部横带：四条实现路径
    paths = [('p1', '增量更新'), ('p2', '探索-利用平衡'),
             ('p3', '基线校准'), ('p4', '反馈校准')]
    for i, (pid, lab) in enumerate(paths):
        x = -4.35 + i * 2.9
        g.node(pid, lab, pos=f'{x:.2f},-3.6!', fillcolor='white',
               color=LGRAY, penwidth='1.2', fontsize='9.5', shape='box',
               style='filled,dashed')
    g.node('PT', '四条实现路径', pos='-5.0,-3.6!', shape='plaintext',
           fontsize='9', fontcolor=GRAY)
    return g


def main():
    os.makedirs(os.path.join(BASE, 'ch01'), exist_ok=True)
    os.makedirs(os.path.join(BASE, 'ch02'), exist_ok=True)
    os.makedirs(os.path.join(BASE, 'ch05'), exist_ok=True)
    os.makedirs(os.path.join(BASE, 'ch06'), exist_ok=True)

    jobs = [
        ('fig1-6 双向映射环', fig1_6, os.path.join(BASE, 'ch01', 'fig1-6.png')),
        ('fig2-1 五元组环+诊疗循环', fig2_1, os.path.join(BASE, 'ch02', 'fig2-1.png')),
        ('fig5-3 策略迭代循环', fig5_3, os.path.join(BASE, 'ch05', 'fig5-3.png')),
        ('fig5-5 统一算法循环', fig5_5, os.path.join(BASE, 'ch05', 'fig5-5.png')),
        ('fig6-4 进化闭环', fig6_4, os.path.join(BASE, 'ch06', 'fig6-4.png')),
    ]
    for name, fn, out in jobs:
        print('生成', name)
        g = fn()
        render(g, out)


if __name__ == '__main__':
    main()
