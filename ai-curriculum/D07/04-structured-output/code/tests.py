# -*- coding: utf-8 -*-
"""
04-structured-output · 确定性测试（纯标准库，不触发真实 LLM 调用）
运行: python tests.py
"""
from __future__ import annotations
import json
import main


def _rag():
    return main.StructuredRAG(main.MINI_CORPUS,
                              main.corpus_texts(main.MINI_CORPUS))


GOOD = {"disease": "原发性失眠", "icd11_code": "7A00",
        "syndrome": "心肾不交证", "formula": "黄连阿胶汤",
        "confidence": 0.32, "differential": ["与高血压对比，需四诊鉴别"],
        "evidence_gap": False}


def test_valid_object_passes():
    """合法对象通过 RAG_REPORT_SCHEMA 校验"""
    rag = _rag()
    assert rag.validate_json(GOOD) == []


def test_validator_rejects_each_violation():
    """缺必填/pattern/越界/类型错 各自被拦截"""
    rag = _rag()
    v = rag.validator
    no_disease = {k: GOOD[k] for k in GOOD if k != "disease"}
    assert any("缺少必填字段 disease" in e
               for e in v.validate(no_disease, main.RAG_REPORT_SCHEMA))
    assert any("pattern" in e for e in v.validate(
        dict(GOOD, icd11_code="7a00"), main.RAG_REPORT_SCHEMA))
    assert any("maximum" in e for e in v.validate(
        dict(GOOD, confidence=1.5), main.RAG_REPORT_SCHEMA))
    assert any("boolean" in e for e in v.validate(
        dict(GOOD, evidence_gap="yes"), main.RAG_REPORT_SCHEMA))
    assert any("minLength" in e for e in v.validate(
        dict(GOOD, disease="原"), main.RAG_REPORT_SCHEMA))
    assert any("minItems" in e for e in v.validate(
        dict(GOOD, differential=[]), main.RAG_REPORT_SCHEMA))


def test_local_json_deterministic_and_valid():
    """local_json 确定性 + schema 合规 + 关键字段正确"""
    rag = _rag()
    results = rag.retrieve("难以入睡 多梦易醒 心烦不安")
    d1, d2 = main.local_json(results), main.local_json(results)
    assert d1 == d2, "local_json 应确定性"
    assert rag.validate_json(d1) == [], rag.validate_json(d1)
    assert d1["disease"] == "原发性失眠"
    assert d1["evidence_gap"] is True   # mini 语料 RRF≈0.033 < 0.05 → 低分声明
    assert isinstance(d1["differential"], list) and len(d1["differential"]) >= 1


def test_llm_retry_then_success():
    """LLM 注入：第一次坏 JSON（缺字段）→ 重试 → 第二次好 JSON → 成功"""
    rag = _rag()
    calls = {"n": 0}

    def fake(req, timeout=60):
        calls["n"] += 1
        content = (json.dumps({"disease": "原发性失眠", "icd11_code": "7A00"},
                              ensure_ascii=False) if calls["n"] == 1
                   else json.dumps(GOOD, ensure_ascii=False))
        class R:
            def __enter__(self_):
                return self_

            def __exit__(self_, *exc):
                return False

            def read(self_):
                return ('{"choices":[{"message":{"content":'
                        + json.dumps(content, ensure_ascii=False) + '}}]}').encode()
        return R()

    orig = main.urllib.request.urlopen
    main.urllib.request.urlopen = fake
    try:
        rag.api_key = "sk-test"
        a = rag.ask("难以入睡 多梦易醒 心烦不安")
        assert a["mode"] == "llm" and a["attempts"] == 2 and a["valid"], a
    finally:
        main.urllib.request.urlopen = orig


def test_llm_always_bad_degrades_to_local():
    """LLM 一直坏 → 重试用尽 → 降级本地模板（graceful degradation）"""
    rag = _rag()

    def fake(req, timeout=60):
        class R:
            def __enter__(self_):
                return self_

            def __exit__(self_, *exc):
                return False

            def read(self_):
                return ('{"choices":[{"message":{"content":"not json"}}]}').encode()
        return R()

    orig = main.urllib.request.urlopen
    main.urllib.request.urlopen = fake
    try:
        rag.api_key = "sk-test"
        a = rag.ask("难以入睡 多梦易醒 心烦不安")
        assert a["mode"] == "local" and a.get("degraded") is True
        assert a["valid"] is True and a["data"]["disease"] == "原发性失眠"
    finally:
        main.urllib.request.urlopen = orig


def test_dsu_skeleton_validates_real_data():
    """平台真实 DSU 样本通过骨架 schema（id pattern + 必填骨架）"""
    from pathlib import Path
    rag = _rag()
    samples = list(Path(r"C:\Users\DELL\tcmP\kg\samples").glob("dsu-samples-*.json"))
    assert samples, "未找到平台 DSU 样本"
    dsu = json.loads(samples[0].read_text(encoding="utf-8"))[0]
    errs = rag.validator.validate(dsu, main.DSU_SKELETON_SCHEMA)
    assert errs == [], errs
    # id 违规样例被拒
    bad = dict(dsu, id="DSU-1")
    assert any("pattern" in e
               for e in rag.validator.validate(bad, main.DSU_SKELETON_SCHEMA))


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
