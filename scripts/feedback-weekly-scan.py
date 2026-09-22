# -*- coding: utf-8 -*-
"""
反馈周报采集工具（canonical, 2026-09-14 起复用）

用途：textbook-user 周报 cron 的供给侧数据采集——扫描 feedback/reviews/drafts 目录 +
全 12 个 Kanban 看板（含 _archived 归档库）+ Git 状态，输出可直接写进周报的统计。

⚠️ 必须用 Hermes venv python 运行（Anaconda 的 sqlite3 DLL 打开 kanban.db 会进程级崩溃）：
    $env:PATH = "C:\\Users\\DELL\\AppData\\Local\\hermes\\hermes-agent\\venv\\Scripts;" + $env:PATH
    python scripts\\feedback-weekly-scan.py
  勿用 `& $py script.py`（触发 backgrounding 守卫）。

⚠️ 关键背景：textbook 看板已归档重建（_archived/textbook-1788857952/），
   当前 textbook 板为 0 卡空白板 —— 统计「终态」必须读归档库，否则会把闭环误报为清零。
"""
import sqlite3, os, glob, sys, io
from collections import Counter

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

HH_ROOT = r"C:\Users\DELL\AppData\Local\Hermes Agent CN Desktop\data\hermes-home"
PROJ = r"C:\Users\DELL\textbook-project"
BOARDS = os.path.join(HH_ROOT, "kanban", "boards")

# 报告周期起点（本周新增判定阈值，每次运行按需修改）
CUT = sys.argv[1] if len(sys.argv) > 1 else "2026-09-08"


def dir_stats():
    print("=" * 70)
    print(f"目录统计（项目: {PROJ}）")
    print("=" * 70)
    for d in ("drafts", "reviews", "feedback", "archive", "scripts"):
        p = os.path.join(PROJ, d)
        files = [os.path.join(r, f) for r, _, fs in os.walk(p) for f in fs]
        if not files:
            print(f"  {d:<10} files=0")
            continue
        latest = max(files, key=os.path.getmtime)
        n_new = sum(1 for f in files if os.path.getmtime(f) >= _cut_epoch())
        print(f"  {d:<10} files={len(files):<6} new_since_{CUT}={n_new:<4} "
              f"latest={os.path.basename(latest)}")
    # feedback 明细
    fb = sorted(os.path.basename(f) for f in glob.glob(os.path.join(PROJ, "feedback", "*")))
    print(f"\n  feedback/ 明细: {fb}")


def _cut_epoch():
    from datetime import datetime
    return datetime.strptime(CUT, "%Y-%m-%d").timestamp()


def _connect_ro(db):
    """归档库只读打开。wal 为空/不存在时用 immutable=1 —— 完全不触碰 -wal/-shm 边车，
    使每周「本周是否有变更」的差分判断不被自身读取动作污染；wal 有内容时退化为 mode=ro
    以保证读到未 checkpoint 的最新事务。"""
    wal = db + "-wal"
    if not os.path.exists(wal) or os.path.getsize(wal) == 0:
        return sqlite3.connect(f"file:{db}?immutable=1", uri=True)
    return sqlite3.connect(f"file:{db}?mode=ro", uri=True)


def board_stats():
    print()
    print("=" * 70)
    print(f"看板全量扫描（含归档）  本周阈值 >= {CUT}")
    print("=" * 70)
    dbs = [(os.path.basename(os.path.dirname(p)), p)
           for p in glob.glob(os.path.join(BOARDS, "*", "kanban.db"))]
    dbs += [("_archived/" + os.path.basename(os.path.dirname(p)), p)
            for p in glob.glob(os.path.join(BOARDS, "_archived", "*", "kanban.db"))]

    g_new, g_ev = 0, 0
    for name, db in sorted(dbs):
        try:
            con = _connect_ro(db)
            cur = con.cursor()
            cols = [r[1] for r in cur.execute("PRAGMA table_info(tasks)")]
            idx = {c: i for i, c in enumerate(cols)}
            rows = list(cur.execute("SELECT * FROM tasks"))
            st = Counter(r[idx["status"]] for r in rows)
            # created_at 存的是 epoch 秒
            new_rows = [r for r in rows if str(r[idx["created_at"]] or "").isdigit()
                        and int(r[idx["created_at"]]) >= _cut_epoch()]
            try:
                ev_new = cur.execute("SELECT COUNT(*) FROM task_events WHERE created_at >= ?",
                                     (int(_cut_epoch()),)).fetchone()[0]
            except Exception:
                ev_new = -1
            print(f"\n### {name}")
            print(f"    tasks={len(rows)} | {dict(st)}")
            print(f"    created_since_{CUT}={len(new_rows)} | events_since={ev_new}")
            for r in new_rows:
                print(f"       NEW: [{r[idx['status']]}] {r[idx['title']][:70]}")
            # 反馈类卡片
            fb = [r for r in rows if "反馈" in str(r[idx["title"]])]
            if fb:
                print(f"    feedback-cards={len(fb)}:")
                for r in fb:
                    print(f"       [{r[idx['status']]}] {r[idx['id']]} | {r[idx['title']]}"
                          f" | assignee={r[idx['assignee']]}")
            # blocked
            bl = [r for r in rows if r[idx["status"]] == "blocked"]
            if bl:
                print(f"    blocked={len(bl)}: " + "; ".join(r[idx["title"]][:40] for r in bl))
            g_new += len(new_rows)
            g_ev += ev_new
            con.close()
        except Exception as e:
            print(f"\n### {name} -- ERROR: {e}")
    print(f"\n===== 全项目合计: new_tasks_since_{CUT}={g_new} | new_events={g_ev} =====")


def archive_registry():
    """列出归档看板及其 epoch 解码时间（解码用 PowerShell，此处只列目录名）。"""
    print()
    print("=" * 70)
    print("归档看板登记表")
    print("=" * 70)
    for p in sorted(glob.glob(os.path.join(BOARDS, "_archived", "*"))):
        if os.path.isdir(p):
            print(f"  {os.path.basename(p)}  (mtime={os.path.getmtime(p)})")
    print("  解码： [DateTimeOffset]::FromUnixTimeSeconds(<epoch>).ToLocalTime()")


if __name__ == "__main__":
    dir_stats()
    board_stats()
    archive_registry()
    print("\n提示：Git 状态请另用 git status --porcelain 统计（本脚本不调用 git）。")
