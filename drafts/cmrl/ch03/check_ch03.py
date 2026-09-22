# -*- coding: utf-8 -*-
"""第3章《认知的深化：统计估计与随机逼近》结构合规与内容质量检查脚本。

输出实测数据，供 chapter-03-selfcheck.md 引用。
口径：段落=每个 ### 小节下的非空行；汉字数=[\u4e00-\u9fff] 计数；总字符数=len(line.strip())。
2026-08-15 初版（L3 三审 P0 修订后固化）：新增例号连续性检查与 P0 修订项（麻黄汤 93% 口径、例3.6 步长反例）专项验算。
"""
import re, glob, os, math

BASE = r"C:\Users\DELL\textbook-project\drafts\cmrl\ch03"
FILES = sorted(glob.glob(os.path.join(BASE, "0*-1.*.md")))
print("== 文件清单 ==")
for f in FILES:
    print(os.path.basename(f))


def load_lines(f):
    with open(f, encoding="utf-8") as fh:
        return [l.rstrip("\r\n") for l in fh.readlines()]


def load_text(f):
    with open(f, encoding="utf-8") as fh:
        return fh.read()


def paras_of(lines):
    """返回 [ {title, paras:[...]}, ... ] 列表（每个 ### 小节）。
    图块行（**图 题行、![ 图片行、图注： 行）不计入正文段落，
    保证插入插图后"每小节 2 段"口径不受影响（2026-08-17 图表插入后维护）。"""
    subs, cur = [], None
    for l in lines:
        if l.startswith("### "):
            cur = {"title": l, "paras": []}
            subs.append(cur)
        elif cur is not None and l.strip():
            s = l.strip()
            if s.startswith("**图") or s.startswith("![") or s.startswith("图注："):
                continue
            cur["paras"].append(s)
    return subs


print("\n== 一、结构合规 ==")
sections = []
for f in FILES:
    lines = load_lines(f)
    first = lines[0].strip() if lines else "(空文件)"
    sec_no = os.path.basename(f)[:2]
    subs = paras_of(lines)
    print(f"\n-- 节 {sec_no} --")
    print(f"  首行: {first}")
    print(f"  小节数: {len(subs)} (应为3)")
    for s in subs:
        n_paras = len(s["paras"])
        lens_han = [len(re.findall(r"[\u4e00-\u9fff]", p)) for p in s["paras"]]
        lens_all = [len(p) for p in s["paras"]]
        print(f"  {s['title']} 段数={n_paras} (应为2) 每段汉字数={lens_han} 总字符数={lens_all}")

print("\n== 一A. 字数汇总（汉字数口径，供 A2 表格） ==")
for f in FILES:
    sec_no = os.path.basename(f)[:2]
    subs = paras_of(load_lines(f))
    row = []
    for s in subs:
        row.append([len(re.findall(r"[\u4e00-\u9fff]", p)) for p in s["paras"]])
    print(f"节 {sec_no}: {row}")

print("\n== 一B. 总字符数口径汇总 ==")
all_total = []
for f in FILES:
    sec_no = os.path.basename(f)[:2]
    subs = paras_of(load_lines(f))
    row = []
    for s in subs:
        row.append([len(p) for p in s["paras"]])
        all_total.extend([len(p) for p in s["paras"]])
    print(f"节 {sec_no}: {row}")
print(f"总字符数全段范围: min={min(all_total)} max={max(all_total)} (A2 标准 400-600)")

print("\n== 二、例号连续性检查（P0-2：缺例3.6 已修订） ==")
all_text = "".join(load_text(f) + "\n" for f in FILES)
ex_loc = {}
for f in FILES:
    for m in re.finditer(r"例3\.(\d)", load_text(f)):
        ex_loc.setdefault(int(m.group(1)), set()).add(os.path.basename(f))
for n in range(1, 8):
    loc = ex_loc.get(n, set())
    print(f"  例3.{n}: {'存在' if loc else '缺失!!'} 出现于 {sorted(loc) if loc else '-'}")
missing = [n for n in range(1, 8) if n not in ex_loc]
print("  例号连续 3.1~3.7:", "OK" if not missing else f"MISSING {missing}")

