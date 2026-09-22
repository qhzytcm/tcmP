# -*- coding: utf-8 -*-
"""《中医场景强化学习》第10章 结构类教材图 Graphviz 重绘脚本（图表工程师）

按【费曼式节点-连线】风格用 Graphviz 重绘 4 幅结构类图：
  fig10-1  AC 架构（行动者-评价者，10.1.1 节末）—— dot 分层三角布局
  fig10-3  六者协同闭环（医患药械规法，10.6.1 节末）—— neato 固定坐标规则六边形
  fig10-5  Agent 循环（感知-决策-行动-反馈-学习，10.6.2 节末）—— neato 固定坐标五边形环
  fig10-6  人机闭环与 CI/CD 进化（六者与 tcmP 平台，10.8.2 节末）—— neato 固定坐标星型+链

语义依据：正文 md 图注四要素（ch10/01-1.1.md、06-1.6.md、08-1.8.md）与
chapter-10-figures.md 颜色对齐登记；颜色词与图注一致（10-5 图注无颜色词→全图黑白灰）。
规范：Digraph、节点=角色/环节、边=交互/流程、箭头定方向、数值/符号标注在节点与边上、
fontname='SimHei'（HTML label 内 FONT FACE="SimHei"，双层尖括号 <<...>>）、
黑白灰为主+低饱和点缀、format='png'、dpi=200；
os.environ['PATH'] 前置 dot 目录（Graphviz 16.0.0，dot.exe）。
输出：figures/ch10/fig10-1.png、fig10-3.png、fig10-5.png、fig10-6.png（覆盖）
验证：PNG 生成、尺寸>=600px、彩色占比<5%（HSV S>0.12 判定）
"""
import os

# 用户要求：PATH 前置 dot 目录（Graphviz 16.0.0）
DOT_DIR = r'C:\Tools\graphviz\Graphviz-16.0.0-win64\bin'
os.environ['PATH'] = DOT_DIR + os.pathsep + os.environ.get('PATH', '')

import graphviz
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, '..', 'figures', 'ch10'))
os.makedirs(OUT, exist_ok=True)

# ---------- 调色板（低饱和，与正文图注颜色词一致） ----------
BLACK = '#1a1a1a'
DARK = '#333333'
GRAY = '#666666'
LGRAY = '#999999'
BLUE = '#4a6785'     # 蓝（低饱和灰蓝）
GREEN = '#5d7a5e'    # 绿（低饱和灰绿）
RED = '#a0514e'      # 红（低饱和砖红）
ORANGE = '#a86f3f'   # 橙（低饱和土橙）
GOLD = '#a8833a'     # 金（低饱和金黄）
PURPLE = '#7a6787'   # 紫（低饱和灰紫）
CYAN = '#5d8a88'     # 青（低饱和青灰）
BG_GRAY = '#e8e8e8'
BG_BLUE = '#e4e8ee'
BG_GREEN = '#e5eae3'
BG_ORANGE = '#f0e6d8'
BG_RED = '#f0e5e4'
BG_GOLD = '#f0e8d6'
BG_PURPLE = '#ece7ef'
BG_CYAN = '#e5eae8'

FONT = 'SimHei'


def H(inner, size=12, bold=False):
    """HTML-like label 包装：强制 SimHei 字体（Graphviz HTML label 不继承 graph fontname）。

    注意 Graphviz 16.0.0 要求 HTML-like label 用双层尖括号 label=<<...>>（实测单层报语法错）。
    """
    b = '<B>' if bold else ''
    be = '</B>' if bold else ''
    return '<<FONT FACE="%s" POINT-SIZE="%d">%s%s%s</FONT>>' % (FONT, size, b, inner, be)


def new_graph(name, engine='dot'):
    g = graphviz.Digraph(name, format='png', engine=engine)
    g.graph_attr.update(dpi='200', bgcolor='white', fontname=FONT, splines='spline')
    return g


def rnode(g, name, label, fillcolor='white', color=BLACK, penwidth=1.6,
          shape='box', style='rounded,filled', fontsize=12, pos=None,
          extra=None):
    attrs = dict(label=label, fontname=FONT, fontsize=str(fontsize), shape=shape,
                 style=style, fillcolor=fillcolor, color=color, penwidth=str(penwidth))
    if pos:
        attrs['pos'] = '%g,%g!' % pos
    if extra:
        attrs.update(extra)
    g.node(name, **attrs)


