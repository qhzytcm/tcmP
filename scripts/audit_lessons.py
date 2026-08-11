#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
audit_lessons.py — AI 课程门禁审计（教学版）
============================================
对齐 ai-engineering-from-scratch 的 audit_lessons.py（L001-L010）精神，
校验 ai-curriculum/ 下每门课程的四件套契约（docs / code / quiz / outputs）：

  L001 目录命名 NN-lesson-slug/（两位数序号）
  L002 docs/zh.md 存在且含六拍关键小节（H1 + MOTTO + 学习目标 + 问题 +
       概念 + 从零实现 + 平台实现 + 交付制品 + 习题 + 术语表）
  L003 code/main.py 存在且语法可编译（py_compile，不执行）
  L004 quiz.json 通过 6 题契约（1 pre + 3 check + 2 post、4 选项、
       correct 零索引、每题含 explanation、lesson 字段匹配）
  L005 outputs/ 非空，制品 .md 含 frontmatter（name/description），
       且 name 以 skill- 或 prompt- 前缀（平台制品命名约定）
  L006 code/tests.py 存在且可运行，退出码 0（自动跑单元测试）
  L007 code/main.py --self-test 可运行，退出码 0（自动跑内置自检）

用法:
  python scripts/audit_lessons.py                    # 全量审计
  python scripts/audit_lessons.py --lesson 01        # 过滤单课（序号前缀）
  python scripts/audit_lessons.py --json             # JSON 输出（CI 友好）
  python scripts/audit_lessons.py --strict           # 有 FAIL 时 exit 1

