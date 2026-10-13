# -*- coding: utf-8 -*-
"""阶段三/四/五 批量驱动：中医诊断学(14) → 方剂学(24) → 中药学(30) 全量生成 + 主前端部署。

幂等：textbook_course_pipeline 对已存在的 wav 跳过，可安全重跑/续跑。
用法（后台）：
  python scripts/batch_books.py
日志：仓库根 _batch345.log（未跟踪，可删）
"""
from __future__ import annotations
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PY = sys.executable
BOOKS = [
    ("中医诊断学.xlsx", "zhenduan", "中医诊断学"),
    ("方剂学.xlsx", "fangji", "方剂学"),
    ("中药学.xlsx", "zhongyao", "中药学"),
]
LOG = REPO / "_batch345.log"


def log(m: str) -> None:
    line = f"[{time.strftime('%m-%d %H:%M:%S')}] {m}"
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def main() -> None:
    log("=== 阶段三/四/五 批量开始 ===")
    for fname, slug, name in BOOKS:
        log(f"--- {name} ({slug}) 生成中 ---")
        r = subprocess.run([PY, str(REPO / "scripts" / "textbook_course_pipeline.py"),
                            "--book", str(REPO / "data" / "textbooks-released" / fname),
                            "--slug", slug, "--name", name, "--all"], cwd=str(REPO))
        if r.returncode != 0:
            log(f"!! {name} 生成 rc={r.returncode}（跳过部署，可重跑续跑）")
            continue
        log(f"{name} 生成完成 rc=0 → 部署主前端")
        d = subprocess.run([PY, str(REPO / "scripts" / "deploy_course_to_frontends.py"),
                            "--slug", slug,
                            "--local", str(REPO / "docs" / "教材视频" / slug),
                            "--skip-secondary"], cwd=str(REPO))
        log(f"{name} 部署 rc={d.returncode}")
    log("ALL_DONE")


if __name__ == "__main__":
    main()
