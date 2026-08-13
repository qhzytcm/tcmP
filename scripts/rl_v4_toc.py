# -*- coding: utf-8 -*-
"""
rl_v4_toc.py — 《强化学习的数学原理-赵世钰》四级目录数据（0cmrl目录 sheet）
=======================================================================
目标: 构建适应中医药大学智能专业的强化学习教材目录（双目标：平台+教材）
参考: rl_v3_a/b/c.py 十章知识结构（RL01-RL10）
编码: 四级 —— 章(1-10) · 节(1.1) · 小节(1.1.1) · 段落(1.1.1.1)
行: (层级, 编码, 标题, 内容定位, 双目标标注)
"""
from __future__ import annotations

from rl_v3_a import CHAPTERS_A
from rl_v3_b import CHAPTERS_B
from rl_v3_c import CHAPTERS_C

CHAPTERS = CHAPTERS_A + CHAPTERS_B + CHAPTERS_C

# 中医药智能专业特色小节注入（每节附加的语境小节）
TCM_SECTION = "中医药智能语境"
TCM_ITEMS = [
    ("中医辨证的场景化理解", "以四诊信息为状态、辨证结论为动作的中医视角重述本节概念"),
    ("tcmP 平台映射", "本节知识在六者平台/病证库/医圣 SOUL 中的对应物"),
    ("医案与病证数据示例", "用 DSU 真实病证单元（失眠/感冒/头痛）演示本节概念"),
]

# 段落生成规则（按小节主题返回 2-3 个段落要点）
PARA_RULES = {
    "概念": ["核心定义与记号", "直观解释与网格世界示例", "中医药语境解读"],
    "数学": ["问题设定与记号", "公式推导要点", "结论与性质"],
    "算法": ["算法思想", "实现步骤", "收敛性/复杂度与平台实现"],
    "性质": ["性质陈述", "证明思路", "对后续章节的意义"],
    "定理": ["定理内容", "证明思路", "在平台算法中的应用"],
    "应用": ["应用场景", "案例拆解", "平台实践路径"],
    "平台": ["平台接口与数据", "编程实现要点", "实践任务"],
}


def _clean_sec(title: str) -> str:
    """节标题清洗：去掉 '1.1 ' 编号前缀"""
    import re
    return re.sub(r"^\d+\.\d+\s*", "", title).strip()


def _short(title: str, n: int = 8) -> str:
    """取标题核心词（去掉标点/后缀）"""
    import re
    t = re.sub(r"[（(：:].*$", "", title).strip()
    return t[:n]


