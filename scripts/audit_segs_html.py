# -*- coding: utf-8 -*-
"""统稿核查一：从 81 个 segs json 首段提取自指篇名 → 校验 16-81 权威篇名序列
统稿核查二：比对 html(轻量) 内嵌 SUBS JSON 与 segs json 的一致性（内容不同步检测）"""
import json
import re
from pathlib import Path

VD = Path(r"C:\Users\DELL\tcmP\docs\视频")
PIAN = ["上古天真论","四气调神大论","生气通天论","金匮真言论","阴阳应象大论","阴阳离合论",
        "阴阳别论","灵兰秘典论","六节藏象论","五脏生成","五脏别论","异法方宜论","移精变气论",
        "汤液醪醴论","玉版论要","诊要经终论","脉要精微论","平人气象论","玉机真藏论","三部九候论",
        "经脉别论","脏气法时论","宣明五气","血气形志","宝命全形论","八正神明论","离合真邪论",
        "通评虚实论","太阴阳明论","阳明脉解","热论","刺热","评热病论","逆调论","疟论","刺疟",
        "气厥论","咳论","举痛论","腹中论","刺腰痛","风论","痹论","痿论","厥论","病能论","奇病论",
        "大奇论","脉解","刺要论","刺齐论","刺禁论","刺志论","针解","长刺节论","皮部论","经络论",
        "气穴论","气府论","骨空论","水热穴论","调经论","缪刺论","四时刺逆从论","标本病传论",
        "天元纪大论","五运行大论","六微旨大论","气交变大论","五常政大论","六元正纪大论",
        "至真要大论","本病论","刺法论","著至教论","示从容论","疏五过论","徵四失论","阴阳类论",
        "方盛衰论","解精微论"]

def first_orig_talk(data):
    for s in data:
        blob = (s.get("orig", "") + s.get("talk", "") + s.get("title", ""))[:260]
        if blob.strip():
            return blob
    return ""

print("== 篇名自指核查（首段 260 字内命中的篇名候选 Top3）==")
seq = {}
for f in sorted(VD.glob("segs_suwen*.json"), key=lambda x: int(x.name.replace("segs_suwen", "").replace(".json", ""))):
    ch = int(f.name.replace("segs_suwen", "").replace(".json", ""))
    data = json.loads(f.read_text(encoding="utf-8"))
    blob = first_orig_talk(data)
    hits = [(p, blob.count(p)) for p in PIAN if p in blob]
    hits.sort(key=lambda x: -x[1])
    top = hits[:3]
    seq[ch] = top
    if ch >= 14:
        print(f"  SW{ch}: {top if top else '（无命中）'} | {blob[:70]!r}")

print("\n== html SUBS vs segs json 一致性抽查 ==")
for ch in [1, 2, 16, 50, 72, 73, 74, 81]:
    jf = VD / f"segs_suwen{ch}.json"
    if not jf.exists():
        continue
    segs = json.loads(jf.read_text(encoding="utf-8"))
    # 找轻量 html
    cands = [x for x in VD.glob(f"素问*-视频课程.html") if re.match(rf"素问0?{ch}-", x.name)]
    if not cands:
        print(f"  篇{ch}: 无 html")
        continue
    hf = cands[0]
    txt = hf.read_text(encoding="utf-8", errors="ignore")
    m = re.search(r"const SUBS = (\[.*?\]);\n", txt, re.S)
    if not m:
        print(f"  篇{ch}: html 中未找到 SUBS")
        continue
    try:
        subs = json.loads(m.group(1))
    except Exception as e:
        print(f"  篇{ch}: SUBS 解析失败 {e}")
        continue
    diffs = 0
    for i, (a, b) in enumerate(zip(segs, subs)):
        for k in ("title", "orig", "talk"):
            if a.get(k) != b.get(k):
                diffs += 1
                if diffs <= 3:
                    print(f"  篇{ch} 段{i+1}.{k} 不同: segs={str(a.get(k))[:40]!r} html={str(b.get(k))[:40]!r}")
    if len(segs) != len(subs):
        print(f"  篇{ch}: 段数不一致 segs={len(segs)} html={len(subs)}")
    print(f"  篇{ch}: {'一致 ✓' if diffs == 0 and len(segs) == len(subs) else f'差异 {diffs} 处'}")