def redge(g, a, b, label=None, color=GRAY, penwidth=1.3, dirn='forward',
          constraint=True, fontcolor=None, style=None, fontsize=10):
    attrs = dict(color=color, penwidth=str(penwidth), fontname=FONT, fontsize=str(fontsize))
    if dirn == 'both':
        attrs['dir'] = 'both'
    elif dirn == 'none':
        attrs['dir'] = 'none'
    if label is not None:
        attrs['label'] = label
    if fontcolor:
        attrs['fontcolor'] = fontcolor
    else:
        attrs['fontcolor'] = color
    if style:
        attrs['style'] = style
    if not constraint:
        attrs['constraint'] = 'false'
    g.edge(a, b, **attrs)


# ============================================================
# 图 10-1 决策与评价分离架构（10.1.1 节末）—— neato 固定坐标
# 节点：浅蓝框=医者（辨证开方）、浅橙框=规者（质控）与药者（审方）、浅灰框=环境
#      （患者与医院场景）——图体只保留中医角色与流程（图注 c）
# 边：红色粗箭头=规者/药者向医者回传疗效预判；蓝色细箭头=当前证候与治法方剂环流；
#     橙色细箭头=复诊疗效与后继证候的回传（图注 b）
# 坐标（英寸，Graphviz neato pos 单位为英寸）
# ============================================================
def fig10_1():
    g = new_graph('fig10-1', engine='neato')

    rnode(g, 'doctor',
          H('医者<BR/>辨证开方<BR/><BR/>处方水平随<BR/>临证积累而精进', size=11),
          fillcolor=BG_BLUE, color=BLUE, penwidth=2.2, pos=(0.0, 1.9))
    rnode(g, 'regulator',
          H('规者<BR/>质控<BR/><BR/>评价标准随<BR/>随访数据而校准', size=11),
          fillcolor=BG_ORANGE, color=ORANGE, penwidth=2.2, pos=(3.1, 1.0))
    rnode(g, 'pharmacist',
          H('药者<BR/>审方<BR/><BR/>评价标准随<BR/>随访数据而校准', size=11),
          fillcolor=BG_ORANGE, color=ORANGE, penwidth=2.2, pos=(3.1, -1.0))
    rnode(g, 'env',
          H('环境（患者与医院场景）<BR/>当前证候（四诊信息）→ 治法方剂 → '
            '复诊疗效（随访反馈）', size=10),
          fillcolor=BG_GRAY, color=LGRAY, penwidth=1.6, pos=(0.0, -2.1))

    # 红色粗箭头：规者/药者 → 医者（疗效预判回传）
    redge(g, 'regulator', 'doctor', label=H('疗效预判', size=11, bold=True),
          color=RED, penwidth=3.2)
    redge(g, 'pharmacist', 'doctor', label=H('疗效预判', size=11, bold=True),
          color=RED, penwidth=3.2)
    # 蓝色细箭头：当前证候与治法方剂环流（双向）
    redge(g, 'env', 'doctor', label=H('当前证候', size=10), color=BLUE,
          penwidth=1.6)
    redge(g, 'doctor', 'env', label=H('治法方剂', size=10), color=BLUE,
          penwidth=1.6)
    # 橙色细箭头：复诊疗效与后继证候回传
    redge(g, 'env', 'regulator',
          label=H('复诊疗效与后继证候', size=9.5), color=ORANGE, penwidth=1.6)
    redge(g, 'env', 'pharmacist',
          label=H('复诊疗效与后继证候', size=9.5), color=ORANGE, penwidth=1.6)
    return g


