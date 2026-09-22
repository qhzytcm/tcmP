# -*- coding: utf-8 -*-
"""第6章 正文复验脚本（check_ch06.py）

用途：为 chapter-06-selfcheck.md 提供可复跑的实测数据。
产出：
  A. 结构检查：8 节 × 3 小节 × 2 段；文件命名；首行标题。
  B. 字数检查：每段汉字数（[\u4e00-\u9fff]）与总字符数（去空白后的可见字符）。
  C. 公式验算：随机游走真实价值、例6.1~例6.6 全部数值（含第三回合争议数值复核）。
  D. 交叉引用抽取：章内"6.N"节引用、"图 6-x"引用、跨章"第N章"引用。

用法：python check_ch06.py   （在工作目录 drafts/cmrl/ch06 下运行）
"""
import glob
import os
import re
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
FILES = sorted(glob.glob(os.path.join(BASE, "0*-1.*.md")))
assert len(FILES) == 8, f"应找到 8 个节文件，实际 {len(FILES)}"

HANZI = re.compile(r"[\u4e00-\u9fff]")

# 图块 = 图题（**图 N-x …**）+ 图体（![…](…)）+ 图注（图注：…），是排版元素，
# 不计入正文段落与字数统计（图表工程师 2026-08-17 引入插图后适配）。
FIG_PREFIXES = ("**图 ", "![", "图注：")


def is_figure_block(line):
    return line.startswith(FIG_PREFIXES)


# ---------- A. 结构检查 ----------
def check_structure():
    print("=== A. 结构检查 ===")
    ok = True
    for f in FILES:
        name = os.path.basename(f)
        with open(f, encoding="utf-8") as fh:
            lines = fh.readlines()
        # 首行标题
        first = lines[0].strip()
        if not re.match(r"^## 6\.[1-8] ", first):
            ok = False
            print(f"  [FAIL] {name} 首行标题异常: {first!r}")
        # 小节与段落
        subs = {}
        cur = None
        for ln in lines:
            ln = ln.strip()
            m = re.match(r"^### (6\.[1-8]\.[123]) ", ln)
            if m:
                cur = m.group(1)
                subs[cur] = 0
            elif (ln and not ln.startswith("#") and not is_figure_block(ln) and cur):
                subs[cur] += 1
        sec = name.split("-")[1].replace(".md", "")  # 如 "1.2"（文件保留原始节号）
        sub = sec.split(".")[1]                        # 章内节号 "2"
        expect = [f"6.{sub}.1", f"6.{sub}.2", f"6.{sub}.3"]
        actual = list(subs.keys())
        paras = list(subs.values())
        if actual != expect or paras != [2, 2, 2]:
            ok = False
            print(f"  [FAIL] {name} 小节/段落: {actual} {paras}")
        else:
            print(f"  [PASS] {name}: 小节 {actual}，段数 {paras}")
    print(f"  结构判定: {'通过' if ok else '不通过'}\n")
    return ok


# ---------- B. 字数检查 ----------
def check_lengths():
    print("=== B. 字数检查（每段：汉字数 / 总字符数）===")
    rows = []
    for f in FILES:
        with open(f, encoding="utf-8") as fh:
            content = fh.read()
        parts = [p.strip() for p in re.split(r"\n\s*\n", content) if p.strip()]
        seg = 0
        for p in parts:
            if p.startswith("#") or is_figure_block(p):
                continue
            seg += 1
            hanzi = len(HANZI.findall(p))
            total = len(re.sub(r"\s", "", p))
            rows.append((os.path.basename(f), seg, hanzi, total))
    for name, seg, h, t in rows:
        flag = "OK" if 400 <= t <= 600 else "!!"
        print(f"  {name} 第{seg}段: 汉字{h} / 总{t} {flag}")
    n = len(rows)
    n_ok = sum(1 for _, _, _, t in rows if 400 <= t <= 600)
    n_hanzi = sum(1 for _, _, h, _ in rows if h >= 400)
    print(f"  总段数 {n}；总字符 400-600 达标 {n_ok}/{n}；纯汉字 ≥400 {n_hanzi}/{n}\n")
    return rows


