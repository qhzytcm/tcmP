# -*- coding: utf-8 -*-
"""rem_3 分块语义标点产物（data/llm_out2/rem_3_p1..p7.json）硬约束校验
覆盖：分块条数/no 顺序 · 每条均有标点 · 除标点外逐字恒等（仅允许白名单 OCR 矫正）
"""
import os, re, json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'data', 'llm_batches2', 'rem_3.json')
OUT = os.path.join(ROOT, 'data', 'llm_out2')

PUNCT = '，。、；：'

# 与 _blk/reconcile.py 的 CORR 一致：仅这些 OCR 字形误识可改
CORR = [('浩法', '治法'), ('洛法', '治法'), ('照法', '治法'),
        ('病默', '病状'), ('病送', '病状'), ('病肤', '病状'), ('病选', '病状'),
        ('病迭', '病状'), ('病达', '病状'), ('病跋', '病状'), ('病然', '病状'),
        ('病愿', '病源'), ('满源', '病源'), ('润源', '病源')]

SIZES = [40, 40, 40, 40, 40, 40, 27]


def _corr(s):
    for a, b in CORR:
        s = s.replace(a, b)
    return s


def _strip(s):
    return re.compile('[' + re.escape(PUNCT) + ']').sub('', s)


def _blocks():
    """[(分块号, 产物条目, 对应源切片)]，源切片按产物实际长度顺次切分。"""
    src = json.load(open(SRC, encoding='utf-8'))
    parts, i = [], 0
    for n in range(1, len(SIZES) + 1):
        d = json.load(open(os.path.join(OUT, 'rem_3_p%d.json' % n), encoding='utf-8'))
        parts.append((n, d, src[i:i + len(d)]))
        i += len(d)
    assert i == len(src)
    return parts


def test_sizes_and_no_order():
    blocks = _blocks()
    assert [len(d) for _, d, _ in blocks] == SIZES
    for n, d, s in blocks:
        assert [e['no'] for e in d] == [e['no'] for e in s], n


def test_keys_and_punctuation():
    for n, d, _ in _blocks():
        for e in d:
            assert set(e) == {'no', 'body'}, (n, e['no'])
            assert any(c in e['body'] for c in PUNCT), (n, e['no'])


def test_char_fidelity():
    for n, d, s in _blocks():
        for e, o in zip(d, s):
            assert _strip(e['body']) == _strip(_corr(o['body'])), (n, e['no'])