# ============================================================
# 图 10-3 六者协同与幸福闭环（10.6.1 节末）—— neato 固定坐标规则六边形
# 节点：六色圆角框=医患药械规法（算法映射）、中央暖色圆=幸福闭环（图注 c）
# 边：灰色细线=六方相邻环线；红色加粗双向箭头=医—患 reward 回路；
#     绿/橙/紫/青细箭头=责任分离、独立评价、全程留痕、状态观测（图注 b）
# 坐标（英寸，Graphviz neato pos 单位为英寸）：正六边形半径 R=2.2in；
#   医(0,R) 患(R√3/2,R/2) 药(R√3/2,-R/2) 械(0,-R) 规(-R√3/2,-R/2) 法(-R√3/2,R/2)
#   中央幸福闭环(0,0)
# ============================================================
def fig10_3():
    g = new_graph('fig10-3', engine='neato')
    R = 2.2
    a = R * 0.8660254038   # R*√3/2
    b = R * 0.5

    roles = {
        'yi':   ('医者<BR/>辨证开方', BG_BLUE, BLUE, (0.0, R)),
        'huan': ('患者<BR/>疗效与依从是最终裁判', BG_GREEN, GREEN, (a, b)),
        'yao':  ('药者<BR/>审方与调剂', BG_ORANGE, ORANGE, (a, -b)),
        'xie':  ('械者<BR/>影像检验', BG_CYAN, CYAN, (0.0, -R)),
        'gui':  ('规者<BR/>质控与流程监督', BG_PURPLE, PURPLE, (-a, -b)),
        'fa':   ('法者<BR/>知情同意与责任认定', BG_RED, RED, (-a, b)),
    }
    for k, (lbl, fc, ec, pos) in roles.items():
        rnode(g, k, H(lbl, size=11), fillcolor=fc, color=ec, penwidth=1.8, pos=pos)

    # 中央暖色圆=幸福闭环（健康共同体）
    rnode(g, 'hub', H('幸福闭环<BR/>健康共同体', size=11, bold=True),
          fillcolor=BG_ORANGE, color=ORANGE, penwidth=2.4, shape='circle', pos=(0.0, 0.0))

    # 灰色细线：六方相邻环线（环环相扣，dir=none 顺时针）
    ring = ['yi', 'huan', 'yao', 'xie', 'gui', 'fa']
    for i in range(len(ring)):
        redge(g, ring[i], ring[(i + 1) % len(ring)], color=GRAY, penwidth=1.0, dirn='none')

    # 红色加粗双向箭头：医—患 疗效回路
    redge(g, 'yi', 'huan',
          label=H('疗效回路：信任→依从→疗效→信任', size=10, bold=True),
          color=RED, penwidth=3.2, dirn='both')

    # 四条机制连线（绿/橙/紫/青细箭头，指向医者）
    redge(g, 'yao', 'yi', label=H('责任分离', size=10), color=GREEN, penwidth=1.6)
    redge(g, 'gui', 'yi', label=H('独立评价', size=10), color=ORANGE, penwidth=1.6)
    redge(g, 'fa', 'yi', label=H('全程留痕', size=10), color=PURPLE, penwidth=1.6)
    redge(g, 'xie', 'yi', label=H('状态观测', size=10), color=CYAN, penwidth=1.6)
    return g


# ============================================================
# 图 10-5 Agent 自主循环：感知→决策→行动→反馈→学习（10.6.2 节末）
#   —— neato 固定坐标五边形闭环；图注无颜色词 → 全图黑白灰
# 节点：五个圆角框（感知/决策/行动/反馈/学习，LLM/记忆/工具支撑）+ 中心节奏提示
# 边：粗循环箭头=五环节首尾相接；学习→感知 闭合箭头=进入下一轮
# 坐标（英寸）：五边形半径 R=2.9in，感知(0,R) 决策(R*sin72,R*cos72) 行动(R*sin144,R*cos144)
#               反馈(R*sin216,R*cos216) 学习(R*sin288,R*cos288)；中心文字(0,0)
# ============================================================
def fig10_5():
    g = new_graph('fig10-5', engine='neato')
    import math
    R = 2.9
    # 五边形顶点（顺时针，角度按 y 向上计算：感知在顶）
    pts = {}
    for i, name in enumerate(['perceive', 'decide', 'act', 'feedback', 'learn']):
        ang = math.radians(90 + 72 * i)          # 90° 起顺时针 72° 一步
        pts[name] = (R * math.cos(ang), R * math.sin(ang))

    nodes = {
        'perceive': '感知<BR/>四诊信息与械者观测',
        'decide':   '决策<BR/>辨证论治，LLM 推理',
        'act':      '行动<BR/>开具处方与医嘱，工具调用',
        'feedback': '反馈<BR/>疗效随访与依从观察',
        'learn':    '学习<BR/>经验沉淀与医案整理',
    }
    for name, lbl in nodes.items():
        rnode(g, name, H(lbl, size=11), fillcolor='white', color=BLACK, penwidth=2.0,
              pos=pts[name])

    # 中心节奏提示（外回路：每一次诊疗即一圈）
    rnode(g, 'loopnote', H('每一次诊疗即一圈', size=13, bold=True),
          shape='plaintext', style='', fillcolor='white', color=DARK, penwidth=0,
          pos=(0.0, 0.0))

    # 粗循环箭头：感知→决策→行动→反馈→学习→感知（首尾相接，学习→感知为闭合）
    loop = ['perceive', 'decide', 'act', 'feedback', 'learn']
    for i in range(len(loop)):
        redge(g, loop[i], loop[(i + 1) % len(loop)], color=DARK, penwidth=2.4)
    return g


