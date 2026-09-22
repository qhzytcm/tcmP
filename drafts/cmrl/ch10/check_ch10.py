# -*- coding: utf-8 -*-
"""第10章《幸福的闭环》结构合规与内容质量检查脚本。
输出实测数据，供 chapter-10-selfcheck.md 引用。
口径：段落=每个 ### 小节下的非空行；汉字数=[\u4e00-\u9fff] 计数；总字符数=len(line.strip())。
"""
import re, glob, os

BASE = r"C:\Users\DELL\textbook-project\drafts\cmrl\ch10"
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
        elif cur is not None and l.strip():
            # 图块行（图题/图片引用/图注，由图表工程师插入）不计入正文段落
            s = l.strip()
            if s.startswith("**图") or s.startswith("![") or s.startswith("图注："):
                continue
            cur["paras"].append(s)
    print(f"\n-- 节 {sec_no} --")
    print(f"  首行: {first}")
    print(f"  小节数: {len(subs)} (应为3)")
    lens_matrix = []
    for s in subs:
        n_paras = len(s["paras"])
        lens_han = [len(re.findall(r"[\u4e00-\u9fff]", p)) for p in s["paras"]]
        lens_all = [len(p) for p in s["paras"]]
        lens_matrix.append(lens_han)
        print(f"  {s['title']} 段数={n_paras} (应为2) 每段汉字数={lens_han} 总字符数={lens_all}")
    sections.append(lens_matrix)

# 汇总表
print("\n-- 字数汇总（汉字数）--")
all_han = []
for i, m in enumerate(sections, 1):
    print(f"  10.{i}: {m}")
    for pair in m:
        all_han.extend(pair)
print(f"  总段数: {len(all_han)}")
print(f"  汉字数>=400 的段: {sum(1 for h in all_han if h >= 400)}/{len(all_han)}")
print(f"  汉字数区间: min={min(all_han)}, max={max(all_han)}")
print(f"  汉字数<400 的段(最短5个): {sorted(all_han)[:5]}")

print("\n== 二、交叉引用检查 ==")
sec_titles = {}
for f in FILES:
    sec_no = os.path.basename(f)[:2]
    with open(f, encoding="utf-8") as fh:
        content = fh.read()
    m = re.search(r"^## (10\.\d+) (.+)$", content, re.M)
    if m:
        sec_titles[m.group(1)] = m.group(2)
print("章节标题:")
for k, v in sec_titles.items():
    print(f"  {k} {v}")

all_text = ""
for f in FILES:
    with open(f, encoding="utf-8") as fh:
        all_text += fh.read() + "\n"

# 章内节引用（第 10.X 节 或 10.X 节）
refs = set(re.findall(r"第\s*(10\.[1-8])\s*节", all_text))
refs |= set(re.findall(r"(?<!第)(?<!第\s)10\.[1-8]\s*节", all_text))
print("\n内部节引用:", sorted(refs))
for r in sorted(refs):
    print(f"  第 {r} 节 -> 存在: {r in sec_titles}")

# 章间引用（第 1-9 章 / 10 章 / 全书）
ch_refs = sorted(set(re.findall(r"第\s*([1-9]|10)\s*章", all_text)))
print("\n章间引用:", ch_refs)

# 图引用
fig_refs = sorted(set(re.findall(r"图\s*10[—-]?\d*", all_text)))
print("\n图引用:", fig_refs)

