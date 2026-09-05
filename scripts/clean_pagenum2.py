# -*- coding: utf-8 -*-
"""清理素问课件中的单一教材页码标注（片段级精准替换，避免大 html 全文正则）。

流程:
  1) 清理 segs_suwen*.json 的 title/orig/talk（去页码 token），记录 (old→new) 片段对
  2) 对受污染篇的 -视频课程.html / -视频授课.html 做片段 replace：
       raw 片段命中正文区；json.dumps 转义片段命中 <script>SUBS</script> 区
用法: python clean_pagenum2.py            # dry-run 打印计划
      python clean_pagenum2.py --apply    # 写盘
"""
import json
import re
import sys
from pathlib import Path

VD = Path(r"C:\Users\DELL\tcmP\docs\视频")
NUM = r"[\d０-９一二三四五六七八九十百千万零两]+"
PAT_BRACE = re.compile(rf"[（(]\s*第?\s*(?:{NUM}\s*){{1,4}}页\s*[）)]")
PAT_RAW = re.compile(rf"(?<![0-9０-９一二三四五六七八九十百千万零两])(?:第\s*)?(?:{NUM}\s*){{1,4}}页")

def clean_text(t):
    t = PAT_BRACE.sub("", t)
    t = PAT_RAW.sub("", t)
    # 清理删除后产生的多余空格/标点粘连
    t = re.sub(r" {2,}", " ", t)
    t = re.sub(r"(?<=[。，、；：！？）》】…]) +", "", t)
    t = re.sub(r" ·+ ", " · ", t)
    return t.strip()

def has_pat(t):
    return PAT_BRACE.search(t) is not None or PAT_RAW.search(t) is not None

def main():
    apply = "--apply" in sys.argv
    pairs_by_ch = {}   # ch -> list of (raw_old, raw_new, json_old, json_new)
    touched_json = []
    for f in sorted(VD.glob("segs_suwen*.json")):
        ch = f.name.replace("segs_suwen", "").replace(".json", "")
        data = json.loads(f.read_text(encoding="utf-8"))
        pairs = []
        for s in data:
            for k in ("title", "orig", "talk"):
                if k in s and has_pat(s[k]):
                    old = s[k]
                    new = clean_text(old)
                    if new != old:
                        s[k] = new
                        pairs.append((old, new))
        if pairs:
            touched_json.append((ch, f.name, len(pairs)))
            pairs_by_ch[ch] = pairs
            if apply:
                f.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")

    # html 处理: 命中篇的两种版本
    html_touched = []
    for ch, pairs in pairs_by_ch.items():
        # 匹配该篇 html：素问{ch}- 或 素问0{ch}-（前导零），或中文篇名/SW 名同文件
        cands = []
        for f in sorted(VD.glob("素问*.html")):
            # 从文件名提取篇号
            m = re.match(r"素问0?(\d+)-", f.name)
            if m and m.group(1) == ch:
                cands.append(f)
        for f in cands:
            if not apply:
                html_touched.append(f.name)
                continue
            txt = f.read_text(encoding="utf-8", errors="ignore")
            for raw_old, raw_new in pairs:
                # 正文区（原始文本）
                txt = txt.replace(raw_old, raw_new)
                # SUBS JSON 区（json 转义文本）
                j_old = json.dumps(raw_old, ensure_ascii=False)[1:-1]
                j_new = json.dumps(raw_new, ensure_ascii=False)[1:-1]
                txt = txt.replace(j_old, j_new)
            f.write_text(txt, encoding="utf-8")
            html_touched.append(f.name)

    mode = "APPLIED" if apply else "DRY-RUN"
    print(f"[{mode}] 受污染 segs json: {len(touched_json)} 个")
    for ch, fname, n in touched_json:
        print(f"  json  {fname}  ({n} 处字段)")
    print(f"[{mode}] 受污染 html: {len(html_touched)} 个")
    for h in html_touched:
        print("  html ", h)

if __name__ == "__main__":
    main()
