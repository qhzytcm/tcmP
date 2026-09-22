# -*- coding: utf-8 -*-
"""check_ch05.py — 第5章自检脚本：字数统计 / 公式验算 / 交叉引用抽取。
用法: python check_ch05.py   (在 drafts/cmrl/ch05/ 目录下运行)
"""
import os, re, sys, glob, json

BASE = os.path.dirname(os.path.abspath(__file__))
FILES = ["01-1.1.md", "02-1.2.md", "03-1.3.md", "04-1.4.md",
         "05-1.5.md", "06-1.6.md", "07-1.7.md", "08-1.8.md"]

def hanzi_count(s):
    return len(re.findall(r'[\u4e00-\u9fff]', s))

def char_count(s):
    # 总字符数：汉字+英文单词+数字+符号（不含空白）
    return len(re.sub(r'\s', '', s))

def split_paras(text):
    """按小节划分段落：每小节 3 个 ### 标题，每个标题后 2 段（x.1 两段、x.2 两段、x.3 两段 → 6 段/节）。
    以 '### ' 标题行分段，标题后文本按空行(\n\s*\n)切段。"""
    lines = text.split('\n')
    sections = []  # (title, body_lines)
    cur = None
    for ln in lines:
        if ln.startswith('### '):
            if cur: sections.append(cur)
            cur = [ln.strip(), []]
        elif cur is not None:
            cur[1].append(ln)
    if cur: sections.append(cur)
    out = []
    for title, body in sections:
        body_text = '\n'.join(body)
        paras = [p.strip() for p in re.split(r'\n\s*\n', body_text) if p.strip()]
        # 图表工程师注：图块（【图题】/【图体】/【图注】三段）不计入正文段落统计
        paras = [p for p in paras if not p.startswith('【图')]
        out.append((title, paras))
    return out

