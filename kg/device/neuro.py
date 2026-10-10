# -*- coding: utf-8 -*-
"""光遗传学与神经调控（D07-S11 扩展层）
事实来源：nobelprize.org API（2026 生理学或医学奖，实测抓取）。
⚠️ 边界：光遗传学当前主要用于**动物实验与神经科学研究**；人体应用仍在研究/伦理审查阶段。
    与中医「经络/穴位光刺激」「光生物调节(LLT)」属**不同技术层级**，不可混同、不可宣称疗效。
"""
from __future__ import annotations

NOBEL_2026 = dict(
    prize="The Nobel Prize in Physiology or Medicine 2026",
    date="2026-10-05", amount_sek=12000000,
    laureates=["Karl Deisseroth", "Peter Hegemann", "Georg Nagel"],
    portions=["1/3", "1/3", "1/3"],
    motivation_en="for their discoveries concerning light-gated ion channels and optogenetics",
    motivation_cn="表彰其关于**光门控离子通道与光遗传学**的发现",
    source="https://api.nobelprize.org/2.1/nobelPrizes?nobelPrizeYear=2026（实测抓取）",
)

TECH = [
    dict(k="光敏蛋白（视蛋白）", v="ChR2 等光门控阳离子通道 → 光照去极化（兴奋）；Halorhodopsin 氯泵 → 光照超极化（抑制）"),
    dict(k="基因导入", v="病毒载体/转基因把视蛋白表达在特定神经元群"),
    dict(k="光传输", v="植入光纤/微型 LED，时相精度毫秒级"),
    dict(k="读出", v="电生理记录 + 行为学 + 影像（fMRI/钙成像）"),
    dict(k="时间分辨率", v="毫秒级（远高于药理学调控的分钟—小时级）"),
    dict(k="空间分辨率", v="细胞类型特异（由启动子决定），优于电极的解剖特异"),
]

TCM_CONTRAST = [
    dict(item="兴奋/抑制", opto="光门控通道去极化/超极化", tcm="补/泻；阴阳调节", note="层级不同：细胞—环路 vs 证候—整体"),
    dict(item="刺激位点", opto="特定核团/神经元类型", tcm="腧穴—经络（体表）", note="靶点尺度与作用路径均不同"),
    dict(item="物理手段", opto="可见光（基因依赖）", tcm="针·灸·按·光（无基因依赖）", note="光遗传需基因操作，非无创疗法"),
    dict(item="证据等级", opto="实验动物强证据，人体研究阶段", tcm="临床经验+循证研究", note="两者不可互相背书"),
]

BOUNDARY = [
    "光遗传学≠中医光疗：前者需要基因导入，属实验技术；后者（如低强度激光/红外）为无创物理因子。",
    "人体光遗传学应用尚处研究阶段，涉及基因治疗监管与伦理审查，**不得作为临床疗法宣传**。",
    "中医相关的研究方向（如经穴光刺激、光生物调节）须按医疗器械/临床研究路径取证，不可引用本 Nobel 为其背书。",
    "本教材所有仪器与算法输出均为**提示性**，不替代医师判断。",
]


def summary():
    return dict(nobel=NOBEL_2026, tech=TECH, tcm_contrast=TCM_CONTRAST, boundary=BOUNDARY,
                layers=["分子（光敏蛋白）", "细胞（神经元类型）", "环路（核团）", "行为（整体）"],
                tcm_layer="证候—整体（与上四层不同尺度，需通过「感—知—证」桥接）")


if __name__ == "__main__":
    import json
    print(json.dumps(summary(), ensure_ascii=False, indent=1)[:1200])