# ---------- C. 公式验算 ----------
def verify_formulas():
    print("=== C. 公式验算 ===")
    fails = []
    def chk(label, cond):
        print(f"  [{'PASS' if cond else 'FAIL'}] {label}")
        if not cond:
            fails.append(label)

    # C1 随机游走真实价值：p_i = i/6
    rw = [i / 6 for i in range(1, 6)]
    chk("随机游走 A~E = 0.167/0.333/0.5/0.667/0.833",
        all(abs(rw[i] - v) < 1e-9 for i, v in enumerate([1/6, 2/6, 3/6, 4/6, 5/6])))

    # C2 例6.1 四状态链
    gamma, alpha = 0.9, 0.1
    true_v = [gamma**3, gamma**2, gamma, 1.0]  # s1..s4
    chk("例6.1 真实价值 0.729/0.81/0.9/1",
        all(abs(a - b) < 1e-9 for a, b in zip(true_v, [0.729, 0.81, 0.9, 1.0])))
    v = [0.0] * 4
    # 回合1：s2->s3->s4（s2,s3 奖励0；s4 奖励1）
    v[3] = 0 - alpha * (0 - 1)  # 0.1
    chk("例6.1 回合1后 (0,0,0,0.1)", [round(x, 6) for x in v] == [0, 0, 0, 0.1])
    # 回合2：s1->s2->s3->s4
    v[2] = 0 + alpha * (0.9 * v[3] - 0)   # 0.009
    v[3] = 0.1 + alpha * (1 - 0.1)        # 0.19
    chk("例6.1 回合2后 (0,0,0.009,0.19)", [round(x, 6) for x in v] == [0, 0, 0.009, 0.19])
    # 第三回合（按规则重算，复核修订后正文 0.0252）
    v0 = v[:]
    v[1] = 0 + alpha * (0.9 * v0[2] - 0)          # 0.00081
    v[2] = v0[2] + alpha * (0.9 * v0[3] - v0[2])  # 0.0252
    v[3] = v0[3] + alpha * (1 - v0[3])            # 0.271
    chk("例6.1 第三回合后 s2=0.00081、s4=0.271",
        abs(v[1] - 0.00081) < 1e-9 and abs(v[3] - 0.271) < 1e-9)
    print("  [信息] 例6.1 第三回合后 s3 按规则 = %.4f，与修订后正文 0.0252 一致（原 0.0261 系漏减旧值笔误，已按 P0 修订）" % v[2])

    # C3 例6.2 Sarsa
    q = {(1, "右"): 0.0, (2, "右"): 0.0}
    q[(1, "右")] = 0 + alpha * (0 + 1.0 * q[(2, "右")] - 0)  # 0
    q[(2, "右")] = 0 + alpha * (1 - 0)                        # 0.1
    chk("例6.2 回合1后 q(s1,右)=0、q(s2,右)=0.1",
        q[(1, "右")] == 0 and abs(q[(2, "右")] - 0.1) < 1e-9)
    q[(1, "右")] = q[(1, "右")] + alpha * (0 + 1.0 * q[(2, "右")] - q[(1, "右")])
    q[(2, "右")] = q[(2, "右")] + alpha * (1 - q[(2, "右")])
    chk("例6.2 回合2后 q(s1,右)=0.01、q(s2,右)=0.19",
        abs(q[(1, "右")] - 0.01) < 1e-9 and abs(q[(2, "右")] - 0.19) < 1e-9)
    q_left = 0 + alpha * (-1 - 0)
    chk("例6.2 探索左 q(s1,左)=-0.1", abs(q_left + 0.1) < 1e-9)

    # C4 例6.3 n步回报
    r = [2, 3, 4, 5]
    G14 = r[0] + gamma * r[1] + gamma**2 * r[2] + gamma**3 * r[3]
    chk("例6.3 G(1:2) 常数项 4.7", abs(r[0] + gamma * r[1] - 4.7) < 1e-9)
    chk("例6.3 G(1:3) 常数项 7.94", abs(r[0] + gamma * r[1] + gamma**2 * r[2] - 7.94) < 1e-9)
    chk("例6.3 G(1:4)=11.585", abs(G14 - 11.585) < 1e-9)

    # C5 例6.4 Q学习法
    q = {(1, "左"): 0.0, (1, "右"): 0.0, (2, "左"): 0.0, (2, "右"): 0.0}
    q[(1, "左")] = 0 + alpha * (-1 + 1.0 * 0 - 0)
    chk("例6.4 数据1 q(s1,左)=-0.1", abs(q[(1, "左")] + 0.1) < 1e-9)
    q[(1, "右")] = 0 + alpha * (0 + 1.0 * max(q[(2, "左")], q[(2, "右")]) - 0)
    chk("例6.4 数据2 q(s1,右) 不变为 0", abs(q[(1, "右")]) < 1e-9)
    q[(2, "右")] = 0 + alpha * (1 - 0)
    chk("例6.4 数据3 q(s2,右)=0.1", abs(q[(2, "右")] - 0.1) < 1e-9)
    q[(1, "右")] = q[(1, "右")] + alpha * (0 + 1.0 * max(q[(2, "左")], q[(2, "右")]) - q[(1, "右")])
    chk("例6.4 数据4 q(s1,右)=0.01（用max=0.1，与s2实际选左无关）",
        abs(q[(1, "右")] - 0.01) < 1e-9)

    # C6 例6.5 期望Sarsa
    exp_t = 0.9 * (0.5 * 0.1 + 0.5 * 0.3)
    chk("例6.5 期望Sarsa 目标 0.18", abs(exp_t - 0.18) < 1e-9)
    chk("例6.5 Sarsa 采样 0.09/0.27、Q max 0.27",
        abs(0.9 * 0.1 - 0.09) < 1e-9 and abs(0.9 * 0.3 - 0.27) < 1e-9)

    # C7 例6.6 确定性等价
    v2 = 1 / 0.19
    v1 = 0.9 * v2
    chk("例6.6 v(s1)≈4.74、v(s2)≈5.26", abs(v1 - 4.74) < 0.005 and abs(v2 - 5.26) < 0.005)

    print(f"  公式判定: {'全部通过' if not fails else '失败项: ' + ', '.join(fails)}\n")
    return not fails