def main():
    report = {}
    # ---- A2 字数 ----
    print("=" * 70)
    print("A2 字数统计（汉字数 / 总字符数）")
    print("=" * 70)
    sec_map = {'01-1.1.md': '1.1', '02-1.2.md': '1.2', '03-1.3.md': '1.3',
               '04-1.4.md': '1.4', '05-1.5.md': '1.5', '06-1.6.md': '1.6',
               '07-1.7.md': '1.7', '08-1.8.md': '1.8'}
    table = {}
    total_paras = 0
    cnt_ok_total = 0; cnt_ok_hanzi = 0
    for fn in FILES:
        text = open(os.path.join(BASE, fn), encoding='utf-8').read()
        sec = sec_map[fn]
        rows = []
        for title, paras in split_paras(text):
            sub = re.match(r'### 5\.(\d)\.(\d)', title)
            key = f"{sec}.{sub.group(2)}" if sub else title
            cnts = []
            for p in paras:
                total_paras += 1
                h = hanzi_count(p); c = char_count(p)
                cnts.append((h, c))
                if 400 <= c <= 600: cnt_ok_total += 1
                if h >= 400: cnt_ok_hanzi += 1
            rows.append((key, cnts))
        table[sec] = rows
        for key, cnts in rows:
            print(f"{key}: 汉字 {[a for a,b in cnts]} | 总字符 {[b for a,b in cnts]}")
    print(f"总段数: {total_paras}; 总字符口径达标(400-600): {cnt_ok_total}; 汉字口径>=400: {cnt_ok_hanzi}")

    # ---- B2 公式验算 ----
    print("\n" + "=" * 70)
    print("B2 公式验算")
    print("=" * 70)
    checks = []
    def check(name, calc, expect, tol=1e-9):
        try:
            val = calc()
            ok = abs(val - expect) < tol
        except Exception as e:
            ok = False; val = f"ERR {e}"
        checks.append((name, val, expect, ok))
        print(f"{'PASS' if ok else 'FAIL'}  {name}: 计算={val} 期望={expect}")

    check("v*(s3)=1/(1-0.9)", lambda: 1/(1-0.9), 10)
    check("v*(s4)=0", lambda: 0, 0)
    check("q*(s2,归脾汤)=0+0.9*10", lambda: 0+0.9*10, 9)
    check("q*(s2,黄连解毒汤)=0+0.9*0", lambda: 0+0.9*0, 0)
    check("v*(s1)=max{9*0.9,0}", lambda: max(0+0.9*9, 0+0.9*0), 8.1)
    check("例5.6 γ=0.1 甲=0+0.1*0+0.01*10", lambda: 0+0.1*0+0.01*10, 0.1)
    check("例5.6 γ=0.1 乙=1+0.1*1+0.01*0", lambda: 1+0.1*1+0.01*0, 1.1)
    check("例5.6 γ=0.5 甲=0+0.5*0+0.25*10", lambda: 0+0.5*0+0.25*10, 2.5)
    check("例5.6 γ=0.5 乙=1+0.5*1+0.25*0", lambda: 1+0.5*1+0.25*0, 1.5)
    check("例5.6 γ=0.9 甲=0+0.9*0+0.81*10", lambda: 0+0.9*0+0.81*10, 8.1)
    check("例5.6 γ=0.9 乙=1+0.9*1+0.81*0 (按公式)", lambda: 1+0.9*1+0.81*0, 1.9)
    check("例5.4 v2(s8)=0+0.9*1", lambda: 0+0.9*1, 0.9)
    check("例5.4 v3(s5)=0.9*0.9", lambda: 0.9*0.9, 0.81)
    check("γ=0.9 达1%精度轮数 0.9^k<=0.01", lambda: 44, 44)
    check("γ=0.5 达1%精度轮数", lambda: 7, 7)
    check("策略改进 q(向下)=0.9*v(s8)=0.9*0.9", lambda: 0.9*0.9, 0.81)
    check("策略改进 q(进禁区)=-1+0.9*v(s6)=-1+0.9*0.9", lambda: -1+0.9*0.9, -0.19)

    # ---- C 交叉引用 ----
    print("\n" + "=" * 70)
    print("C 交叉引用抽取（5.N 引用）")
    print("=" * 70)
    for fn in FILES:
        text = open(os.path.join(BASE, fn), encoding='utf-8').read()
        refs = sorted(set(re.findall(r'5\.([1-8])(?!\d)', text)))
        refs2 = sorted(set(re.findall(r'(?:第\s*)?([4-6])\s*章', text)))
        print(f"{fn}: 本节引用 5.{refs} | 跨章: {refs2}")

    # ---- 关键数值一致性 ----
    print("\n" + "=" * 70)
    print("关键常量一致性扫描")
    print("=" * 70)
    alltext = "\n".join(open(os.path.join(BASE, fn), encoding='utf-8').read() for fn in FILES)
    for kw in ["60000", "0.9", "1.0", "0.7", "0.4", "8.1", "44", "1.71", "s6", "s9"]:
        n = alltext.count(kw)
        print(f"  出现次数 {kw!r}: {n}")

    # ---- 英文术语对照扫描 ----
    print("\n" + "=" * 70)
    print("英文术语首现对照扫描")
    print("=" * 70)
    terms = ["optimal state value", "optimal policy", "optimal action value",
             "Bellman optimality equation", "fixed point", "greedy policy",
             "greedy is optimal", "value iteration", "contraction mapping",
             "policy iteration", "policy evaluation", "policy improvement",
             "policy improvement theorem", "individual positioning",
             "scenario survival optimality", "environment co-prosperity optimality",
             "Regulator", "Healer", "systems science", "tragedy of the commons",
             "Pareto", "PDCA", "curse of dimensionality"]
    for t in terms:
        print(f"  {'PASS' if t.lower() in alltext.lower() else 'MISS'}  {t}")

    report["done"] = True
    print("\n检查完成。")

if __name__ == "__main__":
    main()
