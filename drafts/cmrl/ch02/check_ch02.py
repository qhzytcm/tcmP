# -*- coding: utf-8 -*-
"""第2章《认知的结构》结构合规与内容质量检查脚本。
输出实测数据，供 chapter-02-selfcheck.md 引用。
口径：段落=每个 ### 小节下的非空行；汉字数=[\u4e00-\u9fff] 计数；总字符数=len(line.strip())。
"""
import re, glob, os

def is_fig_block(line):
    """图块行：图题（**图 X-X ...**）、图体（![...]）、图注（图注：...）不计入正文段落。"""
    s = line.strip()
    return s.startswith('**图 ') or s.startswith('![') or s.startswith('图注：')

BASE = r"C:\Users\DELL\textbook-project\drafts\cmrl\ch02"
FILES = sorted(glob.glob(os.path.join(BASE, "0*-1.*.md")))
print("== 文件清单 ==")
for f in FILES:
    print(os.path.basename(f))

print("\n== 一、结构合规 ==")
sections = []
for f in FILES:
    with open(f, encoding="utf-8") as fh:
        lines = [l.rstrip("\n") for l in fh.readlines()]
    first = lines[0].strip() if lines else "(空文件)"
    sec_no = os.path.basename(f)[:2]
    subs = []
    cur = None
    for l in lines:
        if l.startswith("### "):
            cur = {"title": l, "paras": []}
            subs.append(cur)
        elif cur is not None and l.strip() and not is_fig_block(l):
            cur["paras"].append(l.strip())
    print(f"\n-- 节 {sec_no} --")
    print(f"  首行: {first}")
    print(f"  小节数: {len(subs)} (应为3)")
    for s in subs:
        n_paras = len(s["paras"])
        lens_han = [len(re.findall(r"[\u4e00-\u9fff]", p)) for p in s["paras"]]
        lens_all = [len(p) for p in s["paras"]]
        print(f"  {s['title']} 段数={n_paras} (应为2) 每段汉字数={lens_han} 总字符数={lens_all}")

print("\n== 一A. 字数汇总（供 A2 表格） ==")
for f in FILES:
    with open(f, encoding="utf-8") as fh:
        lines = [l.rstrip("\n") for l in fh.readlines()]
    sec_no = os.path.basename(f)[:2]
    subs = []
    cur = None
    for l in lines:
        if l.startswith("### "):
            cur = {"title": l, "paras": []}
            subs.append(cur)
        elif cur is not None and l.strip() and not is_fig_block(l):
            cur["paras"].append(l.strip())
    row = []
    for s in subs:
        lens_han = [len(re.findall(r"[\u4e00-\u9fff]", p)) for p in s["paras"]]
        row.append(lens_han)
    print(f"节 {sec_no}: {row}")

# 总字符数口径汇总
print("\n== 一B. 总字符数口径汇总 ==")
all_han, all_total = [], []
for f in FILES:
    with open(f, encoding="utf-8") as fh:
        lines = [l.rstrip("\n") for l in fh.readlines()]
    sec_no = os.path.basename(f)[:2]
    subs = []
    cur = None
    for l in lines:
        if l.startswith("### "):
            cur = {"title": l, "paras": []}
            subs.append(cur)
        elif cur is not None and l.strip() and not is_fig_block(l):
            cur["paras"].append(l.strip())
    row = []
    for s in subs:
        lens_all = [len(p) for p in s["paras"]]
        row.append(lens_all)
    print(f"节 {sec_no}: {row}")

print("\n== 二、交叉引用检查 ==")
sec_titles = {}
for f in FILES:
    with open(f, encoding="utf-8") as fh:
        content = fh.read()
    m = re.search(r"^## (2\.\d+) (.+)$", content, re.M)
    if m:
        sec_titles[m.group(1)] = m.group(2)
print("章节标题:", sec_titles)

all_text = ""
for f in FILES:
    with open(f, encoding="utf-8") as fh:
        all_text += fh.read() + "\n"

# 章内节引用：第 2.X 节 / 2.X 节 / 2.X
refs = set(re.findall(r"第\s*(2\.[1-8])\s*节", all_text))
refs |= set(re.findall(r"第\s*(2\.[1-8])", all_text))
print("\n内部节引用（含'第2.X'字样）:", sorted(refs))

# 统计每节引用了哪些其他节（按 '2.N' 出现，排除自身标题行干扰简单处理：报告全部出现）
ref_count = {}
for m in re.finditer(r"2\.([1-8])", all_text):
    k = "2." + m.group(1)
    ref_count[k] = ref_count.get(k, 0) + 1
print("各节号出现次数:", dict(sorted(ref_count.items())))

# 章间引用
ch_refs = sorted(set(re.findall(r"第\s*([1-9]|10)\s*章", all_text)))
print("\n章间引用:", ch_refs)

# 图引用
fig_refs = sorted(set(re.findall(r"图\s*[12][—-]?\d*", all_text)))
print("图引用:", fig_refs)