CI 挂载: .github/workflows/tcm-ci-cd.yml → ai-curriculum-audit job
"""
from __future__ import annotations
import argparse
import json
import os
import py_compile
import re
import subprocess
import sys
from pathlib import Path

LESSON_DIR_RE = re.compile(r"^(\d{2})-[a-z0-9-]+$")
# 六拍关键小节（docs/zh.md 必须覆盖）
REQUIRED_SECTIONS = [
    ("H1 标题", r"^#\s+\S+"),
    ("MOTTO 引用块", r"^>\s+\S+"),
    ("学习目标", r"学习目标"),
    ("问题（The Problem）", r"问题（The Problem）"),
    ("概念（The Concept）", r"概念（The Concept）"),
    ("从零实现（BUILD IT）", r"从零实现"),
    ("平台实现（USE IT）", r"平台实现"),
    ("交付制品（SHIP IT）", r"交付制品"),
    ("习题", r"习题"),
    ("术语表", r"术语表"),
]
QUIZ_STAGES = {"pre": 1, "check": 3, "post": 2}


def audit_lesson(lesson_dir: Path) -> dict:
    """审计单课，返回 {rule: (ok, detail)} 与 lessons 级问题列表"""
    checks = {}
    name = lesson_dir.name

    # ── L001 目录命名 ──
    m = LESSON_DIR_RE.match(name)
    checks["L001 目录命名"] = (
        (True, f"NN={m.group(1)}") if m else (False, "须为 NN-lesson-slug"))

    # ── L002 docs/zh.md 六拍小节 ──
    doc = lesson_dir / "docs" / "zh.md"
    if doc.exists():
        content = doc.read_text(encoding="utf-8")
        missing = [label for label, rx in REQUIRED_SECTIONS
                   if not re.search(rx, content, re.M)]
        checks["L002 docs 六拍"] = (
            (True, f"{len(REQUIRED_SECTIONS) - len(missing)}/{len(REQUIRED_SECTIONS)} 小节")
            if not missing else (False, "缺: " + ", ".join(missing)))
    else:
        checks["L002 docs 六拍"] = (False, "docs/zh.md 不存在")

    # ── L003 code/main.py 可编译 ──
    main_py = lesson_dir / "code" / "main.py"
    if main_py.exists():
        try:
            py_compile.compile(str(main_py), doraise=True)
            checks["L003 main.py 编译"] = (True, "py_compile OK")
        except py_compile.PyCompileError as e:
            checks["L003 main.py 编译"] = (False, str(e).splitlines()[-1][:120])
    else:
        checks["L003 main.py 编译"] = (False, "code/main.py 不存在")

    # ── L004 quiz.json 6 题契约 ──
    quiz = lesson_dir / "quiz.json"
    if quiz.exists():
        try:
            q = json.loads(quiz.read_text(encoding="utf-8"))
            qs = q["questions"]
            stages = [x["stage"] for x in qs]
            ok = (q.get("lesson") == name
                  and len(qs) == 6
                  and all(stages.count(s) == n for s, n in QUIZ_STAGES.items())
                  and all(len(x["options"]) == 4 and 0 <= x["correct"] < 4
                          and x["explanation"] for x in qs))
            checks["L004 quiz 契约"] = (
                (True, "6题(1+3+2) OK") if ok else
                (False, f"契约违规: lesson={q.get('lesson')!r} 题数={len(qs)} "
                        f"分布={stages.count('pre')}/{stages.count('check')}/"
                        f"{stages.count('post')}"))
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            checks["L004 quiz 契约"] = (False, f"解析失败: {e}")
    else:
        checks["L004 quiz 契约"] = (False, "quiz.json 不存在")

    # ── L005 outputs/ 制品 frontmatter ──
    out_dir = lesson_dir / "outputs"
    if out_dir.exists():
        arts = sorted(out_dir.glob("*.md"))
        bad = []
        for a in arts:
            head = a.read_text(encoding="utf-8")[:400]
            fm = re.match(r"^---\s*\n(.*?)\n---", head, re.S)
            if not fm:
                bad.append(f"{a.name}: 缺 frontmatter")
                continue
            meta = dict(re.findall(r"^(\w+):\s*(.+)$", fm.group(1), re.M))
            if not meta.get("name") or not meta.get("description"):
                bad.append(f"{a.name}: name/description 缺失")
            elif not re.match(r"^(skill|prompt)-", meta["name"]):
                bad.append(f"{a.name}: name 须以 skill-/prompt- 开头")
        checks["L005 outputs 制品"] = (
            (True, f"{len(arts)} 个制品合规") if arts and not bad
            else (False, "; ".join(bad) or "outputs/ 为空"))
    else:
        checks["L005 outputs 制品"] = (False, "outputs/ 不存在")

    # ── L006 tests.py 自动跑 ──
    tests_py = lesson_dir / "code" / "tests.py"
    if tests_py.exists():
        r = subprocess.run([sys.executable, str(tests_py.resolve())],
                           cwd=str(lesson_dir), capture_output=True,
                           text=True, encoding="utf-8",
                           env={**os.environ, "PYTHONIOENCODING": "utf-8"},
                           timeout=180)
        tail = (r.stdout or r.stderr).strip().splitlines()
        checks["L006 tests.py"] = (
            (True, tail[-1][:80] if tail else "exit=0")
            if r.returncode == 0 else
            (False, f"exit={r.returncode}: "
                    f"{(tail[-1] if tail else '')[:80]}"))
    else:
        checks["L006 tests.py"] = (False, "code/tests.py 不存在")

    # ── L007 main.py --self-test 自动跑 ──
    if main_py.exists():
        r = subprocess.run([sys.executable, str(main_py.resolve()),
                            "--self-test"],
                           cwd=str(lesson_dir), capture_output=True,
                           text=True, encoding="utf-8",
                           env={**os.environ, "PYTHONIOENCODING": "utf-8"},
                           timeout=180)
        tail = (r.stdout or r.stderr).strip().splitlines()
        checks["L007 self-test"] = (
            (True, tail[-1][:80] if tail else "exit=0")
            if r.returncode == 0 else
            (False, f"exit={r.returncode}: "
                    f"{(tail[-1] if tail else '')[:80]}"))
    return checks


def main():
    ap = argparse.ArgumentParser(description="AI 课程门禁审计（教学版）")
    ap.add_argument("--dir", default="ai-curriculum",
                    help="课程根目录（默认 ai-curriculum）")
    ap.add_argument("--lesson", default="",
                    help="只审计指定序号前缀（如 01）")
    ap.add_argument("--json", action="store_true", dest="as_json")
    ap.add_argument("--strict", action="store_true",
                    help="存在 FAIL 时以退出码 1 结束（CI 用）")
    args = ap.parse_args()

    root = Path(args.dir)
    if not root.is_dir():
        print(f"❌ 课程目录不存在: {root}")
        sys.exit(2)

    # 支持单层（root/NN-lesson）与双层（root/领域/NN-lesson）结构
    lessons = []
    for d in sorted(root.iterdir()):
        if not d.is_dir():
            continue
        if LESSON_DIR_RE.match(d.name):
            lessons.append(d)      # 单层：课程直接在根下
        else:
            lessons += [c for c in sorted(d.iterdir())
                        if c.is_dir() and LESSON_DIR_RE.match(c.name)]
    if args.lesson:
        lessons = [d for d in lessons if d.name.startswith(args.lesson)]
    if not lessons:
        print(f"⚠️ 未找到课程目录（{root}）")
        sys.exit(0)

    report = {}
    n_fail = 0
    for lesson in lessons:
        checks = audit_lesson(lesson)
        report[lesson.name] = {k: (v[0], v[1]) for k, v in checks.items()}
        n_fail += sum(1 for ok, _ in checks.values() if not ok)

    if args.as_json:
        print(json.dumps({
            "tool": "audit_lessons.py",
            "curriculum": str(root),
            "lessons_audited": len(lessons),
            "rules_failed": n_fail,
            "lessons": report,
        }, ensure_ascii=False, indent=2))
    else:
        print(f"=== AI 课程门禁审计（{root}）===\n")
        for lname, checks in report.items():
            fails = [k for k, (ok, _) in checks.items() if not ok]
            mark = "✅" if not fails else "❌"
            print(f"{mark} {lname}" + (f"  [{len(fails)} 规则失败]" if fails else ""))
            for rule, (ok, detail) in checks.items():
                print(f"    {'  ✅' if ok else '  ❌'} {rule}: {detail}")
        print(f"\n课程 {len(lessons)} 门 · 规则失败 {n_fail} 项")
        if n_fail:
            print("❌ 门禁未通过——请修复后再提交")
        else:
            print("✅ 门禁全绿")

    sys.exit(1 if (args.strict and n_fail) else 0)


if __name__ == "__main__":
    main()
