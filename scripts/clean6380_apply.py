# -*- coding: utf-8 -*-
"""清理 SW63-81 页码（json + html 片段同步），仅处理命中篇"""
import json
import sys
from pathlib import Path

sys.path.insert(0, r"C:\Users\DELL\tcmP\scripts")
from clean_pagenum2 import clean_text, has_pat

VD = Path(r"C:\Users\DELL\tcmP\docs\视频")
report = []
for i in range(63, 82):
    jf = VD / f"segs_suwen{i}.json"
    data = json.loads(jf.read_text(encoding="utf-8"))
    pairs = []
    for s in data:
        for k in ("title", "orig", "talk"):
            v = s.get(k, "")
            if has_pat(v):
                new = clean_text(v)
                if new != v:
                    s[k] = new
                    pairs.append((v, new))
    if not pairs:
        continue
    jf.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    # html 双版本片段同步
    for f in sorted(VD.glob(f"素问{i:02d}-*.html")):
        txt = f.read_text(encoding="utf-8", errors="ignore")
        orig = txt
        for raw_old, raw_new in pairs:
            txt = txt.replace(raw_old, raw_new)
            j_old = json.dumps(raw_old, ensure_ascii=False)[1:-1]
            j_new = json.dumps(raw_new, ensure_ascii=False)[1:-1]
            txt = txt.replace(j_old, j_new)
        if txt != orig:
            f.write_text(txt, encoding="utf-8")
    report.append((i, len(pairs)))
print("清理完成:", report)
