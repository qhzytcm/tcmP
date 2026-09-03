# -*- coding: utf-8 -*-
"""cmrl 单门学科知识树（真实树形版）——须(根)-干-枝-叶 自下而上
树形结构: 底部根系(须) -> 树干(根/干) -> 主枝(三编) -> 次枝(10章) -> 叶冠(43叶)
输出: figures/book/cmrl-knowledge-tree.png
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Polygon, Ellipse
from pathlib import Path

plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

XU = '须：数学基础\n概率·期望·矩阵·收敛·梯度'
ROOT = '根：状态—动作—奖励'
GANS = [
    ('干1 提高认知', [
        ('枝1-1 认知起点', ['叶 状态S=四诊', '叶 动作A=方剂', '叶 策略π=辨证', '叶 奖励R=疗效', '叶 回报G=疗程']),
        ('枝1-2 决策模型', ['叶 MDP五元组', '叶 转移=传变', '叶 折扣=治未病', '叶 价值函数']),
        ('枝1-3 认知深化', ['叶 大数定律', '叶 统计估计', '叶 随机逼近', '叶 证据等级']),
    ]),
    ('干2 确认信仰', [
        ('枝2-1 价值量化', ['叶 状态价值', '叶 贝尔曼账本', '叶 动作价值', '叶 矩阵求解', '叶 收敛性']),
        ('枝2-2 最优择优', ['叶 最优价值', '叶 最优策略', '叶 价值迭代', '叶 策略迭代']),
        ('枝2-3 时序检验', ['叶 TD走一步', '叶 Sarsa同策', '叶 Q学习最优']),
    ]),
    ('干3 追求幸福', [
        ('枝3-1 幸福表达', ['叶 奖励尺子', '叶 四最适度', '叶 多目标', '叶 正则缰绳']),
        ('枝3-2 幸福实现', ['叶 函数近似', '叶 随机梯度', '叶 DQN技巧', '叶 泛化']),
        ('枝3-3 幸福探索', ['叶 参数策略', '叶 策略梯度', '叶 基线', '叶 探索利用']),
        ('枝3-4 幸福闭环', ['叶 AC分工', '叶 优势函数', '叶 PPO步稳', '叶 六者协同']),
    ]),
]

fig, ax = plt.subplots(figsize=(16, 13))
ax.set_xlim(0, 100)
ax.set_ylim(0, 100)
ax.axis('off')

BROWN = '#8d6e63'
BROWN_D = '#5d4037'
GREEN = '#2e7d32'


def box(x, y, text, w, h, fc, ec, fs=8.5):
    ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h,
                                boxstyle='round,pad=0.25', fc=fc, ec=ec, lw=1.0))
    ax.text(x, y, text, ha='center', va='center', fontsize=fs)


def branch(x1, y1, x2, y2, lw=1.5, c=BROWN):
    ax.plot([x1, x2], [y1, y2], color=c, lw=lw, zorder=1, solid_capstyle='round')


# ============ 底部根系（须）============
for dx, dy in ((-7, -4), (-3.5, -6), (0, -7), (3.5, -6), (7, -4)):
    branch(50, 12, 50 + dx, 12 + dy, lw=1.2, c=BROWN)
# 须标注（根系下方）
box(50, 3.5, XU, 26, 5, '#fef9e7', '#f5b041', fs=8.5)

# ============ 树干（根 + 主干）============
# 根（树干基部）
box(50, 13, ROOT, 24, 5, '#d5f5e3', '#2e7d32', fs=9)
# 主干（从根向上 13 -> 78）
ax.add_patch(Polygon([[47, 13], [53, 13], [52.2, 78], [47.8, 78]],
                     closed=True, fc=BROWN, ec=BROWN_D, lw=1))

# ============ 主枝（三编干）从主干分叉 ============
# 干1 左主枝: (49, 62) -> (22, 72)
# 干2 中主枝: (50, 70) -> (50, 82)
# 干3 右主枝: (51, 62) -> (78, 72)
GAN_POS = {1: (49, 62, 22, 72), 2: (50, 68, 50, 80), 3: (51, 62, 78, 72)}
GAN_BOX = {1: (22, 76), 2: (50, 85), 3: (78, 76)}
gan_colors = {'干1 提高认知': '#d6eaf8', '干2 确认信仰': '#fdebd0', '干3 追求幸福': '#e8daef'}

for i, (gan, branches) in enumerate(GANS, 1):
    x1, y1, x2, y2 = GAN_POS[i]
    branch(x1, y1, x2, y2, lw=4, c=BROWN)
    bx, by = GAN_BOX[i]
    box(bx, by, gan, 14, 4.5, gan_colors[gan], BROWN_D, fs=9)

# ============ 次枝（10 章）与叶冠 ============
leaf_colors = ['#ebf5fb', '#fdf2e9', '#f4ecf7']
for i, (gan, branches) in enumerate(GANS, 1):
    x1, y1, x2, y2 = GAN_POS[i]
    nb = len(branches)
    for j, (branch_name, leaves) in enumerate(branches):
        # 次枝从主枝分叉
        t = 0.35 + 0.3 * j / max(nb - 1, 1)
        px = x1 + (x2 - x1) * t
        py = y1 + (y2 - y1) * t
        spread = 9 if i == 2 else 7
        lx = px + (j - (nb - 1) / 2) * spread
        ly = py + 6
        branch(px, py, lx, ly, lw=2, c=BROWN)
        # 枝标注
        box(lx, ly + 2.2, branch_name, 11, 3.2, '#ffffff', BROWN, fs=6.8)
        # 叶（次枝端向上展开成叶冠）
        nl = len(leaves)
        for k, leaf in enumerate(leaves):
            ex = lx + (k - (nl - 1) / 2) * 7.0
            ey = ly + 7 + (k // 4) * 5.5
            branch(lx, ly + 3.5, ex, ey, lw=0.8, c='#9e9e9e')
            # 叶（椭圆）
            ax.add_patch(Ellipse((ex, ey), 6.6, 3.4, fc=leaf_colors[i - 1],
                                 ec='#aab7b8', lw=0.7))
            ax.text(ex, ey, leaf.replace('叶 ', ''), ha='center', va='center',
                    fontsize=5.6, color='#333333')

plt.tight_layout()
out = Path(r'C:\Users\DELL\textbook-project\drafts\cmrl\figures\book')
out.mkdir(exist_ok=True)
png = out / 'cmrl-knowledge-tree.png'
plt.savefig(png, dpi=200, bbox_inches='tight', facecolor='white')
print(f'生成: {png} ({png.stat().st_size // 1024}KB)')
print('叶数:',
      sum(len(leaves) for _, branches in GANS for _, leaves in branches), '叶')
