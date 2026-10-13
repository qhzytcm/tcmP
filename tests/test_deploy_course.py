# -*- coding: utf-8 -*-
"""deploy_course_to_frontends 自检：文件筛选（纯逻辑）+ 从前端不可达分支。

不触网：不可达分支通过 monkeypatch 固定，保证离线可复现。
用法：python -m pytest -q tests/test_deploy_course.py
"""
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))

import deploy_course_to_frontends as d  # noqa: E402


def _fake_book(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    for n in ("index.html", "zhongji-jichu-course.json",
              "第01章-1绪论-视频课程.html", "第01章-1绪论.mp4"):
        (root / n).write_text("x", encoding="utf-8")
    # 中间件与缓存 —— 必须被排除
    (root / "ch01").mkdir()
    (root / "ch01" / "p01.wav").write_text("x", encoding="utf-8")
    (root / "ch01" / "p01.png").write_text("x", encoding="utf-8")
    (root / "__pycache__").mkdir()
    (root / "__pycache__" / "junk.html").write_text("x", encoding="utf-8")
    return root


def test_course_files_filters_middleware_and_cache(tmp_path):
    book = _fake_book(tmp_path / "book")
    files = {p.name for p in d._course_files(book)}
    assert files == {"index.html", "zhongji-jichu-course.json",
                     "第01章-1绪论-视频课程.html", "第01章-1绪论.mp4"}
    # ch*/ 中间件与 __pycache__ 不得泄漏
    assert all(not any(p in ("ch01", "__pycache__") for p in f.parts)
               for f in d._course_files(book))


def test_course_files_empty_dir(tmp_path):
    (tmp_path / "empty").mkdir()
    assert d._course_files(tmp_path / "empty") == []


def test_deploy_secondary_blocked_when_unreachable(tmp_path, monkeypatch):
    """22 不可达 → 返回 None（阻塞），不抛异常、不假装成功。"""
    monkeypatch.setattr(d, "_ssh_reachable", lambda *a, **k: False)
    book = _fake_book(tmp_path / "book")
    assert d.deploy_secondary("zhongji-jichu", book, "", "", "") is None


def test_deploy_secondary_missing_creds_when_reachable(tmp_path, monkeypatch):
    """SSH 可达但无凭据/站点根 → 仍返回 None（阻塞）。"""
    monkeypatch.setattr(d, "_ssh_reachable", lambda *a, **k: True)
    monkeypatch.delenv("TCM_SECONDARY_PASS", raising=False)
    monkeypatch.delenv("TCM_SECONDARY_ROOT", raising=False)
    book = _fake_book(tmp_path / "book")
    assert d.deploy_secondary("zhongji-jichu", book, "", "", "") is None
