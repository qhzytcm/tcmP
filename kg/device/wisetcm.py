# -*- coding: utf-8 -*-
"""智慧中医学对接层（对标《智慧中医学》高等教育出版社 2026-03）
事实来源：百度百科词条 wapbaike 移动页实测抓取（内容简介 + 全目录三篇七章）。
用途：为 D07-S11《中医智能仪器与可穿戴设备》提供高校教材体系、实训设备清单与展望框架。
"""
from __future__ import annotations

BOOK = dict(title="智慧中医学", publisher="高等教育出版社", date="2026-03-05",
            isbn="9787040652802", series="「生物医学-中医药」新兴领域「十四五」高等教育教材",
            structure="全书分为三篇共七章",
            audience="中医药高等院校中医学及相关专业、医学信息学、综合院校人工智能相关专业",
            digital="拓展阅读 · 微视频 · 教学课件 · 思维导图",
            source="百度百科 wapbaike 移动页实测抓取（内容简介/目录）")

TOC = [
    dict(part="上篇 基础篇", chapters=[
        dict(ch="第一章 智慧中医学概述", secs=[
            "中医学发展历史、现状及需求",
            "人工智能技术及其引入中医学领域的目的和意义",
            "智慧中医学的内涵及任务",
            "人工智能在中医学领域中的应用研究概况",
            "智慧中医伦理要求",
            "智慧中医基本条件"])
        ,
        dict(ch="第二章 人工智能基础", secs=[
            "人工智能三要素（数据·算法·算力）",
            "中医诊疗中人工智能的实现路径",
            "人工智能技术（机器学习/深度学习/知识图谱与数据挖掘/扩展现实/智能装备）",
            "生成式人工智能（GPT 基础模型/扩散模型/开源高性能大模型 DeepSeek）"]),
    ]),
    dict(part="中篇 应用篇", chapters=[
        dict(ch="第三章 智慧中医预警与诊断", secs=[
            "智能技术与中医预警（治未病 / 体质辨识）",
            "智能技术与中医诊断（望 / 闻 / 问 / 切 / 四诊合参）"]),
        dict(ch="第四章 智慧中医治疗与康复", secs=[
            "智能技术与中医药及针灸治疗",
            "智能技术与中医康复（运动康复 / 推拿按摩康复）"]),
        dict(ch="第五章 智慧中医科研与教学", secs=[
            "智能技术与中医科学研究（理论研究 / 针灸技术研究 / 名中医经验传承）",
            "智能技术与中医教学（课程应用 / 中医思维培养）"]),
        dict(ch="第六章 智慧中医综合实训", secs=[
            "基于现有智慧中医设备、系统的实践训练",
            "基于问题导向的智慧中医设备改进思路与方法",
            "基于目标导向的智慧中医理论研究、设备或系统研发的探索"]),
    ]),
    dict(part="下篇 展望篇", chapters=[
        dict(ch="第七章 智慧中医发展前景与展望", secs=[
            "智慧中医总体定位（顶层设计 / 未来交叉重点领域）",
            "存在的问题及挑战（预警诊断 / 治疗康复 / 科研教学）",
            "发展趋势（六条）"]),
    ]),
]

# 第六章第一节：现有智慧中医设备（实训清单）——直接扩展本课程器械分类
TRAINING_DEVICES = [
    dict(name="智能中医四诊仪", cat="C1 诊断类", here="第七章 脉舌客观化 / 第八章 四诊合参", note="望闻问切集成采集"),
    dict(name="目诊仪", cat="C1 诊断类", here="第十一章 P 光子", note="眼象（白睛络脉）图像采集与分析"),
    dict(name="方剂配伍实训系统", cat="软件系统", here="D02 中药 / 方剂学", note="配伍规则与禁忌的交互式训练"),
    dict(name="智能中医红外热像仪", cat="C1 诊断类", here="第十一章 P 光子（远红外）", note="体表温度分布（寒热辨证的客观化）"),
    dict(name="人体经穴探测实训系统", cat="C1 诊断类", here="第十一章 E 电子/电压", note="经穴电阻抗探测（经络客观化）"),
    dict(name="针刺手法采集系统", cat="C2 治疗类", here="第十一章 M 质量 / K 运动", note="手法力—位移曲线采集（提插捻转量化）"),
    dict(name="智能艾灸机器人", cat="C2 治疗类", here="第十一章 E/M", note="温控与安全边界（避免烫伤）"),
]

# 第六章第二节：问题导向的设备改进对象
IMPROVE = [
    dict(name="智能中医脉诊仪", issue="脉位/脉势标准化不足、个体差异大", dir="第十一章 M 质量（压力阵列）+ 质控 SQI"),
    dict(name="智能中医舌面诊仪", issue="光源一致性差（同舌异色）", dir="第十一章 P 光子（色卡校正）+ 第五章 质控"),
    dict(name="智能艾灸机器人", issue="灸量与安全边界缺量化", dir="第十一章 E/M（温控）+ 第十章 伦理与安全"),
]

GENAI = ["GPT 基础模型", "扩散模型", "开源高性能大模型 DeepSeek"]
TECH = ["机器学习", "深度学习", "知识图谱与数据挖掘", "扩展现实", "智能装备"]
AI3 = ["数据", "算法", "算力"]

ETHICS = ["中医大健康数据隐私与保密", "医疗事故责任与潜在风险",
          "智能推理结果的偏见与道德规范实践", "决策建议与医患关系"]
BASIC_COND = ["智慧中医标准化需求及体系构建", "智慧中医临床应用需求"]

TRENDS = ["人工智能助推中医健康状态辨识及健康预警",
          "人工智能助力中医智能设备的发展",
          "人工智能赋能中医海量数据的深入挖掘",
          "人机结合深入传承发展中医药",
          "智慧中医标准化体系建设",
          "智慧中医产业化发展"]

CHALLENGES = ["智慧中医预警与诊断存在的问题及挑战",
              "智慧中医治疗与康复存在的问题及挑战",
              "智慧中医科研与教学存在的问题及挑战"]


def summary():
    return dict(book=BOOK, toc=TOC, training_devices=TRAINING_DEVICES, improve=IMPROVE,
                genai=GENAI, tech=TECH, ai3=AI3, ethics=ETHICS, basic_conditions=BASIC_COND,
                trends=TRENDS, challenges=CHALLENGES,
                stats=dict(parts=len(TOC), chapters=sum(len(p["chapters"]) for p in TOC),
                           devices=len(TRAINING_DEVICES), improve=len(IMPROVE), trends=len(TRENDS)))


if __name__ == "__main__":
    import json
    s = summary()
    print(json.dumps({k: v for k, v in s.items() if k != "toc"}, ensure_ascii=False, indent=1)[:800])
    print("篇/章/设备/改进/趋势:", s["stats"])