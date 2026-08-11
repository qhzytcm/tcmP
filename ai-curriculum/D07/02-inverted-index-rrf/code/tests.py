# -*- coding: utf-8 -*-
"""
02-inverted-index-rrf · 确定性测试（纯标准库，无外部依赖）
运行: python tests.py
"""
from __future__ import annotations
import main


def _env():
    tfidf = main.TfidfIndex()
    tfidf.fit(main.corpus_texts(main.MINI_CORPUS))
    inv = main.InvertedIndex()
    inv.build(main.corpus_texts(main.MINI_CORPUS))
    return tfidf, inv


def test_postings_structure():
    """倒排表：词 → 包含它的文档集合"""
    _, inv = _env()
    assert 0 in inv.postings["恶寒"] and 1 not in inv.postings["恶寒"]
    # 「失眠」出现于失眠(病名) 与 高血压(症状「失眠多梦」)
    assert 1 in inv.postings["失眠"] and 3 in inv.postings["失眠"]


def test_or_vs_and():
    """OR 并集召回全，AND 交集召回精"""
    _, inv = _env()
    or_hits = inv.query("恶寒 失眠", mode="or")
    and_hits = inv.query("恶寒 失眠", mode="and")
    assert 0 in or_hits and 1 in or_hits and 3 in or_hits
    assert and_hits == []          # 无文档同时含「恶寒」与「失眠」
    # AND 精确命中：只有感冒同时有「恶寒」「无汗」
    assert inv.query("恶寒 无汗", mode="and") == [0]


def test_rrf_formula_exact():
    """RRF 公式精确值：score = Σ 1/(k + rank + 1)，k=60"""
    f = main.rrf_fuse([(0, 0.5)], {0}, k=60)
    assert abs(f[0][1] - (1 / 61 + 1 / 61)) < 1e-9
    # 三路名次贡献：向量第3名(1/63) + 关键词第1名(1/61)
    f2 = main.rrf_fuse([(5, 0.1), (7, 0.2), (9, 0.3)], {9}, k=60)
    expect = 1 / 63 + 1 / 61
    assert abs(f2[0][1] - expect) < 1e-9 and f2[0][0] == 9


def test_rrf_dual_hit_beats_single():
    """双路命中的文档胜过单路——融合的意义所在"""
    # 文档1：向量第1名，关键词未命中；文档3：向量第2名 + 关键词第1名
    fused = main.rrf_fuse([(1, 0.5), (3, 0.3)], {3}, k=60)
    assert fused[0][0] == 3, f"双路命中应排前: {fused}"
    assert fused[0][1] > fused[1][1]
    # 反向验证：向量第1名 + 关键词第1名（1/61+1/61=0.0328）
    #             vs 向量第20名 + 关键词第2名（1/81+1/62=0.0285）
    fused2 = main.rrf_fuse([(1, 0.5)] + [(i, 0.0) for i in range(2, 21)],
                           {1, 2}, k=60)
    assert fused2[0][0] == 1


def test_hybrid_search_top1_and_tags():
    """混合检索：失眠查询 → Top1 原发性失眠，双路命中标记正确"""
    tfidf, inv = _env()
    out, _, inv_hits = main.hybrid_search(
        "难以入睡 多梦易醒 心烦不安", tfidf, inv, main.MINI_CORPUS, top_k=3)
    assert out[0]["disease"].startswith("原发性失眠"), out
    assert out[0]["in_vector"] and out[0]["in_keyword"], "失眠应双路命中"
    # 高血压(3) 症状含「失眠多梦」→ 关键词命中，但向量排序靠后
    hits = {r["disease"] for r in out}
    assert any(d.startswith("原发性高血压") for d in hits)


def test_topk_respected():
    """top_k 被尊重"""
    tfidf, inv = _env()
    out, _, _ = main.hybrid_search("心烦 失眠", tfidf, inv, main.MINI_CORPUS, 2)
    assert len(out) == 2
    assert out[0]["rrf"] >= out[1]["rrf"]


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