print("\n== 三、P0-1 麻黄汤有效率口径验算（3.1.2） ==")
cured, improved, ineffective, total = 24, 4, 2, 30
rate_count = (cured + improved) / total          # 痊愈+好转 计数口径
rate_w = (cured * 1.0 + improved * 0.7 + ineffective * 0.3) / total  # 3.6.2 转归映射加权
print(f"  计数口径 28/30 = {rate_count:.4f} ≈ 93%（九成三）")
print(f"  加权口径(痊愈1.0/好转0.7/无效0.3) = {rate_w:.4f} ≈ 91%（供 3.6.2 一致校验）")
print("  正文含'约九成三':", "约九成三" in all_text)
print("  正文含'28/30 ≈ 93%':", "28/30 ≈ 93%" in all_text)
print("  正文不再含'百分之八十七':", "百分之八十七" not in all_text)
print("  正文不再含'87%':", "87%" not in all_text)
print("  3.6.2 转归映射(痊愈 = 1.0、好转 = 0.7、无效 = 0.3)存在:", "痊愈 = 1.0、好转 = 0.7、无效 = 0.3" in all_text)

print("\n== 四、公式可验算（B2 全表 + 新增例3.6） ==")
checks = [
    ("麻黄汤有效率 28/30", rate_count, 28 / 30),
    ("例3.1 抛硬币 x̄=0.2", (1 - 1 + 1 + 1 - 1) / 5, 0.2),
    ("例3.2 骰子 18/5=3.6", 18 / 5, 3.6),
    ("例3.2 骰子 13/5=2.6", 13 / 5, 2.6),
    ("σ=√(35/12)≈1.71", math.sqrt(35 / 12), 1.7078),
    ("n=30 半宽 1.96×1.71/√30", 1.96 * math.sqrt(35 / 12) / math.sqrt(30), 0.6116),
    ("n=100 半宽", 1.96 * math.sqrt(35 / 12) / 10, 0.3347),
    ("n=400 半宽", 1.96 * math.sqrt(35 / 12) / 20, 0.1674),
    ("例3.3 q̂=(−1+1−1)/3", (-1 + 1 - 1) / 3, -1 / 3),
    ("例3.3 真值 0.5×(−1)+0.5×1", 0.5 * (-1) + 0.5 * 1, 0.0),
    ("γ=0.9 三时点 0.81/0.9/1", [0.9**2, 0.9, 1.0], [0.81, 0.9, 1.0]),
    ("例3.4 q←0.5+(1/3)(1−0.5)", 0.5 + (1 / 3) * (1 - 0.5), 2 / 3),
    ("例3.5 w₂=3−0.5", 3 - 0.5, 2.5),
    ("例3.7 x̄=(20+5.6+0.6)/30", (20 * 1.0 + 8 * 0.7 + 2 * 0.3) / 30, 0.8733),
    ("例3.7 SE=0.24/√30", 0.24 / math.sqrt(30), 0.0438),
    ("例3.7 半宽 1.96×SE", 1.96 * 0.24 / math.sqrt(30), 0.0859),
    ("例3.7 样本量 n≈(0.24/0.05)²", (0.24 / 0.05) ** 2, 23.04),
    ("差异 SE=0.08/1.96", 0.08 / 1.96, 0.0408),
    ("差异差SE=√2×0.0408", math.sqrt(2) * 0.08 / 1.96, 0.0577),
    ("差异 0.10/0.0577", 0.10 / (math.sqrt(2) * 0.08 / 1.96), 1.732),
    ("差异翻四倍 0.10/(0.0289)", 0.10 / (math.sqrt(2) * (0.08 / 2) / 1.96), 3.464),
]
for name, got, exp in checks:
    if isinstance(exp, list):
        ok = all(abs(a - b) < 1e-3 for a, b in zip(got, exp))
    else:
        ok = abs(got - exp) < 1e-3
    print(f"  {name}: 实测={got if not isinstance(got, list) else [round(x,3) for x in got]} 期望={exp if not isinstance(exp, list) else [round(x,3) for x in exp]} {'OK' if ok else 'MISMATCH'}")

print("\n== 四A. 例3.6 步长反例专项验算（P0-2 新增） ==")
# 部分和（前 10^6 项数值采样）验证发散/收敛方向
def partial_sum(seq_fn, n):
    return sum(seq_fn(k) for k in range(1, n + 1))
