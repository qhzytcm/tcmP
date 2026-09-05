# -*- coding: utf-8 -*-
"""全量污染分类：81 篇 segs json + html，输出每篇类型与可修复性。
类型: CLEAN(无污染) / TAIL(前段正常+尾部Hermes/广告,可截断) / FULL(整段Hermes占位,需重生成) / AD(广告句)
"""
import json
import re
from pathlib import Path

VD = Path(r"C:\Users\DELL\tcmP\docs\视频")
HERMES_RE = re.compile(r"Hermes独立理解《[^》]*》[:：]")
AD_KWS = ["搜索人纪求真", "搜索人际求真", "人纪求真下载", "应用商店搜索", "视频一听就懂",
          "告别学了后面忘", "快速梳理知识框架", "手机应用商店", "人纪求真"]
# 尾部追加标记（Hermes 段前面是正常讲解时，段内还会以 （追加内容） 出现）
TAIL_MARK = re.compile(r"Hermes独立理解《[^》]*》\s*[（(]追加内容[）)]")


def has_ad(t):
    return any(k in t for k in AD_KWS)


def classify_seg(s):
    talk = s.get("talk") or ""
    tags = []
    m = HERMES_RE.search(talk)
    if m:
        prefix = talk[:m.start()].strip()
        if len(prefix) < 10:
            tags.append("FULL")          # 整段 Hermes 占位，无正常讲解前缀
        else:
            tags.append("TAIL")          # 正常讲解 + Hermes 尾段
    elif TAIL_MARK.search(talk):
        tags.append("TAIL")
    if has_ad(talk):
        tags.append("AD")
    if not tags:
        return "CLEAN"
    if "FULL" in tags:
        return "FULL"
    if "TAIL" in tags and "AD" not in tags:
        return "TAIL"
    return "MIX"  # TAIL+AD 或仅 AD


def main():
    stat = {}
    rows = []
    for f in sorted(VD.glob("segs_suwen*.json")):
        ch = f.name.replace("segs_suwen", "").replace(".json", "")
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except Exception as e:
            rows.append((ch, "ERR", str(e)))
            continue
        seg_types = [classify_seg(s) for s in data]
        uniq = set(seg_types)
        if "FULL" in uniq:
            typ = "FULL"
        elif "MIX" in uniq:
            typ = "MIX"
        elif "TAIL" in uniq:
            typ = "TAIL"
        elif "AD" in uniq:
            typ = "AD"
        else:
            typ = "CLEAN"
        stat[typ] = stat.get(typ, 0) + 1
        rows.append((ch, typ, len(data), seg_types.count("FULL"), seg_types.count("TAIL"), seg_types.count("AD")))

    print("=== 篇级类型统计 ===")
    for k in ["CLEAN", "TAIL", "MIX", "AD", "FULL", "ERR"]:
        print(f"  {k}: {stat.get(k, 0)}")
    print("\n=== 明细 (篇,类型,段数,full段,tail段,ad段) ===")
    for r in rows:
        print("  %-4s %-6s seg=%d full=%d tail=%d ad=%d" % r)

    # 汇总可自动修 vs 需重生成
    auto_fix = [r[0] for r in rows if r[1] in ("TAIL", "MIX", "AD")]
    regen = [r[0] for r in rows if r[1] == "FULL"]
    print(f"\n可自动截断修复: {len(auto_fix)} 篇 -> {auto_fix}")
    print(f"需整篇重生成:   {len(regen)} 篇 -> {regen}")


if __name__ == "__main__":
    main()
