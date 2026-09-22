# -*- coding: utf-8 -*-
"""check_ch09.py — 第9章自检脚本：段落字数统计、标题结构验证、关键公式验算、交叉引用抽取
用法：python check_ch09.py  （在 drafts/cmrl/ch09/ 目录下运行）
输出：A2（字数）、B2（公式验算）、C（引用）所需实测数据
"""
import re, glob, os, math, json

BASE = os.path.dirname(os.path.abspath(__file__))
FILES = sorted(glob.glob(os.path.join(BASE, "[0-9][0-9]-*.md")))
FILES = [f for f in FILES if os.path.basename(f)[:2].isdigit()]
FILES = sorted(FILES, key=lambda f: int(os.path.basename(f)[:2]))

def hanzi_count(s):
    return len(re.findall(r'[\u4e00-\u9fff]', s))

def total_chars(s):
    return len(re.sub(r'\s', '', s))

print("=" * 80)
print("A. 结构检查：节数 / 小节数 / 每小节段落数")
print("=" * 80)
ok = True
sec_stats = {}
for f in FILES:
    name = os.path.basename(f)
    with open(f, encoding='utf-8') as fh:
        lines = fh.read().splitlines()
    # 节标题
    sec_titles = [l for l in lines if re.match(r'^## 9\.\d+ ', l)]
    sub_titles = [l for l in lines if re.match(r'^### 9\.\d+\.\d+ ', l)]
    # 段落 = 非空、非标题行（图块行不计入正文段落）
    paras = [l for l in lines if l.strip() and not l.strip().startswith('#')
             and not l.strip().startswith(('**图', '![', '图注：'))]
    n_sub = len(sub_titles)
    # 每小节段落数：按小节标题切分（图块行【图题/图体/图注】不计入正文段落）
    para_blocks = []
    cur = []
    for l in lines:
        if re.match(r'^### 9\.\d+\.\d+ ', l):
            if cur: para_blocks.append(cur)
            cur = []
        elif l.strip() and not l.strip().startswith('##') \
                and not l.strip().startswith(('**图', '![', '图注：')):
            cur.append(l)
    if cur: para_blocks.append(cur)
    lens = [len(b) for b in para_blocks]
    ok &= (len(sec_titles) == 1) and (n_sub == 3) and (all(x == 2 for x in lens))
    print(f"{name}: 节标题={len(sec_titles)}, 小节={n_sub}, 每小节段落数={lens}  {'OK' if (len(sec_titles)==1 and n_sub==3 and all(x==2 for x in lens)) else 'FAIL'}")
print("结构检查:", "全部通过" if ok else "存在问题")

print()
print("=" * 80)
print("A2. 每段字数统计（汉字数 / 总字符数）")
print("=" * 80)
sec_map = {}
for f in FILES:
    name = os.path.basename(f)
    sec_no = name.split('-')[0]
    with open(f, encoding='utf-8') as fh:
        lines = fh.read().splitlines()
    blocks = []
    cur = []
    subname = None
    for l in lines:
        m = re.match(r'^### (9\.\d+\.\d+) ', l)
        if m:
            if cur: blocks.append((subname, cur))
            subname = m.group(1)
            cur = []
        elif l.strip() and not l.strip().startswith('##') \
                and not l.strip().startswith(('**图', '![', '图注：')):
            cur.append(l)
    if cur: blocks.append((subname, cur))
    for sub, paras in blocks:
        for i, p in enumerate(paras, 1):
            h = hanzi_count(p)
            t = total_chars(p)
            key = f"{sub}"
            sec_map.setdefault(sec_no, {})[f"{sub} 第{i}段"] = (h, t)
            print(f"{sub} 第{i}段: 汉字={h:4d}, 总字符={t:4d}")

print()
print("=" * 80)
print("B2. 关键公式验算")
print("=" * 80)
e = math.e
def softmax_pair(x, y, tau=1.0):
    ex = math.exp(x/tau); ey = math.exp(y/tau)
    return ex/(ex+ey), ey/(ex+ey)

