# -*- coding: utf-8 -*-
"""最终视觉质量检查：
1. 边-节点冲突检测：边 path 采样点落在非端点节点 bbox 内视为冲突。
2. ASCII 缩略图：缩小 PNG 输出灰度字符画，目检布局。
"""
import os, re, sys, html, subprocess, tempfile
import numpy as np
from PIL import Image
os.environ['PATH'] = r'C:\Tools\graphviz\Graphviz-16.0.0-win64\bin' + os.pathsep + os.environ.get('PATH', '')
sys.path.insert(0, r'C:\Users\DELL\textbook-project\drafts\cmrl\ch10')
import gen_ch10_graphviz as m


def render_svg(g):
    engine = getattr(g, 'engine', 'dot') or 'dot'
    with tempfile.NamedTemporaryFile('w', suffix='.dot', delete=False, encoding='utf-8') as f:
        f.write(g.source)
        fname = f.name
    try:
        r = subprocess.run([r'C:\Tools\graphviz\Graphviz-16.0.0-win64\bin\dot.exe',
                            '-K' + engine, '-Tsvg', fname],
                           capture_output=True, encoding='utf-8', errors='replace')
        return r.stdout
    finally:
        os.unlink(fname)


def node_blocks(svg):
    out = {}
    for blk in re.findall(r'<g id="node\d+" class="node">.*?</g>', svg, re.S):
        tm = re.search(r'<title>(.*?)</title>', blk, re.S)
        if not tm:
            continue
        nid = html.unescape(tm.group(1))
        xs, ys = [], []
        for p in re.findall(r'<polygon[^>]*points="([^"]+)"', blk):
            for pt in p.split():
                a, b = pt.split(',')
                xs.append(float(a)); ys.append(float(b))
        for d in re.findall(r'<path[^>]*d="([^"]+)"', blk):
            for val in re.findall(r'[-0-9.]+,[-0-9.]+', d):
                a, b = val.split(',')
                xs.append(float(a)); ys.append(float(b))
        for e in re.findall(r'<ellipse[^>]*cx="([-0-9.]+)"[^>]*cy="([-0-9.]+)"[^>]*rx="([-0-9.]+)"[^>]*ry="([-0-9.]+)"', blk):
            cx, cy, rx, ry = map(float, e)
            xs += [cx - rx, cx + rx]; ys += [cy - ry, cy + ry]
        if xs:
            out[nid] = (min(xs), min(ys), max(xs), max(ys))
    return out


def edge_paths(svg):
    """返回 [(edge_title, [(x,y)...])]，点来自 path d 的绝对坐标（跳过 M 之后曲线控制点采样）。"""
    out = []
    for blk in re.findall(r'<g id="edge\d+" class="edge">.*?</g>', svg, re.S):
        tm = re.search(r'<title>(.*?)</title>', blk, re.S)
        title = html.unescape(tm.group(1)) if tm else '?'
        for d in re.findall(r'<path[^>]*d="([^"]+)"', blk):
            pts = []
            for cmd, rest in re.findall(r'([MCL])\s*([-0-9.,\s]+)', d):
                for val in re.findall(r'[-0-9.]+,[-0-9.]+', rest):
                    a, b = val.split(',')
                    pts.append((float(a), float(b)))
            if pts:
                out.append((title, pts))
        for p in re.findall(r'<polygon[^>]*points="([^"]+)"', blk):  # 箭头多边形
            for pt in p.split():
                a, b = pt.split(',')
                pts.append((float(a), float(b)))
    return out


def point_in_box(pt, box, pad=2.0):
    x, y = pt
    return (box[0] - pad <= x <= box[2] + pad) and (box[1] - pad <= y <= box[3] + pad)


figs = [('fig10-1', m.fig10_1), ('fig10-3', m.fig10_3),
        ('fig10-5', m.fig10_5), ('fig10-6', m.fig10_6)]

for tag, fn in figs:
    g = fn()
    svg = render_svg(g)
    boxes = node_blocks(svg)
    edges = edge_paths(svg)
    print('==== %s ====' % tag)
    conflicts = 0
    for etitle, pts in edges:
        # 解析边端点：title 形如 "a->b" 或 "a--b"
        mm = re.match(r'(.*?)(?:->|--)(.*)', etitle)
        ends = {mm.group(1).strip(), mm.group(2).strip()} if mm else set()
        for p in pts:
            for nid, box in boxes.items():
                if nid in ends:
                    continue
                if point_in_box(p, box):
                    conflicts += 1
                    print('  !! 边 %s 穿过节点 %s @(%.0f,%.0f)' % (etitle, nid, p[0], p[1]))
                    break
    print('  冲突采样点数: %d' % conflicts)

print()
print('==== ASCII 缩略图 ====')
for tag, fn in figs:
    g = fn()
    path = os.path.join(m.OUT, tag + '.png')
    im = Image.open(path).convert('L')
    w, h = im.size
    tw = 100
    th = max(1, int(h / w * tw * 0.45))   # 字符高宽比约 2:1
    im2 = im.resize((tw, th))
    arr = np.asarray(im2)
    chars = ' .:-=+*#%@'
    print('-- %s (%dx%d) --' % (tag, w, h))
    for row in arr:
        print(''.join(chars[min(9, int((255 - v) / 256 * 10))] for v in row))
