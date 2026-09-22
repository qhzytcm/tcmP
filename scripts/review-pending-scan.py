# -*- coding: utf-8 -*-
"""待评阅巡检（cron）：扫描全部看板含归档库，找 assignee=textbook-reviewer 且 status=ready 的任务。

必须用 Hermes venv python 运行（Anaconda sqlite3 DLL 打开 kanban.db 会进程级崩溃）：
    $env:PATH = "C:\\Users\\DELL\\AppData\\Local\\hermes\\hermes-agent\\venv\\Scripts;" + $env:PATH
    python scripts\\review-pending-scan.py
勿用 `& $py script.py`（backgrounding 守卫）。
"""
import sqlite3, os, glob, sys, io
from collections import Counter

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

HH_ROOT = r"C:\Users\DELL\AppData\Local\Hermes Agent CN Desktop\data\hermes-home"
BOARDS = os.path.join(HH_ROOT, "kanban", "boards")


def _connect_ro(db):
    """wal 为空/不存在时用 immutable=1（完全不触碰 -wal/-shm 边车）；有内容时退化为 mode=ro。"""
    wal = db + "-wal"
    if not os.path.exists(wal) or os.path.getsize(wal) == 0:
        return sqlite3.connect(f"file:{db}?immutable=1", uri=True)
    return sqlite3.connect(f"file:{db}?mode=ro", uri=True)


def scan():
    dbs = [(os.path.basename(os.path.dirname(p)), p)
           for p in glob.glob(os.path.join(BOARDS, "*", "kanban.db"))]
    dbs += [("_archived/" + os.path.basename(os.path.dirname(p)), p)
            for p in glob.glob(os.path.join(BOARDS, "_archived", "*", "kanban.db"))]

    grand_ready = 0
    hits = []          # (board, row_dict)
    for name, db in sorted(dbs):
        try:
            con = _connect_ro(db)
            cur = con.cursor()
            cols = [r[1] for r in cur.execute("PRAGMA table_info(tasks)")]
            idx = {c: i for i, c in enumerate(cols)}
            rows = list(cur.execute("SELECT * FROM tasks"))
            st = Counter(r[idx["status"]] for r in rows)

            # 全看板的 reviewer 相关卡（任意状态），便于上下文
            rv = [r for r in rows if "reviewer" in str(r[idx["assignee"]] or "")]
            ready = [r for r in rv if str(r[idx["status"]] or "").strip().lower() == "ready"]

            print("=" * 72)
            print(f"### {name}   tasks={len(rows)} | {dict(st)}")
            print(f"    reviewer-any-status={len(rv)} | reviewer-ready={len(ready)}")
            if rv:
                for r in rv:
                    d = {c: r[idx[c]] for c in cols}
                    print(f"      - [{d['status']}] {d['id']} | assignee={d['assignee']} "
                          f"| pri={d.get('priority')} | {d['title'][:80]}")
            for r in ready:
                hits.append((name, {c: r[idx[c]] for c in cols}))
            grand_ready += len(ready)
            con.close()
        except Exception as e:
            print(f"### {name} -- ERROR: {e}")

    print()
    print("=" * 72)
    print(f"===== 合计 reviewer-ready = {grand_ready} =====")
    print("=" * 72)
    for i, (board, d) in enumerate(hits, 1):
        body = (d.get("body") or d.get("description") or "").strip()
        brief = body.replace("\r", "").replace("\n", " / ")[:600]
        print(f"[{i}] BOARD={board} | ID={d['id']} | PRI={d.get('priority')} "
              f"| TENANT={d.get('tenant')}")
        print(f"    TITLE: {d['title']}")
        if brief:
            print(f"    BODY : {brief}")
        print("-" * 72)
    if not hits:
        print("NO_PENDING_REVIEW")


if __name__ == "__main__":
    scan()
