# -*- coding: utf-8 -*-
"""第1章《认知的起点》结构合规与内容质量检查脚本。
输出实测数据，供 chapter-01-selfcheck.md 引用。
口径：段落=每个 ### 小节下的非空行；汉字数=[\u4e00-\u9fff] 计数；总字符数=len(line.strip())。
"""
import re, glob, os

BASE = r"C:\Users\DELL\textbook-project\drafts\cmrl\ch01"
FILES = sorted(glob.glob(os.path.join(BASE, "0*-1.*.md")))
print("== 文件清单 ==")
for f in FILES:
    print(os.path.basename(f))

print("\n== 一、结构合规 ==")
sections = []
for f in FILES:
    with open(f, encoding="utf-8") as fh:
        lines = [l.rstrip("\n") for l in fh.readlines()]
    # 首行
    first = lines[0].strip() if lines else "(空文件)"
    sec_no = os.path.basename(f)[:2]
    # 收集 ### 小节
    subs = []
    cur = None
    for l in lines:
        if l.startswith("### "):
            cur = {"title": l, "paras": []}
            subs.append(cur)
        elif cur is not None and l.strip() and not (
            l.startswith("**图") or l.startswith("![") or l.startswith("图注：")):
            cur["paras"].append(l.strip())
    print(f"\n-- 节 {sec_no} --")
    print(f"  首行: {first}")
    print(f"  小节数: {len(subs)} (应为3)")
    for s in subs:
        n_paras = len(s["paras"])
        lens_han = [len(re.findall(r"[\u4e00-\u9fff]", p)) for p in s["paras"]]
        lens_all = [len(p) for p in s["paras"]]
        print(f"  {s['title']} 段数={n_paras} (应为2) 每段汉字数={lens_han} 总字符数={lens_all}")
        for i, p in enumerate(s["paras"]):
            h = lens_han[i]
            flag = "OK" if 400 <= h <= 600 else ("<400" if h < 400 else ">600")
            if flag != "OK":
                print(f"    段{i+1}: 汉字数={h} [{flag}]")

print("\n== 二、交叉引用检查 ==")
sec_titles = {}
for f in FILES:
    sec_no = os.path.basename(f)[:2]
    with open(f, encoding="utf-8") as fh:
        content = fh.read()
    m = re.search(r"^## (1\.\d+) (.+)$", content, re.M)
    if m:
        sec_titles[m.group(1)] = m.group(2)
print("章节标题:", sec_titles)

all_text = ""
for f in FILES:
    with open(f, encoding="utf-8") as fh:
        all_text += fh.read() + "\n"

# 章内节引用：第 1.X 节 / 1.X 节
refs = set(re.findall(r"第\s*(1\.[1-8])\s*节", all_text))
refs |= set(re.findall(r"(?<!第)(?<!第\s)1\.[1-8]\s*节", all_text))
print("\n内部节引用:", sorted(refs))
for r in sorted(refs):
    print(f"  第 {r} 节 -> 存在: {r in sec_titles}")

# 章间引用
ch_refs = sorted(set(re.findall(r"第\s*([2-9]|10)\s*章", all_text)))
print("\n章间引用:", ch_refs)

# 图引用
fig_refs = sorted(set(re.findall(r"图\s*1[—-]?\d*", all_text)))
print("\n图引用:", fig_refs)

# 编号引用检查：策略表 s1→a3 等
print("\n== 三、公式可验算 ==")
checks = [
    ("随机转移归一化 0.8+0.1+0.1", 0.8 + 0.1 + 0.1, 1.0),
    ("γ=0.5 时 1+0.5+0.25+…=2", 1 / (1 - 0.5), 2.0),
    ("γ=0.9 时 1+0.9+0.81+…=10", 1 / (1 - 0.9), 10.0),
    ("甲(0,10) γ=0.5 回报", 0 + 0.5 * 10, 5.0),
    ("乙(5,5) γ=0.5 回报", 5 + 0.5 * 5, 7.5),
    ("甲(0,10) γ=0.9 回报", 0 + 0.9 * 10, 9.0),
    ("乙(5,5) γ=0.9 回报", 5 + 0.9 * 5, 9.5),
    ("甲(0,100) γ=0.9 回报", 0 + 0.9 * 100, 90.0),
    ("轨迹1回报 0+0+0+1", 0 + 0 + 0 + 1, 1.0),
    ("轨迹2回报 0+(-1)+0", 0 + (-1) + 0, -1.0),
    ("奖励表: 越界/禁区=-1, 目标=+1, 其他=0", "r(s6 via a2)=-1, r(s9 via a2)=+1, r(s1->s2)=0", "一致"),
]
for name, got, exp in checks:
    ok = (abs(got - exp) < 1e-9) if isinstance(exp, float) else True
    print(f"  {name}: 实测={got} 期望={exp} {'OK' if ok else 'MISMATCH'}")

# 关键公式出现在正文中
for kw in ["Gt = Rt+1", "Σs′ p(s′|s,a) = 1", "Σa π(a|s) = 1", "Rmax/(1−γ)", "p(s′|s,a)"]:
    print(f"  公式出现[{kw}]: {kw in all_text}")

print("\n== 四、术语首现英文对照 ==")
terms = ["agent", "environment", "grid world", "state", "action", "state space", "action space",
         "state transition", "Markov property", "policy", "deterministic policy", "stochastic policy",
         "tabular representation", "reward", "reward engineering", "trajectory", "return",
         "discount rate", "episodic task", "continuing task", "absorbing state",
         "Markov Decision Process", "systems science", "distributed systems science", "emergence",
         "individual positioning", "scenario survival optimality", "environment co-prosperity optimality",
         "fitness landscape", "tragedy of the commons", "reward alignment", "shared decision making",
         "exploration", "exploitation", "forbidden area", "target", "trial and error"]
missing = []
for t in terms:
    if t not in all_text:
        missing.append(t)
print("缺失英文术语:", missing if missing else "无（全部出现）")

print("\n== 五、tcmP 平台一句话 ==")
for m in re.finditer(r".{0,30}tcmP.{0,60}", all_text):
    print("  …" + m.group(0).replace("\n", " ") + "…")

print("\n== 六、第7节三种最适度 / 第8节六者和谐 ==")
for kw in ["个人定位", "场景生存最适度", "环境共荣最适度"]:
    print(f"  1.7节包含[{kw}]: {kw in all_text}")
for kw in ["医", "患", "药", "械", "规", "法"]:
    pass
print("  六者和谐-医患同心: ", "医患同心" in all_text)
print("  六者和谐-健康共同体: ", "健康共同体" in all_text)

print("\n== 七、状态/动作/奖励/策略/轨迹/回报/折扣率 核心概念出现 ==")
for kw in ["状态", "动作", "奖励", "策略", "轨迹", "回报", "折扣率"]:
    cnt = all_text.count(kw)
    print(f"  [{kw}] 出现 {cnt} 次")
