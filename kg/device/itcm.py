# -*- coding: utf-8 -*-
"""智能中医学对接层（对标《智能中医学概论》田贵华、商洪才 主编·人民卫生出版社 2021-11）
事实来源：百度百科词条 wapbaike 移动页实测抓取（含 内容简介/作者简介/目录 全七章）。
用途：为 D07-S11《中医智能仪器与可穿戴设备》提供"智能中医学"学科框架与四诊采集定位。
"""
from __future__ import annotations

BOOK = dict(title="智能中医学概论", authors=["田贵华", "商洪才"], publisher="人民卫生出版社",
            date="2021-11", isbn="9787117323505", kind="学术专著",
            source="百度百科 wapbaike 移动页实测抓取（内容简介/作者简介/目录）")

AUTHORS = [
    dict(name="田贵华", role="北京中医药大学东直门医院科技处处长",
         work="建立「循证优化-精准辨证-疗效验证」针药结合疼痛临床诊疗模式；SCI 42 篇；主持国家级课题 4 项",
         honor="国家「万人计划」青年拔尖人才；国家科技进步二等奖"),
    dict(name="商洪才", role="北京中医药大学东直门医院常务副院长、国际循证中医药研究院副院长",
         work="创建中医药循证研究「四证」方法学体系；主持国家/省部级项目 13 项",
         honor="国家杰出青年基金；国家万人计划科技创新领军人才；2020 年度国家科学技术进步奖二等奖"),
]

CONCEPT = "智能中医学是融合中医理论与人工智能技术的新兴交叉学科（该书首次系统提出）"
PATH = "客观化检测技术 + 中医药大数据 + 人工智能 → 中医药信息的客观化与智能化"
MOTTO = "数据筑基、智慧引航"
FRAMEWORK = "象—素—候—证"          # 辨证框架
METHOD = "中医药循证研究「四证」方法学体系（群体证据与个体证据相融合）"
CASE = "中医慢性疼痛智能诊疗"

TOC = [
    dict(ch="绪言", secs=[]),
    dict(ch="第一章 中医学基础", secs=["中医学发展简史", "中医学特点", "中医学诊疗体系", "问题与挑战"]),
    dict(ch="第二章 人工智能基础", secs=["人工智能概述", "传统机器学习", "深度学习"]),
    dict(ch="第三章 智能中医学的产生与发展", secs=["智能中医学的概念", "智能中医学的发展现状", "问题与挑战"]),
    dict(ch="第四章 智能中医诊疗的标准化", secs=["中医临床诊疗信息的特点", "中医诊疗数据的标准化", "诊疗过程的标准化", "疗效评价的标准化"]),
    dict(ch="第五章 智能中医诊疗技术及应用", secs=["四诊数据采集", "智能辅助诊断", "智能辅助治疗", "典型应用：中医慢性疼痛智能诊疗"]),
    dict(ch="第六章 智能中医学的科技布局", secs=["国家战略布局", "学术布局", "产业布局"]),
    dict(ch="第七章 智能中医学的未来", secs=[]),
]

# 与本课程（D07-S11 仪器与可穿戴）的对接点
BRIDGE = [
    dict(book="第五章 第一节 四诊数据采集", here="第十一章 可感测四元 / 第七章 脉舌客观化",
         note="该书「四诊数据采集」在本课程落到具体物理量（P/E/M/K）与传感器"),
    dict(book="第四章 标准化（数据/过程/疗效）", here="第四章 数据标准 / 第五章 质控",
         note="数据标准化=FHIR/IEEE11073/ICD-11；过程与疗效标准化=临床研究设计"),
    dict(book="第五章 第四节 慢性疼痛智能诊疗", here="第十四/十六章（疼痛·光遗传学对照）",
         note="疼痛客观化：HRV、皮电(E)、体动(K)构成的复合指标"),
    dict(book="辨证框架 象—素—候—证", here="D07-S02 中医信息学·语义张量",
         note="象(现象)→素(要素)→候(证候)→证(证型)：与语义张量三分量可互为投影"),
    dict(book="科技布局（国家/学术/产业）", here="第十篇 实验与展望",
         note="仪器与可穿戴的落点：医疗器械取证 + 临床研究 + 产业化"),
]


def summary():
    return dict(book=BOOK, authors=AUTHORS, concept=CONCEPT, path=PATH, motto=MOTTO,
                framework=FRAMEWORK, method=METHOD, case=CASE, toc=TOC, bridge=BRIDGE,
                stats=dict(chapters=len(TOC), bridge_points=len(BRIDGE)))


if __name__ == "__main__":
    import json
    s = summary()
    print(json.dumps({k: v for k, v in s.items() if k != "toc"}, ensure_ascii=False, indent=1)[:900])
    print("章数:", s["stats"]["chapters"], "| 对接点数:", s["stats"]["bridge_points"])