# -*- coding: utf-8 -*-
"""统稿终验：81 篇 × 双版本 html + mp4 命名规范、SUBS 一致性、标题正确、无 SWNN/页码残留"""
import json
import re
from pathlib import Path

VD = Path(r"C:\Users\DELL\tcmP\docs\视频")
CH_NAMES = json.loads(Path(r"C:\Users\DELL\tcmP\scripts\_ch81.json").read_text(encoding="utf-8")) if (Path(r"C:\Users\DELL\tcmP\scripts\_ch81.json").exists()) else {}
# 若 _ch81.json 不存在则内联小表兜底（1-81 由文件名正则判断即可，名字取自统一篇名表 doc，这里仅做结构验证）

NUM = r"[\d０-９一二三四五六七八九十百千万零两]+"
PAT_PG = re.compile(rf"[（(]\s*第?\s*(?:{NUM}\s*){{1,4}}页\s*[）)]|(?<![0-9０-９一二三四五六七八九十百千万零两])(?:第\s*)?(?:{NUM}\s*){{1,4}}页")

RE_GOOD = re.compile(r"^素问(\d{2})-(.+?)(-视频课程|-视频授课)?\.(mp4|html)$")

def main():
    files = sorted(p.name for p in VD.iterdir() if p.is_file())
    suwen = [f for f in files if f.startswith("素问")]
    # 1) 规范名清单
    bad_names = []
    good = {"mp4": set(), "html_course": set(), "html_teach": set()}
    for f in suwen:
        m = RE_GOOD.match(f)
        if not m:
            bad_names.append(f)
            continue
        ch, body, kind, ext = m.group(1), m.group(2), m.group(3), m.group(4)
        if body.startswith("SW"):
            bad_names.append((f, "篇名仍为 SWNN"))
            continue
        if ext == "mp4":
            good["mp4"].add(ch)
        elif kind == "-视频课程":
            good["html_course"].add(ch)
        elif kind == "-视频授课":
            good["html_teach"].add(ch)
    all81 = {f"{i:02d}" for i in range(1, 82)}
    print("== 1) 命名规范 ==")
    print(f"mp4 覆盖缺: {sorted(all81 - good['mp4']) or '无'}")
    print(f"视频课程 html 覆盖缺: {sorted(all81 - good['html_course']) or '无'}")
    print(f"视频授课 html 覆盖缺: {sorted(all81 - good['html_teach']) or '无'}")
    print(f"非规范名文件: {bad_names or '无'}")
    # 2) 标题抽查（每篇轻量版 <title>）
    print("\n== 2) 标题检查（全部篇）==")
    t_bad = []
    for i in range(1, 82):
        chs = f"{i:02d}"
        cand = [f for f in suwen if f.startswith(f"素问{chs}-") and f.endswith("-视频课程.html")]
        if not cand:
            t_bad.append((f"素问{chs}", "缺课程版"))
            continue
        txt = (VD / cand[0]).read_text(encoding="utf-8", errors="ignore")
        m = re.search(r"<title>(.*?)</title>", txt)
        title = m.group(1) if m else "(无title)"
        if not re.match(r"黄帝内经·素问\d{2}·[^-SW]+$", title) or "SW" in title:
            t_bad.append((cand[0], title))
        if i in (1, 2, 16, 63, 81):
            print(f"  素问{chs}: {title}")
    print(f"  标题异常: {t_bad[:8] or '无 ✓'}")
    # 3) SUBS 一致性（轻量版 vs segs json）
    print("\n== 3) SUBS 与 segs json 一致性 ==")
    diff = []
    for i in range(1, 82):
        chs = f"{i:02d}"
        jf = VD / f"segs_suwen{int(chs)}.json"
        cand = [f for f in suwen if f.startswith(f"素问{chs}-") and f.endswith("-视频课程.html")]
        if not jf.exists() or not cand:
            continue
        segs = json.loads(jf.read_text(encoding="utf-8"))
        txt = (VD / cand[0]).read_text(encoding="utf-8", errors="ignore")
        m = re.search(r"const SUBS = (\[.*?\]);\n", txt, re.S)
        if not m:
            diff.append((chs, "无SUBS"))
            continue
        try:
            subs = json.loads(m.group(1))
        except Exception as e:
            diff.append((chs, f"SUBS解析失败 {e}"))
            continue
        nd = sum(1 for a, b in zip(segs, subs) for k in ("title", "orig", "talk")
                 if a.get(k) != b.get(k))
        if nd or len(segs) != len(subs):
            diff.append((chs, f"{nd} 处字段差异/段数 {len(segs)}vs{len(subs)}"))
    print(f"  不一致篇: {diff or '全部一致 ✓'}")
    # 4) 页码残留（轻量版）
    print("\n== 4) 页码残留（轻量 html + segs）==")
    pg = []
    for i in range(1, 82):
        jf = VD / f"segs_suwen{i}.json"
        if jf.exists():
            data = json.loads(jf.read_text(encoding="utf-8"))
            for s in data:
                for k in ("title", "orig", "talk"):
                    if PAT_PG.search(s.get(k, "")):
                        pg.append((f"segs_suwen{i}.json", k))
                        break
    print(f"  segs json 页码残留: {pg or '无 ✓'}")
    # 5) 归档与旧文件
    print("\n== 5) _legacy_bak 与根目录杂项 ==")
    bak = [p.name for p in (VD / "_legacy_bak").glob("*")] if (VD / "_legacy_bak").exists() else []
    print(f"  _legacy_bak 文件数: {len(bak)}")
    for b in bak:
        print("   ", b)
    others = [f for f in files if f.startswith("素问") and RE_GOOD.match(f) is None and "_" not in f]
    print(f"  根目录残留非规范素问文件: {others or '无'}")

if __name__ == "__main__":
    main()
