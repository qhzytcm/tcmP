# -*- coding: utf-8 -*-
"""内容洁净度验证 v2：
1) 括注型页码残留（（第X页）格式）—— 真格式残留，报
   （裸口语书页引用如"516页中间那一行"为倪师讲课原话，属内容，不报）
2) Hermes独立理解 显式污染
3) Hermes 元叙述风格残留（通读倪师/以系统科学视角/重审 等 AI 腔）—— v2 新增
4) 广告句（人纪求真/应用商店推广语）—— v2 新增
"""
import json
import re
from pathlib import Path

VD = Path(r"C:\Users\DELL\tcmP\docs\视频")
NUM = r"[\d０-９一二三四五六七八九十百千万零两]+"
# 括注型页码（格式残留）：（第X页）/(X页) 等括号包裹形态
PAT_BRACE = re.compile(rf"[（(]\s*第?\s*(?:{NUM}\s*){{1,4}}页\s*[）)]")
# Hermes 显式污染
HERMES = re.compile(r"Hermes独立理解|独立理解《")
# Hermes 元叙述风格（AI 腔，无显式标记但读起来是分析报告）
META = re.compile(r"通读倪师[白话讲解]*并对照|以系统科学视角[重审]*|重审如下|为 AI 类比推理诊断引擎")
# 广告句
AD = re.compile(r"搜索人[纪际]求真下载使用吧|快到手机应用商店搜索人纪求真下载使用吧|视频一听就懂|告别学了后面忘|快速梳理知识框架|让零散的知识点一目了然|人纪求真下载")


def has_brace_pat(t):
    return PAT_BRACE.search(t) is not None


print("== 1) 括注型页码残留（格式）==")
bad_json = []
for f in sorted(VD.glob("segs_suwen*.json")):
    data = json.loads(f.read_text(encoding="utf-8"))
    for si, s in enumerate(data, 1):
        for k in ("title", "orig", "talk"):
            if has_brace_pat(s.get(k, "")):
                bad_json.append((f.name, si, k))
print(f"segs json 括注页码残留: {len(bad_json)}")
for b in bad_json[:10]:
    print("  ", b)

bad_html = []
for f in sorted(VD.glob("*-视频课程.html")):
    txt = f.read_text(encoding="utf-8", errors="ignore")
    if has_brace_pat(txt):
        bad_html.append(f.name)
print(f"轻量 html 括注页码残留: {len(bad_html)}")
for b in bad_html[:10]:
    print("  ", b)

print("\n== 2) Hermes独立理解 显式污染 ==")
bad_hermes = []
for f in sorted(VD.glob("segs_suwen*.json")):
    data = json.loads(f.read_text(encoding="utf-8"))
    for si, s in enumerate(data, 1):
        for k in ("title", "orig", "talk"):
            v = s.get(k, "")
            if HERMES.search(v):
                bad_hermes.append((f.name, si, k, len(v), v[:80]))
print(f"Hermes显式污染条目: {len(bad_hermes)}")
for b in bad_hermes:
    print(f"  {b[0]} seg{b[1]}.{b[2]} len={b[3]}: {b[4]!r}")

print("\n== 3) Hermes 元叙述风格残留（AI 腔）==")
bad_meta = []
for f in sorted(VD.glob("segs_suwen*.json")):
    data = json.loads(f.read_text(encoding="utf-8"))
    for si, s in enumerate(data, 1):
        for k in ("title", "orig", "talk"):
            v = s.get(k, "")
            m = META.search(v)
            if m:
                bad_meta.append((f.name, si, k, m.group(0)))
print(f"元叙述风格条目: {len(bad_meta)}")
for b in bad_meta[:20]:
    print("  ", b)

print("\n== 4) 广告句 ==")
bad_ad = []
for f in sorted(VD.glob("segs_suwen*.json")):
    data = json.loads(f.read_text(encoding="utf-8"))
    for si, s in enumerate(data, 1):
        for k in ("title", "orig", "talk"):
            v = s.get(k, "")
            m = AD.search(v)
            if m:
                bad_ad.append((f.name, si, k, m.group(0)))
print(f"广告句条目: {len(bad_ad)}")
for b in bad_ad[:20]:
    print("  ", b)
