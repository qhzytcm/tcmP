# -*- coding: utf-8 -*-
"""完整统计 Hermes独立理解/广告语 污染结构：每篇每段 talk 形态分类"""
import json
import re
from pathlib import Path

VD = Path(r"C:\Users\DELL\tcmP\docs\视频")
HERMES_RE = re.compile(r"Hermes独立理解《[^》]*》[:：]")
AD_KW = ["搜索人纪求真", "搜索人际求真", "人纪求真下载", "应用商店搜索", "视频一听就懂",
         "告别学了后面忘", "快速梳理知识框架", "人纪求真", "手机应用商店", "人纪真"]

def classify(talk):
    tags = []
    if HERMES_RE.search(talk):
        # Hermes 段位置
        m = HERMES_RE.search(talk)
        prefix = talk[:m.start()]
        if len(prefix.strip()) < 10:
            tags.append("HERMES_全段")
        else:
            tags.append("HERMES_尾部")
    for kw in AD_KW:
        if kw in talk:
            tags.append(f"广告:{kw}")
            break
    return tags

summary = {}
detail = []
for f in sorted(VD.glob("segs_suwen*.json"), key=lambda x: int(x.name.replace("segs_suwen", "").replace(".json", ""))):
    ch = f.name.replace("segs_suwen", "").replace(".json", "")
    data = json.loads(f.read_text(encoding="utf-8"))
    stats = {"seg_count": len(data), "hermes_full": [], "hermes_tail": [], "ad": []}
    for si, s in enumerate(data, 1):
        t = s.get("talk", "")
        o = s.get("orig", "")
        for label, blob in (("talk", t), ("orig", o)):
            tags = classify(blob)
            if "HERMES_全段" in tags:
                stats["hermes_full"].append(si)
            if "HERMES_尾部" in tags:
                stats["hermes_tail"].append(si)
            if any(x.startswith("广告") for x in tags):
                stats["ad"].append(si)
    summary[ch] = stats
    if stats["hermes_full"] or stats["hermes_tail"] or stats["ad"]:
        detail.append((ch, stats))

print("== 污染分布（按篇）==")
for ch, st in detail:
    print(f"  SW{ch}: 全段Hermes段={st['hermes_full']} 尾部Hermes段={st['hermes_tail']} 广告段={st['ad']}")

full_only = [ch for ch, st in summary.items() if st["hermes_full"] and len(st["hermes_full"]) == st["seg_count"]]
print(f"\n整篇全段 Hermes 的篇（talk 全被占）: {full_only}")

# 广告语实际文本样例
print("\n== 广告句实际形态（去重样例）==")
seen = set()
for f in sorted(VD.glob("segs_suwen*.json")):
    data = json.loads(f.read_text(encoding="utf-8"))
    for s in data:
        for blob in (s.get("talk", ""), s.get("orig", "")):
            for sent in re.split(r"[。！？]", blob):
                if any(k in sent for k in AD_KW) and sent.strip() and sent.strip() not in seen:
                    seen.add(sent.strip())
                    print("  •", sent.strip()[:120])
                    if len(seen) > 20:
                        break
        if len(seen) > 20:
            break
    if len(seen) > 20:
        break