checks = []
# 9.1.2 softmax θ1=2.0 θ2=1.0
p1, p2 = softmax_pair(2.0, 1.0)
checks.append(("9.1.2 softmax(2.0,1.0) → π(a1)=0.731/π(a2)=0.269", f"π(a1)={p1:.4f}, π(a2)={p2:.4f}", abs(p1-0.731)<0.002 and abs(p2-0.269)<0.002))
# 9.2.2 数值验证：两状态两动作；验证正文 v2 的 ∇θ1≈0.495、∇θ2≈−0.495、dπ≈0.726/0.274
# 平稳方程：s1下 a1→s1, a2→s2；s2下任意→s1；奖励 r(s1,a1)=2, r(s1,a2)=0, r(s2,·)=0
# 策略：softmax π(a|s,θ)=e^θ_a/(e^θ1+e^θ2)，θ=(1.0,0.5) 两状态共用（正文 v2 口径）
# d(s2)=d(s1)π(a2); d(s1)+d(s2)=1 → d(s1)=1/(1+π(a2))
# θ=(1.0,0.5): π(a1)=e^1/(e^1+e^0.5)=2.718/4.367≈0.6225, π(a2)≈0.3775
# d(s1)=1/(1+0.3775)≈0.726, d(s2)≈0.274
th1, th2 = 1.0, 0.5
pa1 = math.exp(th1)/(math.exp(th1)+math.exp(th2))
pa2 = 1 - pa1
ds1 = 1/(1+pa2)
ds2 = pa2*ds1
# 正文 v2 口径（softmax 参数化，θ=(1.0,0.5) 为两状态共用的动作偏好参数）：
# r̄ = d(s1)[π(a1)*2 + π(a2)*0] + d(s2)*0 = d(s1)*π(a1)*2 ≈ 0.904
rbar = ds1*pa1*2
# 相对动作价值 qπ 口径：q(s1,a1)=2-r̄+v1, q(s1,a2)=-r̄+v2（v2=v1-r̄），v1 平移量在期望中相消
# s2 下 q(s2,a1)=q(s2,a2)（动作与奖励/转移无关）→ Σ_a π(a|s2)∇lnπ(a|s2)=0 → s2 对梯度无贡献
# ∇θ1 = d(s1)*π(a1)*π(a2)*[(2-r̄+v1)-(v1-2r̄)] = d(s1)*π(a1)*π(a2)*(2+r̄) ≈ 0.495
# ∇θ2 = -∇θ1（对称性）≈ -0.495
g1v = ds1*pa1*pa2*(2+rbar)
g2v = -g1v
checks.append(("9.2.2 两状态数值例：dπ(s1)≈0.726/dπ(s2)≈0.274（正文 v2）",
               f"本脚本解平稳方程得 d(s1)≈{ds1:.3f}, d(s2)≈{ds2:.3f}，与正文 v2 一致",
               abs(ds1-0.726)<0.005 and abs(ds2-0.274)<0.005))
checks.append(("9.2.2 梯度：∇θ1≈0.495（提a1偏好）、∇θ2≈−0.495（压a2偏好）（正文 v2）",
               f"脚本按定理（相对动作价值口径）解析计算 ∇θ1≈{g1v:.3f}, ∇θ2≈{g2v:.3f}，与正文 v2 一致",
               abs(g1v-0.495)<0.005 and abs(g2v+0.495)<0.005))