def toc_rows() -> list:
    rows = []
    for ch_idx, ch in enumerate(CHAPTERS, 1):
        chap_no = ch_idx  # 章编号 1-10
        chap_title = ch["title"]
        chap_name = chap_title.split("（")[0].split("(")[0].strip()
        import re as _re
        chap_name = _re.sub(r"^第[一二三四五六七八九十\d]+章\s*", "", chap_name)
        rows.append(("章", f"第{ch_idx}章", chap_name,
                     "本章知识结构：概念→方法→算法→平台实践",
                     "教材目标：掌握强化学习数学基础；平台目标：对接 tcmP 检索/Agent/六者"))

        # 节：来自 Part1 的节 + Part2 平台实践节
        secs = []
        for mod, content in ch["rows"]:
            if mod.startswith("[Part1]"):
                secs.append((_clean_sec(mod.split("] ", 1)[1].strip()), content))
        # Part2 平台实践并入每章末节
        p2 = [c for m, c in ch["rows"] if m.startswith("[Part2]")]
        secs.append(("平台实践与实训", "；".join(c[:40] for c in p2)))

        for sec_idx, (sec_title, sec_content) in enumerate(secs, 1):
            code_sec = f"{chap_no}.{sec_idx}"
            rows.append(("节", code_sec, sec_title,
                         sec_content[:60] + ("…" if len(sec_content) > 60 else ""),
                         "节定位：忠实现代强化学习知识体系"))

            # 小节：3 个知识小节 + 3 个中医药语境小节
            sub_items = _subsections(sec_title)
            for sub_idx, (sub_title, sub_note) in enumerate(sub_items, 1):
                code_sub = f"{code_sec}.{sub_idx}"
                sub_name = f"{_short(sec_title)}·{sub_title}"
                rows.append(("小节", code_sub, sub_name, sub_note,
                             "小节定位：知识点组织"))

                # 段落：每小节 2-3 段
                paras = _paragraphs(sub_title, sec_title)
                for para_idx, (para_title, para_note) in enumerate(paras, 1):
                    rows.append(("段落", f"{code_sub}.{para_idx}",
                                 f"{_short(sec_title, 6)}·{para_title}",
                                 para_note,
                                 "双目标：教材正文要点 + 平台对接"))

            # 中医药语境小节（含平台映射，体现双目标）
            for sub_idx, (sub_title, sub_note) in enumerate(TCM_ITEMS, len(sub_items) + 1):
                code_sub = f"{code_sec}.{sub_idx}"
                rows.append(("小节", code_sub, sub_title, sub_note,
                             "双目标特色小节：中医药智能专业适配"))
                paras = [
                    ("知识要点", f"本节核心概念在{sub_title}中的体现（{sec_title}）"),
                    ("平台落地", "对应 tcmP 平台能力（检索/Agent/病证库/医圣 SOUL）"),
                    ("教学衔接", "对接 ai-curriculum D07 课程与六者平台实训"),
                ]
                for para_idx, (para_title, para_note) in enumerate(paras, 1):
                    rows.append(("段落", f"{code_sub}.{para_idx}", para_title,
                                 para_note, "双目标标注"))
    return rows


def _subsections(sec_title: str) -> list:
    """每节 3 个知识小节（按节标题语义）"""
    t = sec_title
    if any(k in t for k in ("定义", "概念", "价值")):
        return [("概念引入", "本节核心概念的由来与问题动机"),
                ("数学表述", "定义、记号与公式（文字化）"),
                ("性质与直观", "关键性质与网格世界直观示例")]
    if any(k in t for k in ("算法", "迭代", "方法", "求解")):
        return [("算法思想", "算法要解决什么问题、核心思想"),
                ("实现步骤", "矩阵形式与元素形式的实现要点"),
                ("收敛与性质", "收敛性/复杂度分析与实例演算")]
    if any(k in t for k in ("方程", "推导", "定理", "证明")):
        return [("问题设定", "方程/定理解决的问题与记号"),
                ("推导过程", "关键推导步骤（含公式文字化）"),
                ("结论与应用", "定理结论及其对后续算法的影响")]
    if any(k in t for k in ("比较", "权衡", "统一")):
        return [("对比维度", "比较对象与维度（模型/方差/效率等）"),
                ("权衡分析", "各方法的优势与局限"),
                ("选择指南", "不同场景下的方法选择建议")]
    return [("知识要点", "本节核心知识点梳理"),
            ("方法与示例", "方法与网格世界/病证示例"),
            ("小结与衔接", "本节小结与下一节衔接")]


def _paragraphs(sub_title: str, sec_title: str) -> list:
    """每小节 2-3 个段落标题+定位"""
    for key, paras in PARA_RULES.items():
        if key in sub_title or key in sec_title:
            return [(p, f"段落定位：{p}（节：{sec_title}）") for p in paras]
    return [("知识点一", f"核心概念（{sub_title}）"),
            ("知识点二", f"公式/示例要点（{sub_title}）"),
            ("知识点三", f"中医药语境与平台对接（{sub_title}）")]


if __name__ == "__main__":
    rows = toc_rows()
    stats = {}
    for lv, *_ in rows:
        stats[lv] = stats.get(lv, 0) + 1
    print("四级目录统计:", stats, "总行", len(rows))
