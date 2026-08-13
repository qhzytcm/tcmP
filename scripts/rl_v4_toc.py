# -*- coding: utf-8 -*-
"""
rl_v4_toc.py — 《强化学习的数学原理-赵世钰》四级目录数据（0cmrl目录 v3）
=======================================================================
v3 增强（三审现实映射 + 职业应用 + 篇幅预算 ≤30 万字）:
  1) 三审现实映射: 主编(user.md)/中医药主审(tcmreviewer.md)/智能主审(aireviewer.md)
  2) 职业应用导向: 每章 2 个『职业应用』小节（职业矩阵 6 方向）
  3) 篇幅预算: 每章 3 万字（段落 500 字基准，逐级分摊）
编码: 四级 —— 章(N) · 节(N.1) · 小节(N.1.1) · 段落(N.1.1.1)
每章结构: 引言 → 知识节(6) → 平台实践节 → 中医药语境与职业应用节 → 章末小结
行: (层级, 编码, 标题, 内容定位, 预计字数, 主编, 中医药主审, 智能主审, 双目标/职业标注)
"""
from __future__ import annotations
import re

from rl_v3_a import CHAPTERS_A
from rl_v3_b import CHAPTERS_B
from rl_v3_c import CHAPTERS_C

CHAPTERS = CHAPTERS_A + CHAPTERS_B + CHAPTERS_C

# ── 篇幅预算（每章 3 万字，全书 ≤30 万字）──
CHAP_WORDS = 30000
SEC_WORDS = 3000          # 知识节 = 3 小节 × 2 段 × 500
INTRO_WORDS = 1500        # 章首引言
PRACTICE_SEC = 2400       # 平台实践节 = 3 小节 × 2 段 × 400
TCM_SUB = 1000            # 语境小节 = 2 段 × 500
CAREER_SUB = 1500         # 职业小节 = 3 段 × 500
SUMMARY_SUB = 1500        # 章末小结与习题
PARA_WORDS = 500          # 段落字数基准

TCM_ITEMS = [
    ("中医辨证的场景化理解", "以四诊信息为状态、辨证结论为动作的中医视角重述本章概念"),
    ("tcmP 平台映射", "本章知识在六者平台/病证库/医圣 SOUL 中的对应物"),
    ("医案与病证数据示例", "用 DSU 真实病证单元（失眠/感冒/头痛）演示本章概念"),
]

CAREER_ROLES = {
    "临床医师": "辨证决策辅助/诊疗路径优化/师带徒学习（六者·医者视角）",
    "医院管理": "CDSS 质控/排班与资源调度/流程优化（六者·规者视角）",
    "药企研发": "方剂优化/疗效统计/用药安全策略（六者·药者视角）",
    "AI工程": "平台算法研发/模型训练与部署/检索与 Agent 工程",
    "医工器械": "可穿戴数据学习/康复设备自适应/诊疗仪器智能化（六者·械者视角）",
    "教育科研": "学习路径设计/科研方法/教材与课程开发（师带徒视角）",
}
CAREER_PER_CHAPTER = {
    1: ("临床医师", "教育科研"), 2: ("临床医师", "医院管理"),
    3: ("临床医师", "AI工程"), 4: ("医院管理", "AI工程"),
    5: ("药企研发", "临床医师"), 6: ("AI工程", "医院管理"),
    7: ("临床医师", "医工器械"), 8: ("AI工程", "医工器械"),
    9: ("AI工程", "药企研发"), 10: ("临床医师", "医院管理"),
}


def _reviewers(lv: str, title: str) -> tuple:
    t = title
    if lv == "章" or "职业" in t or "小结" in t or "引言" in t:
        return ("✓", "○", "○")
    if any(k in t for k in ("中医药", "辨证", "医案", "证候", "方剂", "语境",
                            "四诊", "病证", "医圣", "六者", "临床")):
        return ("○", "✓", "○")
    return ("○", "○", "✓")   # 数学/算法/接口/实践 → 智能主审