# 9.3.2 REINFORCE 演算
pa1_525 = math.exp(0.2)/(math.exp(0.2)+math.exp(0.1))
pa2_525 = 1 - pa1_525
# softmax 对数梯度 g = φ(a1) − E[φ] = (1,0) − (π(a1),π(a2)) = (π(a2), −π(a2)) = (0.475, −0.475)
g_upd = (pa2_525, -pa2_525)
th_new = (0.2 + 0.1*3.0*pa2_525, 0.1 + 0.1*3.0*(-pa2_525))  # = (0.3425, −0.0425)，与正文一致
pa1_new = math.exp(th_new[0])/(math.exp(th_new[0])+math.exp(th_new[1]))
checks.append(("9.3.2 REINFORCE 演算：π(a1)≈0.525 → 更新后 ≈0.596",
               f"π(a1)={pa1_525:.4f} → θ=({th_new[0]:.4f},{th_new[1]:.4f}) → π(a1)={pa1_new:.4f}",
               abs(pa1_525-0.525)<0.002 and abs(pa1_new-0.596)<0.004))
# 9.4.1 方差 5000 → 2500
E_G2 = 0.5*100**2 + 0.5*0
E_GM2 = 0.5*(100-50)**2 + 0.5*(0-50)**2
checks.append(("9.4.1 方差缩减：无基线 E[G²]≈5000；基线 b=50 后 E[(G−50)²]=2500",
               f"E[G²]={E_G2}, E[(G−50)²]={E_GM2}", E_G2==5000 and E_GM2==2500))
# 9.5.2 温度 τ=1 与 τ=0.5
t1a, t1b = softmax_pair(2.0, 1.0, 1.0)
t2a, t2b = softmax_pair(2.0, 1.0, 0.5)
checks.append(("9.5.2 温度：τ=1 → 0.73/0.27；τ=0.5 → 0.88/0.12",
               f"τ=1: {t1a:.2f}/{t1b:.2f}；τ=0.5: {t2a:.2f}/{t2b:.2f}",
               abs(t1a-0.73)<0.01 and abs(t2a-0.88)<0.01))
# 9.6.2 高斯残差
res = (1.8-1.5)/0.25
checks.append(("9.6.2 高斯残差 (1.8−1.5)/0.25 = 1.2", f"残差={res}", abs(res-1.2)<1e-9))
# 9.1.2 对数梯度 softmax：φ−E[φ] 符号验证
# 9.2.2 数值验证在正文 v2 中 ∇θ1≈0.495, ∇θ2≈−0.495

allok = True
for name, detail, passed in checks:
    allok &= passed
    print(f"{'✓' if passed else '✗'} {name} | {detail}")

print()
print("=" * 80)
print("C. 交叉引用抽取（章内节引用 9.x → 9.y；跨章引用 第N章）")
print("=" * 80)
sec_refs = {}
chap_refs = set()
for f in FILES:
    name = os.path.basename(f)
    sec_no = re.match(r'(\d+)', name).group(1)
    with open(f, encoding='utf-8') as fh:
        text = fh.read()
    # 章内节引用：9.N（可能带 .x）
    refs = set()
    for m in re.finditer(r'9\.(\d+)(?:\.\d+)?节', text):
        refs.add(int(m.group(1)))
    for m in re.finditer(r'9\.(\d+)(?!\.\d)', text):
        refs.add(int(m.group(1)))
    # 排除自身节号与编号非引用（如“9.6 节将给出”）
    self_no = int(sec_no)
    refs.discard(self_no)
    sec_refs[int(sec_no)] = sorted(refs)
    for m in re.finditer(r'第\s*(\d+)\s*章', text):
        chap_refs.add(int(m.group(1)))
    # 图引用
    figs = sorted(set(int(m.group(1)) for m in re.finditer(r'图\s*9[-\－](\d+)', text)))
    if figs:
        print(f"  第9.{sec_no}节 引用图: {figs}")
print("章内节引用:")
for k in sorted(sec_refs):
    print(f"  9.{k} → {sec_refs[k]}")
print("跨章引用 第N章:", sorted(chap_refs))

# 图引用整体统计
print()
all_text = ""
for f in FILES:
    with open(f, encoding='utf-8') as fh:
        all_text += fh.read()
figs_all = sorted(set(int(m.group(1)) for m in re.finditer(r'图\s*9[-\－](\d+)', all_text)))
print("正文显式引用图号:", figs_all)
print()
print("自检脚本完成。")
