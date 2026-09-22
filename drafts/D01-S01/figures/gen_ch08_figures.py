# -*- coding: utf-8 -*-
"""第8章 经络学说（下）配图生成脚本（黑白线稿 + 定位标注）
输出：figures/ch08/fig8-1.png ~ fig8-3.png
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
import os

plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

OUTDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ch08')
os.makedirs(OUTDIR, exist_ok=True)

BLACK = 'black'
GRAY = '0.35'


def new_ax(figsize=(4.6, 8.2)):
    fig, ax = plt.subplots(figsize=figsize)
    ax.set_xlim(-3.2, 3.2)
    ax.set_ylim(-0.8, 11.4)
    ax.set_aspect('equal')
    ax.axis('off')
    return fig, ax


def draw_body(ax, lw=1.6):
    """简笔人体轮廓（正面朝向读者），中心线 x=0。"""
    ax.add_patch(Circle((0, 10.0), 1.05, fill=False, lw=lw, ec=BLACK))  # 头
    ax.plot([-0.35, -0.35], [8.95, 8.45], color=BLACK, lw=lw)  # 颈
    ax.plot([0.35, 0.35], [8.95, 8.45], color=BLACK, lw=lw)
    ax.plot([-1.35, 1.35], [8.4, 8.4], color=BLACK, lw=lw)  # 肩线
    ax.plot([-1.35, -1.15, -1.15, 1.15, 1.15, 1.35], [8.4, 8.4, 3.7, 3.7, 8.4, 8.4], color=BLACK, lw=lw)  # 躯干
    ax.plot([-1.15, -1.35], [3.7, 3.7], color=BLACK, lw=lw)
    ax.plot([1.15, 1.35], [3.7, 3.7], color=BLACK, lw=lw)
    ax.plot([-1.35, -2.0], [8.2, 6.0], color=BLACK, lw=lw)  # 上臂
    ax.plot([1.35, 2.0], [8.2, 6.0], color=BLACK, lw=lw)
    ax.plot([-2.0, -1.75], [6.0, 4.2], color=BLACK, lw=lw)  # 前臂
    ax.plot([2.0, 1.75], [6.0, 4.2], color=BLACK, lw=lw)
    ax.plot([-1.75, -1.75], [4.2, 3.7], color=BLACK, lw=lw)  # 手
    ax.plot([1.75, 1.75], [4.2, 3.7], color=BLACK, lw=lw)
    ax.plot([-0.55, -0.7], [3.7, 1.7], color=BLACK, lw=lw)  # 大腿
    ax.plot([0.55, 0.7], [3.7, 1.7], color=BLACK, lw=lw)
    ax.plot([-0.7, -0.6], [1.7, 0.35], color=BLACK, lw=lw)  # 小腿
    ax.plot([0.7, 0.6], [1.7, 0.35], color=BLACK, lw=lw)
    ax.plot([-0.6, -1.0], [0.35, 0.3], color=BLACK, lw=lw)  # 足
    ax.plot([0.6, 1.0], [0.35, 0.3], color=BLACK, lw=lw)


def mark(ax, x, y, text, dx=0.18, dy=0.0, ha='left', fs=9, color=BLACK, ms=4):
    ax.plot([x], [y], marker='o', ms=ms, mfc='white', mec=color, mew=1.2)
    if text:
        ax.text(x + dx, y + dy, text, fontsize=fs, ha=ha, va='center', color=color)


def arrow_line(ax, pts, lw=2.4, color=BLACK, arrow=True):
    ax.plot([p[0] for p in pts], [p[1] for p in pts], color=color, lw=lw, solid_capstyle='round')
    if arrow:
        p0, p1 = pts[-2], pts[-1]
        ax.annotate('', xy=p1, xytext=p0,
                    arrowprops=dict(arrowstyle='-|>', color=color, lw=lw, mutation_scale=16))


# =====================================================================
# 图8-1 督任冲三脉体表循行示意图
# =====================================================================
fig, (axb, axf) = plt.subplots(1, 2, figsize=(9.2, 8.2))
for ax in (axb, axf):
    ax.set_xlim(-3.2, 3.2)
    ax.set_ylim(-0.8, 11.4)
    ax.set_aspect('equal')
    ax.axis('off')

# 背面：督脉
draw_body(axb)
axb.set_title('背面 · 督脉（阳脉之海）', fontsize=12, pad=8)
arrow_line(axb, [(0, 3.7), (0, 8.6), (0, 10.0), (0, 11.05)])
mark(axb, 0, 3.7, '会阴（起）', 0.25, fs=9, ms=4)
axb.text(-0.25, 8.55, '风府', fontsize=9, ha='right')
axb.text(-0.25, 10.2, '巅顶', fontsize=9, ha='right')
axb.text(0.4, 7.3, '后正中线\n（大椎）', fontsize=8, ha='left', va='center', color=GRAY)
axb.text(-2.9, 10.9, '①', fontsize=11, fontweight='bold')

# 正面：任脉 + 冲脉
draw_body(axf)
axf.set_title('正面 · 任脉（阴脉之海）+ 冲脉（血海）', fontsize=12, pad=8)
arrow_line(axf, [(0, 3.7), (0, 7.4), (0, 8.45), (0, 9.3)])
mark(axf, 0, 3.7, '会阴（起）', 0.25, fs=9, ms=4)
axf.text(0.25, 7.4, '胸中', fontsize=9, ha='left')
axf.text(-0.25, 9.3, '口唇', fontsize=9, ha='right')
arrow_line(axf, [(-0.6, 3.7), (-0.6, 7.4)], color=GRAY)
arrow_line(axf, [(0.6, 3.7), (0.6, 7.4)], color=GRAY)
axf.text(-1.4, 5.5, '冲脉\n（夹脐上行）', fontsize=8, ha='center', color=GRAY)
axf.text(0.22, 5.9, '脐', fontsize=8, ha='left', color=GRAY)
axf.text(-2.9, 10.9, '②', fontsize=11, fontweight='bold')

fig.tight_layout()
fig.savefig(os.path.join(OUTDIR, 'fig8-1.png'), dpi=200, bbox_inches='tight', facecolor='white')
plt.close(fig)
print('saved fig8-1.png')


# =====================================================================
# 图8-2 骨度分寸法定位图（正面 + 背面）
# =====================================================================
fig, (axf, axb) = plt.subplots(1, 2, figsize=(9.4, 8.2))
for ax in (axf, axb):
    ax.set_xlim(-3.4, 3.4)
    ax.set_ylim(-0.8, 11.4)
    ax.set_aspect('equal')
    ax.axis('off')


def dim(ax, x, y1, y2, label, color=BLACK, dx=0.0):
    ax.annotate('', xy=(x, y2), xytext=(x, y1),
                arrowprops=dict(arrowstyle='<->', color=color, lw=1.4))
    ax.text(x + dx + 0.16, (y1 + y2) / 2, label, fontsize=9, ha='left', va='center', color=color)


# 正面
draw_body(axf)
axf.set_title('正面 · 骨度分寸', fontsize=12, pad=8)
dim(axf, 1.75, 7.6, 8.4, '天突→歧骨 9寸')
dim(axf, 1.75, 5.9, 7.6, '歧骨→脐 8寸')
dim(axf, 1.75, 3.7, 5.9, '脐→耻骨上 5寸')
axf.plot([1.75], [7.6], marker='o', ms=3, mfc='white', mec=BLACK, mew=1.0)
axf.plot([1.75], [5.9], marker='o', ms=3, mfc='white', mec=BLACK, mew=1.0)
dim(axf, 2.7, 4.2, 6.0, '肘→腕 12寸')
dim(axf, 2.7, 6.0, 8.2, '腋前→肘 9寸')
dim(axf, -2.7, 0.35, 1.7, '胫骨内髁→\n内踝 13寸', dx=-0.6)
dim(axf, -2.7, 1.7, 3.7, '耻骨上→股骨\n内上髁 18寸', dx=-0.6)
axf.text(-2.95, 10.9, '①', fontsize=11, fontweight='bold')

# 背面
draw_body(axb)
axb.set_title('背面 · 骨度分寸', fontsize=12, pad=8)
dim(axb, -1.75, 3.7, 8.4, '大椎→尾骶 21椎', dx=-0.6)
axb.annotate('', xy=(1.05, 10.0), xytext=(-1.05, 10.0),
             arrowprops=dict(arrowstyle='<->', color=BLACK, lw=1.4))
axb.text(0, 10.35, '前发际→后发际 12寸', fontsize=9, ha='center', va='bottom')
axb.text(-2.95, 10.9, '②', fontsize=11, fontweight='bold')

fig.tight_layout()
fig.savefig(os.path.join(OUTDIR, 'fig8-2.png'), dpi=200, bbox_inches='tight', facecolor='white')
plt.close(fig)
print('saved fig8-2.png')


# =====================================================================
# 图8-3 常用经穴定位图（15穴，正面 + 背面）
# =====================================================================
fig = plt.figure(figsize=(9.6, 8.6))
axf = fig.add_axes([0.02, 0.04, 0.46, 0.92])
axb = fig.add_axes([0.50, 0.04, 0.46, 0.92])
for ax in (axf, axb):
    ax.set_xlim(-3.4, 3.4)
    ax.set_ylim(-0.8, 11.4)
    ax.set_aspect('equal')
    ax.axis('off')

# 正面（身体右侧 = 读者左侧；对称标注即可）
draw_body(axf)
axf.set_title('正面 · 常用经穴（11穴）', fontsize=12, pad=8)
mark(axf, 0.3, 9.6, '迎香', 0.16)                 # 鼻翼外
mark(axf, 1.15, 5.9, '天枢（脐旁2寸）', 0.16)      # 脐旁
mark(axf, 2.0, 6.0, '曲池', 0.16)                 # 肘外端
mark(axf, 1.88, 5.85, '尺泽', -1.6, ha='right')    # 肘横纹
mark(axf, 1.75, 4.2, '太渊', 0.16)                # 腕横纹
mark(axf, 1.75, 4.55, '列缺', -1.3, ha='right')    # 腕上1.5寸
mark(axf, -1.75, 4.2, '神门', 0.16)               # 左腕尺侧
mark(axf, 0.7, 1.35, '足三里', 0.16)              # 犊鼻下3寸
mark(axf, 0.62, 0.6, '丰隆', 0.16)                # 外踝上8寸
mark(axf, -0.62, 1.0, '三阴交', -0.16, ha='right')  # 内踝上3寸
mark(axf, 1.75, 3.55, '', 0.0, fs=1, ms=4)          # 合谷（手背）点位
axf.annotate('合谷（手背）', xy=(1.75, 3.55), xytext=(2.75, 3.1),
             fontsize=8, ha='left',
             arrowprops=dict(arrowstyle='-|>', color=GRAY, lw=1.0))
mark(axf, 0.9, 0.28, '太冲', 0.16, fs=8)           # 足背
axf.text(2.9, 10.9, '①', fontsize=11, fontweight='bold')

# 背面
draw_body(axb)
axb.set_title('背面 · 委中 / 至阴 / 涌泉', fontsize=12, pad=8)
mark(axb, -0.7, 1.7, '委中（腘横纹中点）', 0.16, ha='left')
axb.plot([-1.0], [0.28], marker='o', ms=4, mfc='white', mec=BLACK, mew=1.2)
axb.annotate('至阴（足小趾外侧）', xy=(-1.0, 0.28), xytext=(-2.9, 1.1),
             fontsize=8, ha='left',
             arrowprops=dict(arrowstyle='-|>', color=GRAY, lw=1.0))
axb.plot([0.0], [0.28], marker='o', ms=4, mfc='white', mec=BLACK, mew=1.2)
axb.annotate('涌泉（足底前1/3）', xy=(0.0, 0.28), xytext=(-0.4, -0.5),
             fontsize=8, ha='center',
             arrowprops=dict(arrowstyle='-|>', color=GRAY, lw=1.0))
axb.text(2.9, 10.9, '②', fontsize=11, fontweight='bold')

fig.savefig(os.path.join(OUTDIR, 'fig8-3.png'), dpi=200, bbox_inches='tight', facecolor='white')
plt.close(fig)
print('saved fig8-3.png')

print('ALL DONE')
