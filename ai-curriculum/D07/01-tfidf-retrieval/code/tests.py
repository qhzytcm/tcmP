# -*- coding: utf-8 -*-
"""
01-tfidf-retrieval · 确定性测试（纯标准库，无外部依赖）
运行: python tests.py
"""
from __future__ import annotations
import main


def test_tokenize_bigram():
    """中文连续段按字符 bigram 切分"""
    assert main.tokenize("恶寒重发热轻") == ["恶寒", "寒重", "重发", "发热", "热轻"]
    # 英文整词 + 中文 bigram 混合
    toks = main.tokenize("covid 恶寒重")
    assert "covid" in toks and "恶寒" in toks


def test_idf_rare_terms_weighted_higher():
    """IDF：罕见词权重 > 全语料共现词权重"""
    idx = main.TfidfIndex()
    idx.fit(main.corpus_texts(main.MINI_CORPUS))
    idf_common = max(idx.idf[t] for t in idx.idf
                     if idx.df[t] >= len(main.MINI_CORPUS) - 1)
    idf_rare = min(idx.idf[t] for t in idx.idf if idx.df[t] == 1)
    assert idf_rare > idf_common
    # 公式核对：df=1（N=5）→ log(6/2)+1 ≈ 2.0986；df=5 → log(6/6)+1 = 1.0
    assert abs(idf_common - 1.0) < 1e-9


def test_cold_syndrome_retrieval():
    """『恶寒重 发热轻 无汗』→ Top1 普通感冒（风寒束表证）"""
    idx = main.TfidfIndex()
    idx.fit(main.corpus_texts(main.MINI_CORPUS))
    r = main.search("恶寒重 发热轻 无汗", idx, main.MINI_CORPUS, 1)
    assert r[0]["disease"].startswith("普通感冒"), r
    assert r[0]["formula"] == "麻黄汤"


def test_insomnia_retrieval():
    """『难以入睡 多梦易醒 心烦不安』→ Top1 原发性失眠（心肾不交证）"""
    idx = main.TfidfIndex()
    idx.fit(main.corpus_texts(main.MINI_CORPUS))
    r = main.search("难以入睡 多梦易醒 心烦不安", idx, main.MINI_CORPUS, 1)
    assert r[0]["disease"].startswith("原发性失眠"), r
    assert r[0]["syndrome"] == "心肾不交证"


def test_cosine_identity_and_symmetry():
    """归一化向量自相似=1；余弦满足对称性"""
    idx = main.TfidfIndex()
    idx.fit(main.corpus_texts(main.MINI_CORPUS))
    qv = idx.vectorize("心烦不安")
    assert abs(idx.cosine(qv, qv) - 1.0) < 1e-9
    assert idx.cosine(qv, idx.vectors[1]) == idx.cosine(idx.vectors[1], qv)


def test_topk_respected():
    """top_k 参数被尊重且结果有序"""
    idx = main.TfidfIndex()
    idx.fit(main.corpus_texts(main.MINI_CORPUS))
    r = main.search("头晕 目眩 烦躁 易怒", idx, main.MINI_CORPUS, 2)
    assert len(r) == 2
    assert r[0]["score"] >= r[1]["score"]


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
