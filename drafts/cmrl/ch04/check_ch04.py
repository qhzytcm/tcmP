# -*- coding: utf-8 -*-
"""
《中医场景强化学习》第4章 自检脚本 check_ch04.py
检查对象：drafts/cmrl/ch04/01-1.1.md ~ 08-1.8.md（8 个节文件）
产出：A 结构统计（节/小节/段落/字数）、B 公式验算、C 交叉引用提取、D 术语英文抽查
用法：python check_ch04.py
"""
import re
import os

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)))
FILES = [f'{i:02d}-1.{i}.md' for i in range(1, 9)]


def read_lines(f):
    with open(os.path.join(BASE, f), encoding='utf-8') as fh:
        return fh.read().splitlines()


def section_a():
    print('===== A. 结构统计（汉字数 / 总字符数） =====')
    summary = {}
    for f in FILES:
        lines = read_lines(f)
        sec = [l for l in lines if l.startswith('## ')]
        subs = [l for l in lines if l.startswith('### ')]
        paras = [l.strip() for l in lines if l.strip() and not l.strip().startswith('#')]
        stats = []
        for p in paras:
            han = len(re.findall(r'[\u4e00-\u9fff]', p))
            total = len(re.sub(r'\s', '', p))
            stats.append((han, total))
        summary[f] = stats
        print(f, '|', sec[0] if sec else 'NONE', '| 小节:', len(subs), '| 段落:', len(paras))
        for i, (han, total) in enumerate(stats, 1):
            print(f'  段{i}: 汉字={han} 总字符={total}')
    all_paras = [s for f in FILES for s in summary[f]]
    han_vals = [s[0] for s in all_paras]
    tot_vals = [s[1] for s in all_paras]
    print(f'段落总数: {len(all_paras)}')
    print(f'汉字口径: min={min(han_vals)} max={max(han_vals)} 达400={sum(1 for v in han_vals if v >= 400)}/{len(han_vals)}')
    print(f'总字符口径: min={min(tot_vals)} max={max(tot_vals)} 达400={sum(1 for v in tot_vals if v >= 400)}/{len(tot_vals)}')
    return summary


def mat_vec_mul(P, v):
    """矩阵乘向量（纯 Python，小规模）"""
    return [sum(P[i][j] * v[j] for j in range(len(v))) for i in range(len(P))]


def back_substitute_lower_tri(A, b):
    """回代求解下三角方程组 A v = b（纯 Python）"""
    n = len(b)
    v = [0.0] * n
    for i in range(n - 1, -1, -1):
        s = sum(A[i][j] * v[j] for j in range(i + 1, n))
        v[i] = (b[i] - s) / A[i][i]
    return v


