# -*- coding: utf-8 -*-
"""
03-rag-dialogue · 确定性测试（纯标准库，无外部依赖；不触发 LLM 调用）
运行: python tests.py
"""
from __future__ import annotations
import main


def _rag():
    return main.RAGPipeline(main.MINI_CORPUS,
                            main.corpus_texts(main.MINI_CORPUS))


def test_retrieve_top1_dual_hit():
    """检索环节：失眠查询 Top1 双路命中"""
    rag = _rag()
    r = rag.retrieve("难以入睡 多梦易醒 心烦不安")
    assert r[0]["disease"].startswith("原发性失眠")
    assert r[0]["in_vector"] and r[0]["in_keyword"]


def test_build_context_fields():
    """上下文组装：含病名/证候/方剂/证据字段"""
    rag = _rag()
    r = rag.retrieve("难以入睡 多梦易醒 心烦不安")
    ctx = rag.build_context(r)
    for key in ("原发性失眠", "心肾不交证", "黄连阿胶汤", "证据"):
        assert key in ctx, f"上下文缺 {key}"


def test_prompt_has_anti_hallucination_constraint():
    """生成指令含防幻觉约束（只允许引用检索结果）"""
    rag = _rag()
    p = rag.augment_prompt("失眠", rag.build_context(rag.retrieve("失眠")))
    assert "只允许引用检索结果" in p and "库外" in p


def test_local_mode_deterministic_structure():
    """无 key 自动降级本地模板；报告结构完整且引用 Top1"""
    rag = _rag()
    a = rag.ask("难以入睡 多梦易醒 心烦不安")
    assert a["mode"] == "local", f"无 key 应降级本地: {a['mode']}"
    assert "最可能的病证组合" in a["report"]
    assert "推荐方剂方向" in a["report"]
    assert "原发性失眠" in a["report"]
    assert "鉴别要点" in a["report"] and "原发性高血压" in a["report"]


def test_faithfulness_local_100pct():
    """faithfulness：本地模板报告 100% 可溯源到 Top-K"""
    rag = _rag()
    a = rag.ask("难以入睡 多梦易醒 心烦不安")
    f = rag.faithfulness(a["results"], a["report"])
    assert f["coverage"] == 1.0
    assert "原发性失眠" in f["cited"]


def test_llm_mode_respects_key():
    """有 key 时 mode=llm 且返回 token_estimate（不真正调用，注入假响应）"""
    rag = _rag()
    rag.api_key = "sk-test"
    orig = main.urllib.request.urlopen

    def fake_urlopen(req, timeout=60):
        payload = ("【最可能的病证组合】原发性失眠（ICD-11: 7A00）")
        class R:
            def __enter__(self):
                return self

            def __exit__(self, *exc):
                return False

            def read(self):
                return ('{"choices":[{"message":{"content":"'
                        + payload + '"}}]}').encode("utf-8")
        return R()

    main.urllib.request.urlopen = fake_urlopen
    try:
        a = rag.ask("难以入睡 多梦易醒 心烦不安")
        assert a["mode"] == "llm", f"有 key 应走 LLM: {a['mode']}"
        assert "原发性失眠" in a["report"]
        assert "token_estimate" in a and a["token_estimate"] > 0
    finally:
        main.urllib.request.urlopen = orig


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items())
             if k.startswith("test_") and callable(v)]
    passed = 0
    for t in tests:
        try:
            t()
            print(f"  ✅ {t.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"  ❌ {t.__name__}: {e}")
        except Exception as e:
            print(f"  💥 {t.__name__}: {type(e).__name__}: {e}")
    print(f"\n{passed}/{len(tests)} 通过")
    raise SystemExit(0 if passed == len(tests) else 1)
