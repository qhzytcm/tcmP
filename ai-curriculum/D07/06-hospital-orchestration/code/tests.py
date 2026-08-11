# -*- coding: utf-8 -*-
"""
06-hospital-orchestration · 确定性测试（纯标准库，不触发真实 LLM 调用）
运行: python tests.py
"""
from __future__ import annotations
import json
import main


def _hospital():
    return main.Hospital(main.MINI_CORPUS,
                         main.corpus_texts(main.MINI_CORPUS))


def test_six_roles_complete():
    """六者 SOUL 齐备：6 角色各含 mission/tools/boundary"""
    assert len(main.SIX_ROLES) == 6
    for role, soul in main.SIX_ROLES.items():
        assert soul["mission"] and soul["tools"] and soul["boundary"], role
    assert set(main.SIX_ROLES) == {"healer", "patient", "pharmacist",
                                   "device", "regulator", "legal"}


def test_router_routes_correctly():
    """路由：问题 → 正确角色；无关键词默认医者"""
    r = main.HospitalRouter()
    assert r.route("这张处方有附子15g") == "pharmacist"
    assert r.route("CT设备故障报修") == "device"
    assert r.route("医保报销纠纷咨询") == "legal"
    assert r.route("内科质控检查") == "regulator"
    assert r.route("不知道挂什么科") == "patient"
    assert r.route("随便聊聊") == "healer"


def test_role_local_handling():
    """各角色本地处理：患者自查导诊、医者辨证、药者十八反"""
    hospital = _hospital()
    p = hospital.agents["patient"].handle("失眠多梦")
    assert "自查" in p["reply"] and "导诊" in p["reply"]
    h = hospital.agents["healer"].handle("失眠多梦 心烦不安")
    assert "辨证" in h["reply"] and "论治" in h["reply"]
    ph = hospital.agents["pharmacist"].handle("审方：附子15g 半夏10g")
    assert ("十八反" in ph["reply"] or "相反" in ph["reply"]), ph["reply"]
    dev = hospital.agents["device"].handle("CT设备报错")
    assert "设备" in dev["reply"] and "维护" in dev["reply"]
    lg = hospital.agents["legal"].handle("术后纠纷咨询")
    assert "风险" in lg["reply"]


def test_visit_pipeline_four_steps():
    """就诊流水线：患者→医者→药者→规者 四步闭环"""
    hospital = _hospital()
    visit = hospital.visit_pipeline("失眠多梦 心烦不安")
    roles = [s["role"] for s in visit["steps"]]
    assert roles == ["patient", "healer", "pharmacist", "regulator"], roles
    assert visit["top"]["disease"].startswith("原发性失眠")
    assert visit["top"]["formula"] == "黄连阿胶汤合交泰丸"


def test_collab_log_records():
    """协作日志：流水线产生 ≥4 条记录（对话=进化信号）"""
    hospital = _hospital()
    hospital.visit_pipeline("失眠多梦 心烦不安")
    assert len(hospital.collab_log) >= 4
    assert hospital.collab_log[0]["to"] == "patient"


def test_llm_mode_system_prompt_has_role():
    """LLM 注入：医者有 key → mode=llm，system 含角色使命"""
    hospital = _hospital()
    calls = {}

    def fake(req, timeout=60):
        body = json.loads(req.data)
        calls["sys"] = body["messages"][0]["content"]
        class R:
            def __enter__(self_):
                return self_

            def __exit__(self_, *exc):
                return False

            def read(self_):
                return ('{"choices":[{"message":{"content":"辨证：少阴病"}}]}').encode()
        return R()

    orig = main.urllib.request.urlopen
    main.urllib.request.urlopen = fake
    try:
        hospital.agents["healer"].api_key = "sk-test"
        a = hospital.agents["healer"].handle("失眠多梦")
        assert a["mode"] == "llm"
        assert "医者" in calls["sys"] and "师带徒" in calls["sys"]
        assert "边界" in calls["sys"]
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
