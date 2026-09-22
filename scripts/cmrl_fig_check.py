# -*- coding: utf-8 -*-
"""cmrl_fig_check.py — 全书图表一致性终检（任务 5/6 收口）

检查:
  A. 每章 4 幅 PNG 存在且非空（figures/chNN/figN-*.png）
  B. 正文图块三段式结构: 每图【图题(**图 N-X **) → 图体(![图)(PNG) → 图注(图注:)】齐全
  C. 图体引用文件名与实际 PNG 一一对应
  D. check 脚本回归: 每章 check_chNN.py 退出码 0（图块排除后 48 段不变）
"""
import subprocess
import sys
from pathlib import Path

DRAFTS = Path(r'C:\Users\DELL\textbook-project\drafts\cmrl')
FIGDIR = DRAFTS / 'figures'
sys.path.insert(0, str(Path(__file__).parent))
from cmrl_merge import CHAP_META  # noqa: E402

results = []


def check(name, ok, detail=''):
    results.append((name, ok, detail))
    print(f'{"PASS" if ok else "FAIL"}  {name}  {detail}')


# A. PNG 存在非空
png_ok = True
total_png = 0
for ch in range(1, 11):
    d = FIGDIR / f'ch{ch:02d}'
    pngs = sorted(d.glob('fig*.png')) if d.exists() else []
    total_png += len(pngs)
    if len(pngs) < 4 or any(p.stat().st_size < 1024 for p in pngs):
        png_ok = False
        print(f'  [MISS] ch{ch:02d} PNG: {len(pngs)} 幅')
check(f'A. 每章 ≥4 幅 PNG 非空（共 {total_png} 幅）', png_ok, '')

# B/C. 正文图块三段式 + 引用对应
struct_ok = True
for ch in range(1, 11):
    prefix, sheet, title = CHAP_META[ch]
    d = DRAFTS / f'ch{ch:02d}'
    for f in sorted(d.glob('*.md')):
        if f.name.startswith('chapter-'):
            continue
        text = f.read_text(encoding='utf-8')
        lines = text.splitlines()
        for i, ln in enumerate(lines):
            if ln.strip().startswith('**图 '):          # 图题
                cap = ln.strip()
                # 向下找下一个非空行=图体, 再下一个非空行=图注（允许空行间隔）
                j = i + 1
                while j < len(lines) and not lines[j].strip():
                    j += 1
                body_ok = j < len(lines) and lines[j].strip().startswith('![')
                k = j + 1
                while k < len(lines) and not lines[k].strip():
                    k += 1
                note_ok = k < len(lines) and lines[k].strip().startswith('图注：')
                # 图体引用与 PNG 对应
                ref_ok = False
                if body_ok:
                    import re
                    m = re.search(r'\]\(figures/ch\d+/(fig\d+-\d+\.png)\)', lines[j])
                    if m:
                        ref_ok = (FIGDIR / f'ch{ch:02d}' / m.group(1)).exists()
                if not (body_ok and note_ok and ref_ok):
                    struct_ok = False
                    print(f'  [BAD] {f.name} L{i+1}: 图题={cap[:20]} 体={body_ok} 注={note_ok} 引用={ref_ok}')
check('B/C. 正文图题-图体-图注三段 + 引用对应', struct_ok, '')

# D. check 脚本回归
reg_ok = True
for ch in range(1, 11):
    d = DRAFTS / f'ch{ch:02d}'
    script = d / f'check_ch{ch:02d}.py'
    if not script.exists():
        reg_ok = False
        print(f'  [MISS] ch{ch:02d} check 脚本不存在')
        continue
    r = subprocess.run([sys.executable, str(script)], cwd=str(d),
                       capture_output=True, text=True, encoding='utf-8', timeout=120)
    if r.returncode != 0:
        reg_ok = False
        print(f'  [FAIL] ch{ch:02d} check 退出码 {r.returncode}')
check('D. 10 章 check 脚本回归退出码 0', reg_ok, '')

fails = [r for r in results if not r[1]]
print(f'\n===== 全书图表一致性终检: {"通过" if not fails else "未通过"} '
      f'({len(results)-len(fails)}/{len(results)}) =====')
sys.exit(0 if not fails else 1)