# ---------- D. 引用抽取 ----------
def extract_refs():
    print("=== D. 交叉引用抽取 ===")
    insec = {}
    figref = {}
    cross = {}
    for f in FILES:
        with open(f, encoding="utf-8") as fh:
            content = fh.read()
        # 章内节引用 "6.N"
        secs = sorted(set(re.findall(r"6\.[1-8]", content)))
        insec[os.path.basename(f)] = secs
        # 图引用
        figs = sorted(set(re.findall(r"图\s*6-\d+", content)))
        if figs:
            figref[os.path.basename(f)] = figs
        # 跨章引用
        chs = sorted(set(re.findall(r"第[0-9一二三四五六七八九十]+章", content)))
        if chs:
            cross[os.path.basename(f)] = chs
    for name, secs in insec.items():
        print(f"  {name} 节内引用: {secs}")
    print(f"  图引用: {figref if figref else '（正文无显式图号引用）'}")
    for name, chs in cross.items():
        print(f"  跨章引用 {name}: {chs}")
    print()


if __name__ == "__main__":
    s_ok = check_structure()
    check_lengths()
    f_ok = verify_formulas()
    extract_refs()
    print(f"== 汇总：结构 {'通过' if s_ok else '不通过'}；公式 {'通过' if f_ok else '不通过'} ==")
    sys.exit(0 if (s_ok and f_ok) else 1)
