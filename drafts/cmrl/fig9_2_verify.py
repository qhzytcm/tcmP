# -*- coding: utf-8 -*-
"""① ch09 9.2.2 梯度口径核查  ② fig9-2 12 步 θ 轨迹模拟复核（起点(1.0,0.5)→(1.57,-0.07)?）"""
import re
from pathlib import Path

# ① 口径核查（全库）
print('===== 9.2.2 梯度数值口径（0.495 相关全库分布）=====')
hits = []
for f in sorted(Path(r'C:\Users\DELL\textbook-project\drafts\cmrl').rglob('*.md')):
    if 'archive' in str(f) or '_bak' in str(f):
        continue
    txt = f.read_text(encoding='utf-8', errors='ignore')
    for m in re.finditer(r'0\.49[0-9]|0\.48[0-9]|−0\.49[0-9]', txt):
        s = max(0, m.start() - 20)
        hits.append((str(f.relative_to(r'C:\Users\DELL\textbook-project\drafts\cmrl')), txt[s:m.end() + 30].replace('\n', ' ')[:70]))
for h in hits[:10]:
    print('  ', h)

# ② 模拟复核：两状态两动作（例 9.2.2）
# s1: a1→s1 (r=2), a2→s2 (r=0); s2: 任何→s1 (r=0)
# softmax 线性偏好 h(a)=θ_a; π(a1|s1)=exp(θ1)/(exp(θ1)+exp(θ2))
print('\n===== fig9-2 12 步模拟（softmax 梯度上升, α=0.1）=====')
import math

def policy(theta):
    e1, e2 = math.exp(theta[0]), math.exp(theta[1])
    return e1 / (e1 + e2), e2 / (e1 + e2)

def grad_J(theta):
    """∇θJ 解析：两状态两动作(见正文)；q(s1,a1)=2·(1/(1-γd)) 用平均回报近似——用 qπ 真值解方程组"""
    # 正文: s1 下 a1→s1, a2→s2; s2 任意→s1; r(s1,a1)=2 其余 0
    # 平均回报 r̄ = d1·π1·2；q 相对值近似 q(s1,a1)=2−r̄, q(s1,a2)=0−r̄
    # 直接采用正文方向结论 ∇θ1>0 ∝ q(a1)−q(a2)≈2, ∇θ2<0（图注给出 (0.495,−0.495) 为初始方向）
    # 复现图注：每步 θ←θ+0.1·ĝ，ĝ 取正文数值 (0.495,−0.495)（12 步内按梯度方向微变）
    return None

# 图注口径：起点 (1.0,0.5)；初始调优方向 (0.495,−0.495)；每次调整幅度 0.1；12 步到 (1.57,−0.07)
# 验证: 若每步 θ += 0.1·(0.495,−0.495)/0.7（单位化×幅度）?
theta = [1.0, 0.5]
step_unit = (0.495, -0.495)
norm = math.hypot(*step_unit)  # ≈0.7
print(f'初始方向模: {norm:.4f}')
# 口径 A: 每步移动 0.1 沿单位方向（图注"每次调整幅度 0.1"最自然解读）
trajA = []
t = [1.0, 0.5]
for k in range(1, 13):
    t[0] += 0.1 * step_unit[0] / norm
    t[1] += 0.1 * step_unit[1] / norm
    trajA.append((round(t[0], 3), round(t[1], 3)))
print('口径A(每步0.1沿单位梯度):', trajA[-1], '→ 应≈(1.57,−0.07) 若', trajA[-1][0] > 1.5 and trajA[-1][1] < -0.05)
# 口径 B: 每步 θ += 0.1·梯度(不单位化, 梯度随策略更新重算——softmax 线性精确梯度)
def exact_grad(theta):
    """∇θJ = Σs dπ(s)·Σa ∇θπ·qπ；用相对价值近似: q(s1,a1)−q(s1,a2)≈2（奖励差）"""
    p1, p2 = policy(theta)          # s1 下 a1/a2 概率
    # 平稳分布 d(s1)=1（s2 必回 s1）
    # ∇θ ln π(a1)= (1−p1, −p2)? 对 softmax: ∇θ1 ln π1=(1−p1), ∇θ2 ln π1=−p2; ∇θ1 ln π2=−p1, ∇θ2 ln π2=(1−p2)
    # ∇θJ ≈ d1·Σa π·∇θlnπ·q; q 用 (2−r̄, 0−r̄); r̄=d1·p1·2
    rbar = 1.0 * p1 * 2
    q1, q2 = 2 - rbar, 0 - rbar
    g1 = p1 * (1 - p1) * q1 + p2 * (-p1) * q2
    g2 = p1 * (-p2) * q1 + p2 * (1 - p2) * q2
    return g1, g2

tB = [1.0, 0.5]
for k in range(1, 13):
    g1, g2 = exact_grad(tB)
    tB[0] += 0.1 * g1
    tB[1] += 0.1 * g2
print(f'口径B(softmax精确梯度, α=0.1): 12步后 θ=({tB[0]:.3f},{tB[1]:.3f})')
print(f'  初始梯度: ({exact_grad([1.0,0.5])[0]:.4f},{exact_grad([1.0,0.5])[1]:.4f})（图注称 0.495/−0.495）')
# 口径 C: 若"幅度 0.1"指 θ 欧氏距离每步 0.1 且沿**初始**方向（不做梯度重算）
tC = [1.0, 0.5]
for k in range(1, 13):
    tC[0] += 0.1 * step_unit[0] / norm
    tC[1] += 0.1 * step_unit[1] / norm
print(f'口径C(每步0.1沿初始单位方向12步): ({tC[0]:.3f},{tC[1]:.3f})')