def _clean_sec(title: str) -> str:
    return re.sub(r"^\d+\.\d+\s*", "", title).strip()


def _short(title: str, n: int = 8) -> str:
    return re.sub(r"[（(：:].*$", "", title).strip()[:n]


def _subsections(sec_title: str) -> list:
    t = sec_title
    if any(k in t for k in ("定义", "概念", "价值")):
        return [("概念引入", "核心概念由来与动机"), ("数学表述", "定义/记号/公式"),
                ("性质与直观", "性质与网格世界示例")]
    if any(k in t for k in ("算法", "迭代", "方法", "求解")):
        return [("算法思想", "核心思想"), ("实现步骤", "矩阵/元素形式"),
                ("收敛与性质", "收敛性与实例演算")]
    if any(k in t for k in ("方程", "推导", "定理")):
        return [("问题设定", "问题与记号"), ("推导过程", "关键步骤"),
                ("结论与应用", "定理结论与影响")]
    return [("知识要点", "知识点梳理"), ("方法与示例", "方法与示例"),
            ("小结与衔接", "小结与衔接")]


def toc_rows() -> list:
    rows = []
    for ch_idx, ch in enumerate(CHAPTERS, 1):
        chap_name = re.sub(r"^第[一二三四五六七八九十\d]+章\s*", "",
                           ch["title"].split("（")[0].split("(")[0].strip())
        e, t, a = _reviewers("章", chap_name)
        rows.append(("章", f"第{ch_idx}章", chap_name,
                     "本章知识结构：引言→知识节→平台实践→中医药语境与职业应用→小结",
                     CHAP_WORDS, e, t, a,
                     "双目标：教材3万字预算+平台；三审：主编统筹+双主审协审"))

        # 知识节（Part1 节，最多 6 节）
        secs = [(_clean_sec(m.split("] ", 1)[1].strip()), c)
                for m, c in ch["rows"] if m.startswith("[Part1]")][:6]
        p2 = [c for m, c in ch["rows"] if m.startswith("[Part2]")]
        secs.append(("平台实践与实训", "；".join(c[:40] for c in p2)))

        n_secs = len(secs)
        for sec_idx, (sec_title, sec_content) in enumerate(secs, 1):
            is_practice = sec_title.startswith("平台实践")
            sec_words = PRACTICE_SEC if is_practice else SEC_WORDS
            code_sec = f"{ch_idx}.{sec_idx}"
            e, t, a = _reviewers("节", sec_title)
            rows.append(("节", code_sec, sec_title,
                         sec_content[:60] + ("…" if len(sec_content) > 60 else ""),
                         sec_words, e, t, a, "节定位：现代强化学习知识体系"))

            for sub_idx, (sub_title, sub_note) in enumerate(
                    _subsections(sec_title), 1):
                code_sub = f"{code_sec}.{sub_idx}"
                sub_name = f"{_short(sec_title)}·{sub_title}"
                e, t, a = _reviewers("小节", sub_name)
                rows.append(("小节", code_sub, sub_name, sub_note,
                             sec_words // 3, e, t, a, "小节定位：知识点组织"))
                for para_idx, (pt, pn) in enumerate(
                        [("知识点一", f"核心概念（{sec_title}）"),
                         ("知识点二", f"公式/示例要点（{sec_title}）")], 1):
                    e, t, a = _reviewers("段落", pt)
                    rows.append(("段落", f"{code_sub}.{para_idx}",
                                 f"{_short(sec_title, 6)}·{pt}", pn,
                                 PARA_WORDS, e, t, a, "教材正文要点"))

        # 中医药语境与职业应用节（特色节，含 3 语境 + 2 职业 + 章末）
        feat_code = f"{ch_idx}.{n_secs + 1}"
        e, t, a = _reviewers("节", "中医药语境与职业应用")
        rows.append(("节", feat_code, "中医药语境与职业应用",
                     "双目标特色节：中医药智能专业适配 + 职业应用导向",
                     TCM_SUB * 3 + CAREER_SUB * 2, e, t, a,
                     "三审：语境→中医药主审、职业→主编统筹、数据→智能主审"))
        for sub_idx, (sub_title, sub_note) in enumerate(TCM_ITEMS, 1):
            code_sub = f"{feat_code}.{sub_idx}"
            e, t, a = _reviewers("小节", "中医药·" + sub_title)  # 语境→中医药主审
            rows.append(("小节", code_sub, sub_title, sub_note,
                         TCM_SUB, e, t, a, "双目标特色小节"))
            for para_idx, (pt, pn) in enumerate(
                    [("知识要点", f"核心概念在{sub_title}中的体现"),
                     ("平台落地", "对应 tcmP 平台能力（检索/Agent/病证库/医圣 SOUL）")], 1):
                e, t, a = _reviewers("段落", pt)
                rows.append(("段落", f"{code_sub}.{para_idx}", pt, pn,
                             PARA_WORDS, e, t, a, "双目标标注"))
        # 职业应用小节（2 个）
        for c_idx, role in enumerate(CAREER_PER_CHAPTER.get(ch_idx, ("临床医师", "AI工程")), 1):
            code_career = f"{feat_code}.{len(TCM_ITEMS) + c_idx}"
            e, t, a = _reviewers("小节", "职业应用")
            rows.append(("小节", code_career, f"职业应用·{role}",
                         CAREER_ROLES[role], CAREER_SUB, e, t, a,
                         "职业导向：学员结合职业特点灵活运用 RL"))
            for para_idx, (pt, pn) in enumerate(
                    [(f"{role}的 RL 应用场景", f"{role}如何用本章知识解决问题"),
                     ("方法与工具链", "平台接口/算法工具（tcmP API、numpy 等）"),
                     ("案例与趋势适应", "典型职业案例 + AI 趋势适应路径")], 1):
                e, t, a = _reviewers("段落", pt)
                rows.append(("段落", f"{code_career}.{para_idx}", pt, pn,
                             500, e, t, a, "职业应用标注"))
        # 章末小结与习题
        code_end = f"{feat_code}.{len(TCM_ITEMS) + 3}"
        rows.append(("小节", code_end, "本章小结与习题",
                     "知识回顾 + 60-30-10 分层习题", SUMMARY_SUB,
                     "✓", "○", "○", "三审：主编定稿 + 双主审会签"))
    return rows


if __name__ == "__main__":
    rows = toc_rows()
    stats = {}
    for lv, *_ in rows:
        stats[lv] = stats.get(lv, 0) + 1
    chap_total = sum(w for lv, _, _, _, w, *_ in rows if lv == "章")
    # 校验口径：只统计"节"级预算（最粗粒度，互不包含）+ 章末小结小节
    sec_total = sum(w for lv, _, _, _, w, *_ in rows if lv == "节")
    sum_sub = sum(w for lv, _, title, _, w, *_ in rows
                  if lv == "小节" and "本章小结" in str(title))
    print("四级统计:", stats, "总行", len(rows))
    print(f"全书预算（章行声明）: {chap_total:,} 字（目标 ≤300,000）")
    print(f"节级合计: {sec_total:,} + 章末小结 {sum_sub:,} = {sec_total + sum_sub:,} 字"
          f"（≈每章 {round((sec_total + sum_sub) / 10):,} 字，含引言余量）")
    for ci in range(1, 11):
        c_sec = sum(w for lv, code, _, _, w, *_ in rows
                    if lv == "节" and code.startswith(f"{ci}."))
        c_end = sum(w for lv, code, title, _, w, *_ in rows
                    if lv == "小节" and code.startswith(f"{ci}.")
                    and "本章小结" in str(title))
        flag = "✓" if abs((c_sec + c_end) - CHAP_WORDS) <= 4000 else "⚠️"
        print(f"  第{ci}章 正文预算 {c_sec + c_end:,} 字 {flag}")
