# -*- coding: utf-8 -*-
"""布局质量检查：从 SVG 提取节点 bbox，检测节点重叠，输出结构概览。"""
import os, re, sys, html, subprocess, tempfile
os.environ['PATH'] = r'C:\Tools\graphviz\Graphviz-16.0.0-win64\bin' + os.pathsep + os.environ.get('PATH', '')
sys.path.insert(0, r'C:\Users\DELL\textbook-project\drafts\cmrl\ch10')
import gen_ch10_graphviz as m


def render_svg(g):
    src = g.source
    engine = getattr(g, 'engine', 'dot') or 'dot'
    with tempfile.NamedTemporaryFile('w', suffix='.dot', delete=False, encoding='utf-8') as f:
        f.write(src)
        fname = f.name
    try:
        r = subprocess.run([r'C:\Tools\graphviz\Graphviz-16.0.0-win64\bin\dot.exe',
                            '-K' + engine, '-Tsvg', fname],
                           capture_output=True, encoding='utf-8', errors='replace')
        return r.stdout
    finally:
        os.unlink(fname)


def bbox_of_node(svg, nid):
    """按 <title>nid</title> 定位节点块，返回 (x0,y0,x1,y1)（SVG 原始坐标）。"""
    blocks = re.findall(r'<g id="node\d+" class="node">.*?</g>', svg, re.S)
    for blk in blocks:
        tm = re.search(r'<title>(.*?)</title>', blk, re.S)
        if tm and html.unescape(tm.group(1)) == nid:
            xs, ys = [], []
            for p in re.findall(r'<polygon[^>]*points="([^"]+)"', blk):
                for pt in p.split():
                    a, b = pt.split(',')
                    xs.append(float(a)); ys.append(float(b))
            for d in re.findall(r'<path[^>]*d="([^"]+)"', blk):
                for val in re.findall(r'[-0-9.]+,[-0-9.]+', d):
                    a, b = val.split(',')
                    xs.append(float(a)); ys.append(float(b))
            for e in re.findall(r'<ellipse[^>]*cx="([0-9.]+)"[^>]*cy="([0-9.]+)"[^>]*rx="([0-9.]+)"[^>]*ry="([0-9.]+)"', blk):
                cx, cy, rx, ry = map(float, e)
                xs += [cx - rx, cx + rx]; ys += [cy - ry, cy + ry]
            if not xs:
                for t in re.findall(r'<text[^>]*x="([0-9.]+)"[^>]*y="([0-9.]+)"', blk):
                    xs.append(float(t[0])); ys.append(float(t[1]))
            if not xs:
                return None
            return (min(xs), min(ys), max(xs), max(ys))
    return None


def overlap(a, b):
    return not (a[2] <= b[0] or b[2] <= a[0] or a[3] <= b[1] or b[3] <= a[1])


if __name__ == '__main__':
    figs = [('fig10-1', m.fig10_1, ['actor', 'critic', 'env', 'note']),
            ('fig10-3', m.fig10_3, ['yi', 'huan', 'yao', 'xie', 'gui', 'fa', 'hub']),
            ('fig10-5', m.fig10_5, ['perceive', 'decide', 'act', 'feedback', 'learn', 'loopnote']),
            ('fig10-6', m.fig10_6, ['platform', 'yi', 'huan', 'yao', 'xie', 'gui', 'fa',
                                    'cd_对话', 'cd_日志', 'cd_图谱', 'cd_调优', 'cd_自动上线', 'cd_服务'])]
    for tag, fn, ids in figs:
        g = fn()
        svg = render_svg(g)
        print('==== %s ====' % tag)
        boxes = {}
        for nid in ids:
            bb = bbox_of_node(svg, nid)
            if bb is None:
                print('  %-10s (未找到)' % nid)
                continue
            boxes[nid] = bb
            print('  %-10s x[%6.0f,%6.0f] y[%6.0f,%6.0f]  w=%.0f h=%.0f'
                  % (nid, bb[0], bb[2], bb[1], bb[3], bb[2] - bb[0], bb[3] - bb[1]))
        keys = list(boxes.keys())
        issues = 0
        for i in range(len(keys)):
            for j in range(i + 1, len(keys)):
                if overlap(boxes[keys[i]], boxes[keys[j]]):
                    print('  !! 重叠: %s × %s' % (keys[i], keys[j]))
                    issues += 1
        print('  重叠对数: %d' % issues)