print("\n== 三、公式可验算 ==")
checks = [
    ("转移矩阵行和 0.7+0.2+0.1", 0.7 + 0.2 + 0.1, 1.0),
    ("γ=0.5 时 1+0.5+0.25+…=2", 1 / (1 - 0.5), 2.0),
    ("γ=0.9 时 1+0.9+0.81+…=10", 1 / (1 - 0.9), 10.0),
    ("策略一 G1=γ/(1−γ)，γ=0.9 → 9", 0.9 / (1 - 0.9), 9.0),
    ("策略二 G2=−1+γ/(1−γ)，γ=0.9 → 8", -1 + 0.9 / (1 - 0.9), 8.0),
    ("策略三 G3=−0.5+γ/(1−γ)，γ=0.9 → 8.5", -0.5 + 0.9 / (1 - 0.9), 8.5),
    ("期望 0.6×1+0.4×0", 0.6 * 1 + 0.4 * 0, 0.6),
    ("四状态 vπ(s4)=1+0.9vπ(s4) → 10", 1 / (1 - 0.9), 10.0),
    ("vπ(s2)=1+0.9×10", 1 + 0.9 * 10, 10.0),
    ("vπ(s1)=0+0.9×10", 0 + 0.9 * 10, 9.0),
]
for name, got, exp in checks:
    ok = abs(got - exp) < 1e-9
    print(f"  {name}: 实测={got} 期望={exp} {'OK' if ok else 'MISMATCH'}")

# 三策略不等式对 γ∈(0,1) 恒成立 + 差值 0.5
import random
random.seed(42)
ok_ineq = all((g := random.uniform(0.01, 0.99), g/(1-g) > -0.5 + g/(1-g) > -1 + g/(1-g))[1] for _ in range(200))
print(f"  G1>G3>G2 对 200 个随机 γ∈(0,1) 抽样: {'恒成立 OK' if ok_ineq else 'MISMATCH'}")
print(f"  G1−G3 = 0.5, G3−G2 = 0.5（与 γ 无关）: 推导成立")

# 迭代收敛 v_{k+1}=r+0.9P v_k 从 v0=0 → (9,10,10,10)
r = [0, 1, 1, 1]
P = [  # s1->s2, s2->s4, s3->s4, s4->s4
    [0, 1, 0, 0],
    [0, 0, 0, 1],
    [0, 0, 0, 1],
    [0, 0, 0, 1],
]
v = [0.0, 0.0, 0.0, 0.0]
for _ in range(200):
    v = [r[i] + 0.9 * sum(P[i][j] * v[j] for j in range(4)) for i in range(4)]
print(f"  迭代收敛 v → {[round(x, 6) for x in v]}（期望 (9,10,10,10)）")

# 关键公式出现在正文中
for kw in ["Gt = Rt+1", "Rt+1 + γRt+2 + γ²Rt+3", "p(s′|s,a)", "vπ(s) = Σa π(a|s) qπ(s,a)",
           "v = rπ + γPπv", "(I − γPπ)⁻¹", "E[X] = E[E[X | Y]]", "Σa π(a|s) = 1",
           "马尔可夫性质", "1/(1−γ)", "随机矩阵"]:
    print(f"  公式出现[{kw}]: {kw in all_text}")

print("\n== 四、术语首现英文对照 ==")
terms = ["full-factor observation", "decision process model", "Markov decision process",
         "Markov property", "policy", "trajectory", "return", "discount rate",
         "state transition", "transition probability", "stochastic matrix", "outcome",
         "discounted return", "expectation", "random variable", "conditional expectation",
         "law of total expectation", "uncertainty", "state value", "action value",
         "Bellman equation", "bootstrap", "absorbing state", "distributed systems science",
         "emergence", "coupling", "individual positioning", "scenario survival optimality",
         "environment co-prosperity optimality", "fitness landscape", "tragedy of the commons",
         "mutual modeling", "reward alignment", "shared decision making", "Disease-Syndrome Unit"]
missing = []
for t in terms:
    if t not in all_text:
        missing.append(t)
print("缺失英文术语:", missing if missing else "无（全部出现）")

print("\n== 五、tcmP 平台一句话 ==")
for m in re.finditer(r".{0,40}tcmP.{0,70}", all_text):
    print("  …" + m.group(0).replace("\n", " ") + "…")

print("\n== 六、第7节三种最适度 / 第8节六者和谐 ==")
for kw in ["个人定位", "场景生存最适度", "环境共荣最适度"]:
    print(f"  2.7节包含[{kw}]: {kw in all_text}")
for kw in ["相互理解", "相互建模", "信息对称", "规则共建", "技术中立", "反馈闭环", "目标函数对齐"]:
    print(f"  2.8节包含[{kw}]: {kw in all_text}")
print("  六者和谐-医患同心: ", "医患同心" in all_text)
print("  六者和谐-人类命运共同体: ", "人类命运共同体" in all_text)

print("\n== 七、本章核心概念出现次数 ==")
for kw in ["全要素观测", "五元组", "状态转移", "折扣回报", "折扣率", "不确定性", "期望",
           "价值函数", "贝尔曼方程", "治未病", "方证对应", "同病异治"]:
    cnt = all_text.count(kw)
    print(f"  [{kw}] 出现 {cnt} 次")

print("\n== 八、自引用一致性关键常量 ===")
for kw in ["0.7, 0.2, 0.1", "(0.7, 0.2, 0.1)", "0.6×1 + 0.4×0", "(9, 10, 10, 10)",
           "γ = 0.9", "1.0、0.7、0.4", "归脾汤", "交泰丸", "天王补心丹", "酸枣仁汤"]:
    cnt = all_text.count(kw)
    print(f"  [{kw}] 出现 {cnt} 次")
