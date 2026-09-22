# -*- coding: utf-8 -*-
"""周报统计脚本：读 kanban_tmp.json + 目录扫描 + git 状态，输出周报所需全部数字。"""
import json, os, subprocess, sys
from pathlib import Path
from collections import Counter, defaultdict

ROOT = Path(r"C:\Users\DELL\textbook-project")
SINCE = "2026-08-15"  # 上周报告日，本周周期 = 08-15 ~ 08-21

def parse_date(ts):
    # ts 形如 2026-08-21 12:34:56 或含毫秒
    return str(ts)[:10]

print("=" * 60)
print("【一】Kanban 看板统计（kanban_tmp.json）")
print("=" * 60)
cards = []
with open(ROOT / "kanban_tmp.json", encoding="utf-16") as f:
    cards = json.load(f)
print(f"卡片总数: {len(cards)}")
status_cnt = Counter(c.get("status", "?") for c in cards)
for s, n in sorted(status_cnt.items(), key=lambda x: -x[1]):
    print(f"  {s}: {n}")
# 看板名分布
board_cnt = Counter(c.get("board", c.get("board_slug", "?")) for c in cards)
print("按看板分布:", dict(board_cnt))
# blocked 卡片详情
print("\n-- blocked 卡片 --")
for c in cards:
    if c.get("status") == "blocked":
        print(f"  {c.get('id','?')} | {c.get('title','?')}")
# done 卡片
print("\n-- done 卡片 --")
for c in cards:
    if c.get("status") == "done":
        print(f"  {c.get('id','?')} | {c.get('title','?')}")

print()
print("=" * 60)
print("【二】目录文件统计（drafts/reviews/feedback/archive 等）")
print("=" * 60)
def count_files(p: Path, skip_dirs=()):
    n = 0
    recent = 0
    for root, dirs, files in os.walk(p):
        dirs[:] = [d for d in dirs if d not in skip_dirs and not d.startswith("_")]
        for fn in files:
            fp = Path(root) / fn
            if ".git" in fp.parts or "__pycache__" in fp.parts:
                continue
            n += 1
            try:
                mtime = os.path.getmtime(fp)
            except OSError:
                continue
            import datetime
            if datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d") >= SINCE:
                recent += 1
    return n, recent

for d in ["drafts", "reviews", "feedback", "archive", "domain-specs", "kg-schema",
          "ai-curriculum", "scripts", "assets", "dashboard", "sage-personas",
          "sage-api", "mobile-app", "chapter-templates", ".github/workflows"]:
    p = ROOT / d
    if p.exists():
        total, recent = count_files(p)
        print(f"  {d}/: {total} 文件 | 本周(>={SINCE})变更 {recent}")
    else:
        print(f"  {d}/: (不存在)")

print()
print("=" * 60)
print("【三】drafts/ 章节草稿（md，排除 figures/scripts/bak）")
print("=" * 60)
md_cnt = 0
recent_md = 0
recent_files = []
import datetime
for root, dirs, files in os.walk(ROOT / "drafts"):
    dirs[:] = [d for d in dirs if d not in ("figures", "__pycache__") and not d.startswith("_")]
    for fn in files:
        if fn.endswith(".md"):
            fp = Path(root) / fn
            md_cnt += 1
            mtime = datetime.datetime.fromtimestamp(os.path.getmtime(fp)).strftime("%Y-%m-%d")
            if mtime >= SINCE:
                recent_md += 1
                recent_files.append(f"{fp.relative_to(ROOT)} ({mtime})")
print(f"drafts/ 章节草稿 md 总数: {md_cnt} | 本周修改: {recent_md}")
print("-- 本周修改的 md（前 40）--")
for rf in recent_files[:40]:
    print(f"  {rf}")
if len(recent_files) > 40:
    print(f"  ... 共 {len(recent_files)} 个")

print()
print("=" * 60)
print("【四】reviews/ 与 feedback/ 明细")
print("=" * 60)
print("reviews/ 文件:")
rev = list((ROOT / "reviews").glob("**/*")) if (ROOT / "reviews").exists() else []
rev_files = [r for r in rev if r.is_file()]
print(f"  {len(rev_files)} 个文件")
for r in rev_files:
    print(f"  {r.relative_to(ROOT)}")
print("feedback/ 文件:")
fb = [r for r in (ROOT / "feedback").glob("**/*") if r.is_file()]
for r in sorted(fb):
    print(f"  {r.relative_to(ROOT)}")

print()
print("=" * 60)
print("【五】Git 状态")
print("=" * 60)
r = subprocess.run(["git", "log", f"--since={SINCE}", "--pretty=format:%h|%ad|%s", "--date=short"],
                   cwd=ROOT, capture_output=True, text=True)
commits = [l for l in r.stdout.strip().splitlines() if l]
print(f"本周提交数（>= {SINCE}）: {len(commits)}")
for c in commits:
    print(f"  {c}")
r2 = subprocess.run(["git", "status", "--short"], cwd=ROOT, capture_output=True, text=True)
lines = [l for l in r2.stdout.splitlines() if l.strip()]
print(f"未提交变更条目: {len(lines)}")
# 按类型统计
tcnt = Counter(l[:2].strip() for l in lines)
print("按状态:", dict(tcnt))
# 未提交文件涉及目录
dirs = Counter()
for l in lines:
    parts = l[3:].split("/")
    if parts:
        dirs[parts[0] + ("/" + parts[1] if len(parts) > 1 else "")] += 1
print("未提交变更目录分布:", dict(dirs.most_common(15)))
# 最近未提交文件（时间排序前 30）
import time
untracked_mod = []
for l in lines:
    path = l[3:].strip().strip('"')
    fp = ROOT / path
    if fp.exists() and fp.is_file():
        mt = os.path.getmtime(fp)
        untracked_mod.append((datetime.datetime.fromtimestamp(mt).strftime("%m-%d %H:%M"), path))
untracked_mod.sort(reverse=True)
print("-- 最近修改的未提交文件（前 25）--")
for t, p in untracked_mod[:25]:
    print(f"  {t} | {p}")

print()
print("=" * 60)
print("【六】archive 周报基线")
print("=" * 60)
archives = sorted([r.name for r in (ROOT / "archive").glob("weekly-progress-*.md")])
print("已有周报:", archives)
