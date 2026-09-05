# -*- coding: utf-8 -*-
"""素问 01-81 html/mp4 命名统稿 v2：两位零填充 + 中文篇名 + 标题统一 + 旧版归档。

两阶段（内容判定优先，避免误归档现行版）:
  阶段1: 内容为超旧代格式(单引号 SUBS {sec:...}) 的 html -> 一律移入 _legacy_bak/
  阶段2: 剩余文件按名字统一: 已是规范名->跳过; 目标名被占->归档变体; 否则 rename + 内容替换
用法: python unify_naming.py [--apply]
"""
import json
import re
import sys
from pathlib import Path

VD = Path(r"C:\Users\DELL\tcmP\docs\视频")
BAK = VD / "_legacy_bak"

CH_NAMES_81 = {
    1: "上古天真论", 2: "四气调神大论", 3: "生气通天论", 4: "金匮真言论", 5: "阴阳应象大论",
    6: "阴阳离合论", 7: "阴阳别论", 8: "灵兰秘典论", 9: "六节藏象论", 10: "五藏生成篇",
    11: "五藏别论", 12: "异法方宜论", 13: "移精变气论", 14: "汤液醪醴论", 15: "玉版论要",
    16: "诊要经终论", 17: "脉要精微论", 18: "平人气象论", 19: "玉机真藏论", 20: "三部九候论",
    21: "经脉别论", 22: "脏气法时论", 23: "宣明五气", 24: "血气形志", 25: "宝命全形论",
    26: "八正神明论", 27: "离合真邪论", 28: "通评虚实论", 29: "太阴阳明论", 30: "阳明脉解",
    31: "热论", 32: "刺热", 33: "评热病论", 34: "逆调论", 35: "疟论", 36: "刺疟",
    37: "气厥论", 38: "咳论", 39: "举痛论", 40: "腹中论", 41: "刺腰痛", 42: "风论",
    43: "痹论", 44: "痿论", 45: "厥论", 46: "病能论", 47: "奇病论", 48: "大奇论",
    49: "脉解", 50: "刺要论", 51: "刺齐论", 52: "刺禁论", 53: "刺志论", 54: "针解",
    55: "长刺节论", 56: "皮部论", 57: "经络论", 58: "气穴论", 59: "气府论", 60: "骨空论",
    61: "水热穴论", 62: "调经论", 63: "缪刺论", 64: "四时刺逆从论", 65: "标本病传论",
    66: "天元纪大论", 67: "五运行大论", 68: "六微旨大论", 69: "气交变大论", 70: "五常政大论",
    71: "六元正纪大论", 72: "刺法论", 73: "本病论", 74: "至真要大论", 75: "著至教论",
    76: "示从容论", 77: "疏五过论", 78: "徵四失论", 79: "阴阳类论", 80: "方盛衰论",
    81: "解精微论",
}

RE_FN = re.compile(r"^素问0?(\d+)-(.+)\.(mp4|html)$")
RE_SW_NAME = re.compile(r"^SW\d+$")


def is_oldfmt(txt):
    return "sec: '第" in txt or 'sec: "第' in txt or "{ sec:" in txt


def read_head(path, n=6000):
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as fh:
            return fh.read(n)
    except Exception:
        return ""


def read_small(path):
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def parse(fname):
    m = RE_FN.match(fname)
    if not m:
        return None
    ch = int(m.group(1))
    body = m.group(2)
    ext = m.group(3)
    kind = ""
    if ext == "html":
        if body.endswith("-视频课程"):
            kind = "-视频课程"
            body = body[: -len(kind)]
        elif body.endswith("-视频授课"):
            kind = "-视频授课"
            body = body[: -len(kind)]
    return {"ch": ch, "body": body, "ext": ext, "kind": kind}