print("  1/k: Σa_k 前1e6项 = %.3f（发散趋势，满足①）" % partial_sum(lambda k: 1 / k, 10**6))
print("  1/k: Σa_k² 前1e6项 = %.4f（→π²/6≈%.4f，满足②）" % (partial_sum(lambda k: 1 / k**2, 10**6), math.pi**2 / 6))
print("  1/√k: Σa_k 前1e6项 = %.1f（发散趋势，满足①）" % partial_sum(lambda k: 1 / math.sqrt(k), 10**6))
print("  1/√k: Σa_k² = Σ1/k 前1e6项 = %.3f（发散，不满足②）" % partial_sum(lambda k: 1 / k, 10**6))
print("  1/k²: Σa_k 前1e6项 = %.4f（→π²/6 收敛，不满足①）" % partial_sum(lambda k: 1 / k**2, 10**6))
print("  1/k²: Σa_k² = Σ1/k⁴ 前1e6项 = %.4f（→π⁴/90≈%.4f，满足②）" % (partial_sum(lambda k: 1 / k**4, 10**6), math.pi**4 / 90))
print("  正文含'例3.6（步长反例）':", "例3.6（步长反例）" in all_text)
print("  正文含'π⁴/90':", "π⁴/90" in all_text)
print("  正文含'π²/6':", "π²/6" in all_text)
fig_text = load_text(os.path.join(BASE, "chapter-03-figures.md"))
print("  配图3-8 含'对应例3.6':", "对应例3.6" in fig_text)

print("\n== 五、交叉引用检查 ==")
sec_titles = {}
for f in FILES:
    m = re.search(r"^## (3\.\d+) (.+)$", load_text(f), re.M)
    if m:
        sec_titles[m.group(1)] = m.group(2)
print("章节标题:", sec_titles)

refs = set(re.findall(r"第\s*(3\.[1-8])\s*节", all_text))
print("\n内部节引用（含'第3.X节'字样）:", sorted(refs))
ref_count = {}
for m in re.finditer(r"3\.([1-8])", all_text):
    k = "3." + m.group(1)
    ref_count[k] = ref_count.get(k, 0) + 1
print("各节号出现次数:", dict(sorted(ref_count.items())))
ch_refs = sorted(set(re.findall(r"第\s*([1-9]|10)\s*章", all_text)))
print("章间引用:", ch_refs)
fig_refs = sorted(set(re.findall(r"图\s*[123][—-]?\d*", all_text)))
print("正文图引用:", fig_refs)

print("\n== 六、术语首现英文对照（B1 抽查） ==")
terms = ["model-free learning", "experience", "episode", "episodic task", "return",
         "discount rate", "value", "Monte Carlo method", "mean estimation",
         "law of large numbers", "central limit theorem", "confidence interval",
         "i.i.d.", "statistical estimation", "policy iteration", "exploration",
         "exploitation", "exploring starts", "soft policy", "ε-greedy",
         "first-visit", "every-visit", "on-policy", "off-policy",
         "importance sampling", "incremental mean estimation", "step size",
         "stochastic approximation", "Robbins-Monro", "stochastic gradient descent",
         "evidence level", "degree of certainty", "systems science",
         "distributed systems science", "emergence", "individual positioning",
         "scenario survival optimality", "environment co-prosperity optimality",
         "shared decision making"]
missing = [t for t in terms if t not in all_text]
print("缺失英文术语:", missing if missing else "无（全部出现）")

print("\n== 七、关键常量一致性（自引用） ==")
for kw in ["A = 1.0、B = 0.7、C = 0.4", "痊愈 = 1.0、好转 = 0.7、无效 = 0.3",
           "0.873", "0.044", "0.086", "0.79 至 0.96", "28/30 ≈ 93%",
           "例3.7", "例3.6", "1/√k", "1/k²"]:
    cnt = all_text.count(kw)
    print(f"  [{kw}] 出现 {cnt} 次")

print("\n== 八、tcmP 平台一句话 ==")
for m in re.finditer(r".{0,40}tcmP.{0,70}", all_text):
    print("  …" + m.group(0).replace("\n", " ") + "…")

print("\n== 九、关键公式出现 ==")
for kw in ["v_π(s) = E[G_t | S_t = s]", "G_t = R_{t+1} + γR_{t+2} + γ²R_{t+3}",
           "w_{k+1} = w_k + (1/k)(x_k − w_k)", "w_{k+1} = w_k − a_k·g̃(w_k, η_k)",
           "Σ_{k=1}^∞ a_k = ∞", "Σ_{k=1}^∞ a_k² < ∞", "x̄ = (20×1.0 + 8×0.7 + 2×0.3)/30",
           "μ ± 1.96σ/√n"]:
    print(f"  [{kw}] 出现: {kw in all_text}")

print("\n== 十、核心概念出现次数 ==")
for kw in ["无模型学习", "回合", "回报", "价值", "大数定律", "中心极限定理",
           "置信区间", "蒙特卡洛", "探索", "利用", "增量均值", "随机逼近",
           "Robbins-Monro", "证据等级", "把握程度", "证据升级"]:
    print(f"  [{kw}] 出现 {all_text.count(kw)} 次")

print("\n== 完成 ==")
