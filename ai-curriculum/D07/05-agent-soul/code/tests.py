# -*- coding: utf-8 -*-
"""
05-agent-soul · 确定性测试（纯标准库，不触发真实 LLM 调用）
运行: python tests.py
"""
from __future__ import annotations
import json
import main


def _agent():
    return main.SageAgent(main.MINI_CORPUS,
                          main.corpus_texts(main.MINI_CORPUS))


def test_soul_structure_complete():
    """SOUL 结构：六经表 6 条、引语、身份、防编造边界"""
    a = _agent()
    assert len(a.soul["six_channels"]) == 6
    assert len(a.soul["quotes"]) >= 2 and a.soul["identity"]
    assert "编造" in a.soul["knowledge_boundary"]


def test_mentor_depth_changes_with_level():
    """师带徒：教学要求随 user_level 变化"""
    a = _agent()
    p1 = main.build_soul_system_prompt(a.soul, "住院医-1")
    p3 = main.build_soul_system_prompt(a.soul, "主治医")
    assert "基础概念" in p1 and "鉴别诊断" in p3
    assert "住院医-1" in p1 and "主治医" in p3
    # 六经表与语录进 system prompt
    assert "太阳病" in p1 and "观其脉证" in p1


def test_tool_retrieval_works():
    """工具：检索返回病证候选"""
    a = _agent()
    r = a.retrieve_tool("失眠多梦 心烦不安")
    assert r and r[0]["disease"]
    assert all("formula" in x and "syndrome" in x for x in r)


def test_local_consult_structure_and_level():
    """本地师带徒：结构完整（辨证/论治/经典/思考题/免责），深度随级别变"""
    a = _agent()
    r1 = a.consult("失眠多梦 心烦不安", user_level="住院医-1")
    assert r1["mode"] == "local"
    for key in ("辨证", "论治", "经典", "思考题", "免责"):
        assert key in r1["reply"], f"缺 {key}"
    assert "住院医-1" in r1["reply"]
    r3 = a.consult("失眠多梦 心烦不安", user_level="主治医")
    assert "主治医" in r3["reply"] and "鉴别" in r3["reply"]
    assert r1["reply"] != r3["reply"], "不同级别回答应不同"


def test_history_memory():
    """状态记忆：多次问诊入档"""
    a = _agent()
    a.consult("失眠多梦 心烦不安", user_level="住院医-1")
    a.consult("恶寒重 发热轻 无汗", user_level="住院医-2")
    assert len(a.history) == 2
    assert a.history[0]["chief_complaint"] == "失眠多梦 心烦不安"
    assert a.history[1]["user_level"] == "住院医-2"


def test_llm_system_prompt_has_soul_and_level():
    """LLM 注入：system prompt 含人格与阶段，user prompt 含检索参考"""
    a = _agent()
    calls = {}

    def fake(req, timeout=60):
        body = json.loads(req.data)
        calls["sys"] = body["messages"][0]["content"]
        calls["user"] = body["messages"][1]["content"]
        class R:
            def __enter__(self_):
                return self_

            def __exit__(self_, *exc):
                return False

            def read(self_):
                return ('{"choices":[{"message":{"content":'
                        '"辨证：少阴病…"}}]}').encode()
        return R()

    orig = main.urllib.request.urlopen
    main.urllib.request.urlopen = fake
    try:
        a.api_key = "sk-test"
        r = a.consult("失眠多梦 心烦不安", user_level="主治医")
        assert r["mode"] == "llm"
        assert "张仲景" in calls["sys"] and "主治医" in calls["sys"]
        assert "鉴别诊断" in calls["sys"]
        assert "病证库检索参考" in calls["user"]
        assert "1. 先辨证" in calls["user"] and "5. 末尾附免责声明" in calls["user"]
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
