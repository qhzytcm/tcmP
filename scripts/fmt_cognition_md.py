# -*- coding: utf-8 -*-
"""0认知特色.txt → 素问30-夷陵君认知特色提炼.md（tab 转 markdown 分节）"""
from pathlib import Path

src = Path(r"C:\Users\DELL\tcmP\scripts\_wyshan_text\0认知特色.txt")
out = Path(r"C:\Users\DELL\tcmP\docs\视频\素问30-夷陵君认知特色提炼.md")
lines = [l for l in src.read_text(encoding="utf-8").splitlines() if l.strip()]
parts = []
for l in lines:
    if "\t" in l:
        k, v = l.split("\t", 1)
    else:
        k, v = "", l
    k = k.strip()
    v = v.strip()
    if not v:
        continue
    if k in ("总论", "结语"):
        parts.append(f"\n## {k}\n\n{v}\n")
    elif k.startswith(("一、", "二、", "三、", "四、")):
        parts.append(f"\n## {k}\n")
    elif k and not k[0].isdigit():
        parts.append(f"\n### {k}\n\n{v}\n")
    else:
        # 数字条目等
        head = f"**{k}** " if k else ""
        parts.append(f"- {head}{v}\n")
out.write_text("\n".join(parts), encoding="utf-8")
print(f"写入 {out} ({out.stat().st_size} 字节)")
