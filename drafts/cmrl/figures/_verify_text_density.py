# -*- coding: utf-8 -*-
"""图内文字密度统计（图表工程师·文字精简批次）

统计口径：
  - 语义标注（sem）= 图内全部文字标签：ax.text/annotate/节点框文本/fig.text/
    图例条目/坐标轴标题（不含刻度数字、不含 (a)(b) 面板编号）
  - 总文字 = 语义标注 + 刻度数字
  - 最小字号：分别统计 全图（含刻度）与 语义 两类

用法：
  python _verify_text_density.py           # 默认：统计全部 4 个费曼脚本 + ch10 graphviz
"""
import os
import sys
import importlib

FIGDIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, FIGDIR)
sys.path.insert(0, os.path.normpath(os.path.join(FIGDIR, '..', 'ch10')))
os.chdir(FIGDIR)

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

captured = []
_orig_close = plt.close


def _close(fig=None, *a, **k):
    if fig is not None:
        captured.append(fig)
    return _orig_close(fig, *a, **k)


plt.close = _close


def count_fig(fig):
    sem, ticks = [], []

    def add(t, kind):
        fs = t.get_fontsize()
        if fs is None:
            fs = -1
        (sem if kind == 'sem' else ticks).append((t.get_text(), fs))

    for t in fig.texts:
        add(t, 'sem')
    for ax in fig.axes:
        for t in ax.texts:
            add(t, 'sem')
        if ax.legend_:
            for t in ax.legend_.get_texts():
                add(t, 'sem')
        if ax.xaxis.label.get_text():
            add(ax.xaxis.label, 'sem')
        if ax.yaxis.label.get_text():
            add(ax.yaxis.label, 'sem')
        for t in ax.get_xticklabels():
            add(t, 'ticks')
        for t in ax.get_yticklabels():
            add(t, 'ticks')
    return sem, ticks


def count_graphviz_digraph(g):
    """按 dot 语句统计：节点 label 数（每条 node 语句 1 个）、边 label 数；
    最小字号从 node/edge 语句与 HTML label 的 POINT-SIZE 解析。"""
    node_labels = 0
    edge_labels = 0
    min_fs = None
    for line in g.body:
        line = line.strip()
        if not line:
            continue
        fs = None
        mfs = None
        import re
        m = re.search(r'fontsize=([0-9.]+)', line)
        if m:
            fs = float(m.group(1))
        for ps in re.findall(r'POINT-SIZE="?([0-9.]+)"?', line):
            ps = float(ps)
            fs = ps if fs is None else min(fs, ps)
        if fs is not None:
            mfs = fs
        if '->' in line:
            if 'label=' in line:
                edge_labels += 1
        else:
            node_labels += 1
        if mfs is not None:
            min_fs = mfs if min_fs is None else min(min_fs, mfs)
    return node_labels + edge_labels, node_labels, edge_labels, min_fs


def report_row(tag, n_sem, n_ticks, min_all, min_sem, note=''):
    print('%-14s 语义=%-3d 刻度=%-3d 总=%-3d | 最小字号(全)=%-5s 最小(语义)=%-5s %s'
          % (tag, n_sem, n_ticks, n_sem + n_ticks,
             str(min_all) if min_all else '-', str(min_sem) if min_sem else '-', note))


def main():
    jobs = [
        ('gen_ch07_figures_feynman',
         [('fig7-1', 'fig7_1'), ('fig7-3雷达', 'fig7_2'),
          ('fig7-2钟形', 'fig7_3'), ('fig7-4', 'fig7_4')]),
        ('gen_ch08_figures_feynman',
         [('fig8-1', 'fig8_1'), ('fig8-2', 'fig8_2'),
          ('fig8-3', 'fig8_3'), ('fig8-4', 'fig8_4')]),
        ('gen_ch09_figures_feynman',
         [('fig9-1', 'fig9_1'), ('fig9-2', 'fig9_2'),
          ('fig9-3', 'fig9_3'), ('fig9-4', 'fig9_4')]),
        ('gen_ch10_figures_feynman',
         [('fig10-1', 'fig10_1'), ('fig10-2', 'fig10_2'),
          ('fig10-3', 'fig10_3'), ('fig10-4', 'fig10_4'),
          ('fig10-5', 'fig10_5'), ('fig10-6', 'fig10_6'),
          ('fig10-7', 'fig10_7')]),
    ]
    for mod, figmap in jobs:
        m = importlib.import_module(mod)
        print('=====', mod)
        for tag, fnname in figmap:
            before = len(captured)
            getattr(m, fnname)()
            fig = captured[before]
            sem, ticks = count_fig(fig)
            allfs = [fs for _, fs in sem + ticks if fs > 0]
            semfs = [fs for _, fs in sem if fs > 0]
            report_row(tag, len(sem), len(ticks),
                       min(allfs) if allfs else None,
                       min(semfs) if semfs else None)

    # ---- ch10 Graphviz 重绘 4 幅 ----
    sys.path.insert(0, os.path.normpath(os.path.join(FIGDIR, '..', 'ch10')))
    g10 = importlib.import_module('gen_ch10_graphviz')
    print('===== ch10/gen_ch10_graphviz.py')
    for tag, fnname in [('fig10-1', 'fig10_1'), ('fig10-3', 'fig10_3'),
                        ('fig10-5', 'fig10_5'), ('fig10-6', 'fig10_6')]:
        g = getattr(g10, fnname)()
        total, nn, ne, mfs = count_graphviz_digraph(g)
        report_row(tag, total, 0, mfs, mfs,
                   note='(节点label=%d 边label=%d)' % (nn, ne))

if __name__ == '__main__':
    main()