print("\n== 三、公式可验算 ==")
checks = [
    ("softmax π(a1): e^0.5/(e^0.5+e^0.3)", __import__("math").exp(0.5) / (__import__("math").exp(0.5) + __import__("math").exp(0.3)), 0.5498),
    ("softmax π(a2): e^0.3/(e^0.5+e^0.3)", __import__("math").exp(0.3) / (__import__("math").exp(0.5) + __import__("math").exp(0.3)), 0.4502),
    ("π(a1)+π(a2)=1", __import__("math").exp(0.5) / (__import__("math").exp(0.5) + __import__("math").exp(0.3)) + __import__("math").exp(0.3) / (__import__("math").exp(0.5) + __import__("math").exp(0.3)), 1.0),
    ("ρt(a2)=0.2/0.5", 0.2 / 0.5, 0.4),
    ("ρt(a1)=0.8/0.5", 0.8 / 0.5, 1.6),
    ("未修正 Δθ=0.1×(−0.5498,0.5498)×0.4 第一分量", 0.1 * (-0.5498) * 0.4, -0.0220),
    ("未修正 Δθ 第二分量", 0.1 * 0.5498 * 0.4, 0.0220),
    ("ρt=0.4502/0.5", 0.4502 / 0.5, 0.9004),
    ("修正后 Δθ 第一分量=0.1×0.9004×(−0.5498)×0.4", 0.1 * 0.9004 * (-0.5498) * 0.4, -0.0198),
    ("ρt 若 π(a2)=0.9 → 0.9/0.5", 0.9 / 0.5, 1.8),
    ("自然梯度 0.192/0.24", 0.192 / 0.24, 0.8),
    ("A2C δt=1+0.9×10−10", 1 + 0.9 * 10 - 10, 0.0),
    ("优势 75−60（相对平均60）", 75 - 60, 15),
    ("优势 45−60", 45 - 60, -15),
    ("αw/αθ=0.1/0.01", 0.1 / 0.01, 10.0),
]
for name, got, exp in checks:
    ok = abs(got - exp) < 0.0001
    print(f"  {name}: 实测={got:.4f} 期望={exp} {'OK' if ok else 'MISMATCH'}")

# 关键公式出现在正文中
for kw in ["Aπ(s,a) = qπ(s,a) − vπ(s)", "δt", "ρt", "min(ρt Ât", "clip(ρt, 1−ε, 1+ε)", "KL", "Fisher", "αw/αθ"]:
    print(f"  公式出现[{kw}]: {kw in all_text}")

print("\n== 四、术语首现英文对照 ==")
terms = ["actor-critic architecture", "actor", "critic", "baseline", "Q actor-critic",
         "two-timescale", "Advantage Actor-Critic", "A2C", "advantage function",
         "asynchronous parallel learning", "worker", "A3C", "Asynchronous Advantage Actor-Critic",
         "Mnih 等，2016", "off-policy learning", "on-policy", "importance sampling",
         "importance ratio", "Proximal Policy Optimization", "PPO", "natural gradient",
         "Fisher information matrix", "TRPO", "Trust Region Policy Optimization",
         "Schulman 等，2015", "KL", "clipped surrogate objective", "SAC", "DDPG",
         "shared vision", "distributed system", "V-trace"]
missing = []
for t in terms:
    if t not in all_text:
        missing.append(t)
print("缺失英文术语:", missing if missing else "无（全部出现）")

print("\n== 五、tcmP 平台一句话 ==")
for m in re.finditer(r".{0,30}tcmP.{0,60}", all_text):
    print("  …" + m.group(0).replace("\n", " ") + "…")

print("\n== 六、六者协同 / 三编总结 / 核心概念 ==")
for kw in ["医者", "患者", "药者", "械者", "规者", "法者", "和而不同",
           "奖励共识", "回路透明", "责任分离", "全程留痕",
           "双回路", "诊疗回路", "系统学习回路",
           "提高认知", "确认信仰", "追求幸福",
           "上编", "中编", "下编",
           "幸福医院", "和谐社会", "人类命运共同体",
           "适度而非最优化", "效不更方", "效改其方", "效如桴鼓", "中病即止"]:
    print(f"  [{kw}] 出现 {all_text.count(kw)} 次")

print("\n== 七、核心算法数值一致性抽查 ==")
for kw in ["0.8", "1.6", "0.4", "0.9004", "0.0198", "0.0220", "0.5498", "0.4502",
           "0.24", "0.192", "n = 5", "αw = 0.1", "αθ = 0.01", "1−ε", "1+ε", "0.1 至 0.2"]:
    print(f"  数值[{kw}] 出现 {all_text.count(kw)} 次")