def section_b():
    print()
    print('===== B. 公式验算（纯 Python，无第三方依赖） =====')
    checks = []
    near = lambda a, b, tol=1e-9: abs(a - b) < tol
    # 1/(1-0.9) = 10（正文 4.1.2 / 4.2.2 / 例4.4）
    checks.append(('1/(1-0.9)=10', near(1 / (1 - 0.9), 10)))
    # 例4.2 正确版：v(s3)=10, v(s2)=1+0.9*10=10, v(s1)=0+0.9*10=9
    checks.append(('例4.2 正确 v(s2)=10', near(1 + 0.9 * 10, 10)))
    checks.append(('例4.2 正确 v(s1)=9', near(0.9 * 10, 9)))
    # 错误版（漏记 s2->s3 奖励）：v(s2)=9, v(s1)=8.1 —— 正文 4.1.2 例4.1 采用，4.2.2 明示为"插曲"
    checks.append(('漏记奖励版 v(s2)=9, v(s1)=8.1（4.1.2 例4.1 数值）',
                   near(0.9 * 10, 9) and near(0.9 * 9, 8.1)))
    # 例4.3：8.8 / 3.6 / 6.2
    checks.append(('例4.3 q(归脾汤)=8.8', near(0.7 + 0.9 * 9, 8.8)))
    checks.append(('例4.3 q(银翘散)=3.6', near(0.9 * 4, 3.6)))
    checks.append(('例4.3 v(s)=6.2', near(0.5 * 8.8 + 0.5 * 3.6, 6.2)))
    # 例4.4 矩阵求解（纯 Python 回代，I-gamma*P 为下三角块）
    P = [[0, 1, 0, 0], [0, 0, 0, 1], [0, 0, 0, 1], [0, 0, 0, 1]]
    r = [0, 1, 1, 1]
    g = 0.9
    I_gP = [[(1.0 if i == j else 0.0) - g * P[i][j] for j in range(4)] for i in range(4)]
    v = back_substitute_lower_tri(I_gP, r)
    checks.append(('例4.4 矩阵解 v=[9,10,10,10]',
                   all(near(a, b) for a, b in zip(v, [9, 10, 10, 10]))))
    # 例4.5 迭代序列
    vk = [0.0, 0.0, 0.0, 0.0]
    seq = []
    for _ in range(4):
        vk = [r[i] + g * x for i, x in enumerate(mat_vec_mul(P, vk))]
        seq.append(vk)
    expected = [[0, 1, 1, 1], [0.9, 1.9, 1.9, 1.9], [1.71, 2.71, 2.71, 2.71], [2.439, 3.439, 3.439, 3.439]]
    for i, (s, e) in enumerate(zip(seq, expected), 1):
        checks.append((f'例4.5 v{i} 与正文一致', all(near(a, b) for a, b in zip(s, e))))
    checks.append(('0.9^20 ≈ 0.12', abs(0.9 ** 20 - 0.12) < 0.005))
    # 例4.8 六方共识合成：0.895 ≈ 0.89
    rs = [0.8, 1.0, 0.9, 1.0, 0.7, 0.9]
    ws = [0.25, 0.25, 0.15, 0.15, 0.1, 0.1]
    checks.append(('例4.8 合成奖励 0.895≈0.89', near(sum(w * rr for w, rr in zip(ws, rs)), 0.895)))
    checks.append(('例4.8 权重和=1', near(sum(ws), 1)))
    # 4.4.3 大 n 运算量 (10^6)^3 = 10^18
    checks.append(('(10^6)^3 = 10^18', (10 ** 6) ** 3 == 10 ** 18))
    # 九宫格 3 步内确定性路径 5+25+125=155（正文"几千条"存疑项）
    checks.append(('九宫格 3 步内确定性路径 5+25+125=155', 5 + 25 + 125 == 155))
    for name, ok in checks:
        print(('✓' if ok else '✗'), name)
    return checks


def section_c():
    print()
    print('===== C. 交叉引用提取 =====')
    for f in FILES:
        with open(os.path.join(BASE, f), encoding='utf-8') as fh:
            txt = fh.read()
        nxt_ch = re.findall(r'下一章[^。；]*', txt)
        ref_ch = re.findall(r'第[一二三四五六七八九十0-9]+章', txt)
        refs_ex = sorted(set(re.findall(r'例4\.[1-8]', txt)))
        print(f, '| 下一章:', nxt_ch, '| 章号:', ref_ch, '| 例引用:', refs_ex)


def section_d():
    print()
    print('===== D. 术语英文抽查 =====')
    terms = ['state value', 'discounted return', 'value estimation equation', 'Bellman equation',
             'bootstrap', 'action value', 'Q-function', 'stochastic matrix', 'contraction mapping',
             'value network', 'individual positioning', 'scenario survival optimality', 'environment co-prosperity optimality',
             'Markov', 'spectral']
    full = ''
    for f in FILES:
        with open(os.path.join(BASE, f), encoding='utf-8') as fh:
            full += fh.read()
    for t in terms:
        print(f'{t}: {"出现" if t.lower() in full.lower() else "缺失"}')


if __name__ == '__main__':
    section_a()
    section_b()
    section_c()
    section_d()