def main():
    apply = "--apply" in sys.argv
    files = sorted(VD.glob("素问*.mp4")) + sorted(VD.glob("素问*.html"))
    infos = []
    for f in files:
        p = parse(f.name)
        if not p:
            continue
        p["path"] = f
        infos.append(p)
    # 轻量版(-视频课程.html)全读判旧格式
    oldfmt_light = set()
    for p in infos:
        if p["ext"] == "html" and p["kind"] == "-视频课程":
            if is_oldfmt(read_small(p["path"])):
                oldfmt_light.add(p["path"].name)
    # 阶段1: 超旧代 = 自身 oldfmt 的轻量版 + 同 body 前缀的授课版
    stage1 = []
    for p in infos:
        if p["ext"] != "html":
            continue
        if p["kind"] == "-视频课程" and p["path"].name in oldfmt_light:
            stage1.append(p)
        elif p["kind"] == "-视频授课":
            twin = p["path"].name.replace("-视频授课", "-视频课程")
            if twin in oldfmt_light:
                stage1.append(p)
    stage1_names = {p["path"].name for p in stage1}
    # 阶段2: 其余
    renames, dup_legacy, skips = [], [], []
    for p in infos:
        if p["path"].name in stage1_names:
            continue
        name_new = CH_NAMES_81.get(p["ch"])
        new_name = f"素问{p['ch']:02d}-{name_new}{p['kind']}.{p['ext']}"
        if p["path"].name == new_name:
            skips.append((p["path"].name, "已是规范名"))
            continue
        # SW 变体（如 -SW1-）：仅当同 ch 已存在中文 body 版本时才归档，否则照常 rename
        if re.match(r"^SW\d+$", p["body"]):
            has_cn = any(q["ch"] == p["ch"] and q["ext"] == p["ext"]
                         and q["kind"] == p["kind"] and not re.match(r"^SW\d+$", q["body"])
                         and q["path"].name not in stage1_names
                         for q in infos)
            if has_cn:
                dup_legacy.append((p["path"].name, new_name, "SW编号变体(同篇有中文名版)"))
                continue
        if (VD / new_name).exists() and new_name not in stage1_names:
            dup_legacy.append((p["path"].name, new_name, "重复变体(目标已存在)"))
            continue
        renames.append((p["path"], new_name))

    mode = "APPLY" if apply else "DRY-RUN"
    print(f"[{mode}] 超旧代归档 {len(stage1)} | 重复变体归档 {len(dup_legacy)} | rename {len(renames)} | 跳过 {len(skips)}")
    for p in stage1:
        print(f"  归档(超旧代): {p['path'].name}")
    for old, new, why in dup_legacy:
        print(f"  归档(重复): {old}  ({why})")
    for f, new in renames:
        print(f"  改名: {f.name} → {new}")
    for old, why in skips:
        print(f"  跳过: {old}  ({why})")

    if not apply:
        print("\n(未写盘; 加 --apply 执行)")
        return

    BAK.mkdir(exist_ok=True)
    manifest = []
    # 先归档（腾出规范名）
    for p in stage1:
        src = p["path"]
        dst = BAK / src.name
        if dst.exists():
            dst = BAK / (src.stem + "_dup" + src.suffix)
        src.rename(dst)
        manifest.append({"old": src.name, "new": str(dst.relative_to(VD)), "why": "超旧代格式"})
    for old, new, why in dup_legacy:
        src = VD / old
        src.rename(BAK / old)
        manifest.append({"old": old, "new": f"_legacy_bak/{old}", "why": why})
    # 再 rename + 内容替换
    for f, new_name in renames:
        txt = None
        if f.suffix == ".html":
            txt = f.read_text(encoding="utf-8", errors="ignore")
            m = RE_FN.match(new_name)
            ch = int(m.group(1))
            name_new = CH_NAMES_81[ch]
            p = parse(f.name)
            old_body = p["body"]
            old_title_pat = re.compile(
                rf"黄帝内经·素问0?{p['ch']}·{re.escape(old_body)}")
            new_title = f"黄帝内经·素问{ch:02d}·{name_new}"
            txt2 = old_title_pat.sub(new_title, txt)
            old_mp4 = re.compile(rf"素问0?{p['ch']}-{re.escape(old_body)}\.mp4")
            new_mp4 = f"素问{ch:02d}-{name_new}.mp4"
            txt2 = old_mp4.sub(new_mp4, txt2)
            if txt2 != txt:
                f.write_text(txt2, encoding="utf-8")
        f.rename(VD / new_name)
        manifest.append({"old": f.name, "new": new_name, "why": "命名统稿"})
    (VD / "_unify_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"完成, 操作清单 → docs/视频/_unify_manifest.json ({len(manifest)} 项)")


if __name__ == "__main__":
    main()
