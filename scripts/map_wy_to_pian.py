# -*- coding: utf-8 -*-
"""判定 wy01-30 每集对应的素问篇：篇名出现统计 + 首尾字幕"""
from pathlib import Path

base = Path(r"C:\Users\DELL\tcmP\scripts\_wyshan_text")
PIAN_NAMES = ["上古天真论", "四气调神大论", "生气通天论", "金匮真言论", "阴阳应象大论",
              "阴阳离合论", "阴阳别论", "灵兰秘典论", "六节藏象论", "五脏生成", "五脏别论",
              "异法方宜论", "移精变气论", "汤液醪醴论", "玉版论要", "诊要经终论",
              "脉要精微论", "平人气象论", "玉机真藏论", "三部九候论", "经脉别论",
              "脏气法时论", "宣明五气", "血气形志", "宝命全形论", "八正神明论",
              "离合真邪论", "通评虚实论", "太阴阳明论", "阳明脉解", "金匮真言"]

for i in range(1, 31):
    f = base / f"wy{i:02d}.txt"
    lines = [l.strip() for l in f.read_text(encoding="utf-8").splitlines() if l.strip()]
    joined = "\n".join(lines)
    hits = {}
    for p in PIAN_NAMES:
        c = joined.count(p)
        if c > 0:
            hits[p] = c
    top = sorted(hits.items(), key=lambda x: -x[1])[:6]
    print(f"\n===== wy{i:02d} (字幕{len(lines)}条) 篇名命中: {top if top else '无'} =====")
    print("  开头:", " / ".join(lines[:6])[:170])
    # 找含'篇'或'卷'或'讲到'或'结束'的句子（前部）
    clues = []
    for ln in lines[:120]:
        if any(k in ln for k in ["这一篇", "下一篇", "这篇叫", "讲完了", "结束", "篇是", "《", "卷"]):
            clues.append(ln)
    for c_ in clues[:4]:
        print("  线索:", c_[:90])
    print("  结尾:", " / ".join(lines[-4:])[:150])