# ============================================================
# 图 10-6 六者与 AI 平台：人机闭环与 CI/CD 进化（10.8.2 节末）
#   —— neato 固定坐标：中央平台+六方环绕（星型）+ 底部 CI/CD 金色闭环链
# 节点：中央蓝框=tcmP AI 平台；六色小框=医患药械规法（各注贡献与所得）（图注 c）
# 边：双向箭头=人机闭环双向交互（上行贡献经验/数据/规则，下行获得推荐/服务/报表）；
#     下方金色闭环链=CI/CD 进化闭环（对话→日志→图谱→调优→自动上线→服务→再回到对话）（图注 b）
# ============================================================
def fig10_6():
    g = new_graph('fig10-6', engine='neato')

    # 中央蓝框=tcmP AI 平台
    rnode(g, 'platform',
          H('tcmP AI 平台<BR/><B>大模型 + 疗效反馈学习</B><BR/>'
            '（辨证引擎 · 疗效评价 · 质控规则）<BR/>'
            '上行：经验·数据·规则 → 下行：推荐·服务·报表', size=11),
          fillcolor=BG_BLUE, color=BLUE, penwidth=2.2, pos=(0.0, 1.8))

    # 六色小框（环绕平台：顶/右上/右下/右下底/左下底/左上）
    actors = {
        'yi':   ('医者<BR/>辨证经验<BR/>获得推荐支持', BG_BLUE, BLUE, (0.0, 3.72)),
        'huan': ('患者<BR/>疗效依从<BR/>获得健康服务', BG_GREEN, GREEN, (2.72, 2.5)),
        'yao':  ('药者<BR/>审方与不良反应<BR/>获得用药知识', BG_ORANGE, ORANGE, (3.11, 0.31)),
        'xie':  ('械者<BR/>检验影像数据<BR/>获得分析工具', BG_CYAN, CYAN, (1.56, -1.6)),
        'gui':  ('规者<BR/>质控指标<BR/>获得监督报表', BG_PURPLE, PURPLE, (-1.56, -1.6)),
        'fa':   ('法者<BR/>合规规则<BR/>获得留痕证据', BG_RED, RED, (-2.72, 2.5)),
    }
    for k, (lbl, fc, ec, pos) in actors.items():
        rnode(g, k, H(lbl, size=10), fillcolor=fc, color=ec, penwidth=1.6, pos=pos)

    # 人机闭环：六方 ↔ 平台 双向箭头（灰色细线）
    for k in actors:
        redge(g, k, 'platform', color=LGRAY, penwidth=1.3, dirn='both')

    # 底部 CI/CD 进化闭环（金色闭环链：对话→日志→图谱→调优→自动上线→服务→对话）
    cicd_y = -3.89
    steps = ['对话', '日志', '图谱', '调优', '自动上线', '服务']
    xs = [-3.58, -2.15, -0.72, 0.72, 2.15, 3.58]
    for st, x in zip(steps, xs):
        rnode(g, 'cd_' + st, H(st, size=11, bold=True),
              fillcolor='white', color=GOLD, penwidth=1.6, pos=(x, cicd_y))
    for i in range(len(steps) - 1):
        redge(g, 'cd_' + steps[i], 'cd_' + steps[i + 1], color=GOLD, penwidth=1.8)
    # 闭合：服务 → 再回到对话
    redge(g, 'cd_服务', 'cd_对话', color=GOLD, penwidth=1.8)
    # 链上方标题
    rnode(g, 'cicd_note', H('CI/CD 进化闭环（服务 → 数据 → 共识 → 服务）', size=11, bold=True),
          shape='plaintext', style='', fillcolor='white', color=GOLD, penwidth=0,
          pos=(0.0, -2.85))
    return g


# ============================================================
# 验证：PNG 生成、尺寸>=600px、彩色占比<5%（HSV S>0.12 判定，与 verify_color.py 同口径）
# ============================================================
def verify(fname):
    path = os.path.join(OUT, fname)
    im = Image.open(path).convert('RGB')
    w, h = im.size
    arr = np.asarray(im).astype(np.float64) / 255.0
    mx = arr.max(axis=2)
    mn = arr.min(axis=2)
    denom = np.where(mx > 0, mx, 1.0)
    sat = (mx - mn) / denom
    ratio = float((sat > 0.12).mean() * 100.0)
    ok = (w >= 600 and h >= 600 and ratio < 5.0)
    print('[%s] %s  %dx%d px  彩色占比 %.2f%%  %s' %
          ('OK' if ok else 'FAIL', path, w, h, ratio,
           '通过' if ok else '未达标'))
    return ok


def main():
    figs = [('fig10-1', fig10_1), ('fig10-3', fig10_3),
            ('fig10-5', fig10_5), ('fig10-6', fig10_6)]
    for tag, fn in figs:
        g = fn()
        out = os.path.join(OUT, tag)
        g.render(out, format='png', cleanup=True)
        print('%s done -> %s.png' % (tag, out))
    print('--- 验证 ---')
    results = [verify('fig10-1.png'), verify('fig10-3.png'),
               verify('fig10-5.png'), verify('fig10-6.png')]
    print('ALL PASS' if all(results) else 'SOME FAIL')


if __name__ == '__main__':
    main()
