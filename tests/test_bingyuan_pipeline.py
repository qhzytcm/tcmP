# -*- coding: utf-8 -*-
"""病源辭典流水线 单测（pytest）
覆盖：竖排列重建(S2) · 笔画序(S3/S4) · 词条切分 · 主题词索引(S6)
"""
import os, sys, json, importlib.util as U

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, 'scripts')
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def _load(name):
    spec = U.spec_from_file_location(name, os.path.join(SCRIPTS, name + '.py'))
    mod = U.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope='module')
def s2():
    return _load('s2_convert')


@pytest.fixture(scope='module')
def s3():
    return _load('s3_typeset')


# ── S2 竖排列重建（x 中心聚类，右起，列内 y 升序）──────────────
def _seg(x0, y0, x1, y1, txt):
    return {'box': [[x0, y0], [x1, y0], [x1, y1], [x0, y1]], 'text': txt}


def test_page_text_vertical_column_clustering(s2):
    rec = {'lines': [
        _seg(100, 0, 140, 200, 'AAA'), _seg(100, 300, 140, 500, 'BBB'),   # 左列两段
        _seg(200, 0, 240, 200, 'CCC'), _seg(200, 300, 240, 500, 'DDD'),   # 右列两段
    ]}
    txt, vert = s2.page_text(rec)
    assert vert is True
    assert txt == 'CCCDDDAAABBB'          # 右列先，列内自上而下


def test_page_text_horizontal(s2):
    rec = {'lines': [
        _seg(0, 200, 300, 214, '第二行'), _seg(0, 100, 300, 114, '第一行'),
    ]}
    txt, vert = s2.page_text(rec)
    assert vert is False
    assert txt == '第一行第二行'


def test_page_text_empty(s2):
    assert s2.page_text({'lines': []}) == ('', False)


# ── S4 笔画序 ────────────────────────────────────────────────
def test_stroke_key_ordering(s3):
    assert s3.stroke_key('病')[0] == 10
    assert s3.stroke_key('中')[0] == 4
    # 首字笔画升序：中(4) < 伤(6) < 病(10)
    ks = sorted(['病', '中', '伤'], key=s3.stroke_key)
    assert ks == ['中', '伤', '病']
    # 同首字按次字：中风 & 中暑 —— 风(4) < 暑(12)
    assert s3.stroke_key('中风') < s3.stroke_key('中暑')


# ── 词条切分 + 笔画升序编号 ──────────────────────────────────
def test_extract_and_sort(s3):
    pages = [(10, '前言无词条'),
             (11, '【病源】皆可溯其因【中风】乃风邪所中【伤寒】由寒邪而致')]
    ents = s3.extract_entries(pages)
    assert [e['head'] for e in ents] == ['病源', '中风', '伤寒']
    ents.sort(key=lambda e: (s3.stroke_key(e['head']), e['head']))
    for i, e in enumerate(ents, 1):
        e['no'] = f'{i:04d}'
    keys = [s3.stroke_key(e['head']) for e in ents]
    assert keys == sorted(keys)              # 升序无倒置
    assert [e['no'] for e in ents] == ['0001', '0002', '0003']


# ── S6 主题词索引 ────────────────────────────────────────────
def test_subject_index(s3):
    ents = [{'no': '0001', 'head': '中风', 'body': '风邪入中宜搜风养血'},
            {'no': '0002', 'head': '伤寒', 'body': '寒邪为病宜温散'},
            {'no': '0003', 'head': '风湿', 'body': '风湿相搏'}]
    idx = s3.build_subject_index(ents)
    assert '风' in idx and '寒' in idx
    assert '0001' in idx['风'] and '0003' in idx['风']
    assert idx['寒'] == ['0002']


# ── S7 规范化为 ICD-11/病证单元做准备 ────────────────────────
@pytest.fixture(scope='module')
def s7():
    return _load('s7_normalize')


def test_normalize_ocr_fix(s7):
    assert '病状' in s7.normalize_text('病送')          # 保守校正
    assert '参见' in s7.normalize_text('参看')          # 同义归一


def test_normalize_punct_fullwidth(s7):
    out = s7.normalize_text('寒热,头痛.咳;')
    assert '，' in out and '。' in out and '；' in out


def test_normalize_strip_noise(s7):
    out = s7.normalize_text('中风★☆abc123风')
    assert '★' not in out and '☆' not in out
    assert '风' in out


def test_split_sections(s7):
    body = '前导病源由风邪所中病状卒然仆倒治法宜搜风养血'
    secs = s7.split_sections(body)
    assert set(secs) == {'病源', '病状', '治法'}
    assert '风邪' in secs['病源'] and '仆倒' in secs['病状'] and '搜风' in secs['治法']


def test_s7_stroke_key(s7):
    assert s7.stroke_key('病')[0] == 10
    assert sorted(['病', '中'], key=s7.stroke_key)[0] == '中'


# ── S9+S10 端到端：编译含目录/索引的 PDF 并校验页码标注 ──────
def test_s9_s10_index_page_numbers(tmp_path):
    s9 = _load('s9_index')
    s10 = _load('s10_index_verify')
    terms = [
        {'no': '0001', 'head': '中风', 'body': '风邪所中宜搜风养血通络熄风' * 4, 'icd11': {'code': '8B20'}},
        {'no': '0002', 'head': '伤寒', 'body': '寒邪为病宜麻黄桂枝温散逐寒' * 4, 'icd11': None},
        {'no': '0003', 'head': '病源', 'body': '溯其因以明治法分病源病状治法' * 4, 'icd11': {'code': 'BA00'}},
    ]
    out = str(tmp_path / 'book.pdf')
    d2, toc, pmap = s9.build_book(terms, out)
    assert os.path.exists(out) and d2.page >= 2
    assert set(pmap) == {'0001', '0002', '0003'}          # 三条均有页码
    tp = tmp_path / 'terms.json'
    tp.write_text(json.dumps(terms, ensure_ascii=False), encoding='utf-8')
    rep = s10.verify(out, str(tp), out=str(tmp_path / 'verify.json'))
    assert rep['ok'], rep['checks']
    names = [c['name'] for c in rep['checks']]
    assert sum(1 for n in names if '页码正确' in n) >= 3      # 目录三节页码校验项均在


# ── S11 docx：域/书签/双栏 XML（不需 Word COM）─────────────
def test_s11_docx_fields_and_columns(tmp_path):
    import zipfile
    s11 = _load('s11_docx')
    terms = [{'no': '0001', 'head': '中风', 'body': '风邪所中' * 8, 'icd11': {'code': '8B20'}},
             {'no': '0002', 'head': '伤寒', 'body': '寒邪为病' * 8, 'icd11': None}]
    out = str(tmp_path / 'b.docx')
    s11.build_docx(terms, out, {'风': ['0001']})
    xml = zipfile.ZipFile(out).read('word/document.xml').decode('utf-8')
    assert ' PAGEREF e0001 \\h ' in xml          # 词条索引页码域
    assert ' PAGEREF sec_body \\h ' in xml       # 目录正文页域
    assert 'w:name="e0001"' in xml and 'w:name="sec_index"' in xml   # 书签
    assert 'w:cols' in xml and 'w:num="2"' in xml                    # 正文双栏


# ── S13 语义向量二次矫正：助手逻辑 + 安全护栏 ───────────────
def test_s13_helpers():
    s13 = _load('s13_semantic_fix')
    assert s13.edit_distance_le1('病源辞', '病源典') is True       # 单字替换
    assert s13.edit_distance_le1('病源辞', '病源') is False       # 长度不同
    assert s13.edit_distance_le1('治法外治', '法外治法') is False  # 轮转（多位不同）
    sk = s13.skipkeys('治法外治')
    assert len(sk) == 4
    assert s13.skipkeys('法外治法') & sk          # 轮转共享 skip-key → 故须以「同字集」排除


def test_s13_no_headword_auto_merge():
    """回归护栏：v1 曾把 上焦寒→上焦热（不同病名）自动合并，禁止重演。"""
    import inspect
    src = inspect.getsource(_load('s13_semantic_fix'))
    assert "t['head'] = " not in src and "t['head']=" not in src   # 词目只产复核清单，不自动改
    assert 'headword_review' in src


# ── S14 结构一致性：三要素切分 + 不改写正文护栏 ─────────────
def test_s14_split3_basic_and_variants():
    s14 = _load('s14_structure_audit')
    s = s14.split3('病源由湿热所致病状面目俱黄治法宜茵陈五苓散')
    assert '湿热' in s['病源'] and '面目俱黄' in s['病状'] and '茵陈' in s['治法']
    # OCR 变体：满源→病源边界 / 病送→病状边界 / 洛法→治法边界
    v = s14.split3('满源由风邪病送身体作寒洛法宜温散')
    assert '风邪' in v['病源'] and '身体作寒' in v['病状'] and '温散' in v['治法']


def test_s14_split_does_not_rewrite_text():
    """护栏：S14 只切边界、不引入新字符（正文原样）。"""
    s14 = _load('s14_structure_audit')
    body = '满源由风邪病送身体作寒洛法宜温散'
    s = s14.split3(body)
    joined = s['病源'] + s['病状'] + s['治法']
    assert set(joined) <= set(body)          # 未引入任何新字符
    assert '风邪' in joined and '温散' in joined


# ── S15/S17 LLM 标点：保字与防跑偏护栏 ───────────────────
def test_s15_rule_punct_preserves_chars():
    s15 = _load('s15_llm_punct')
    body = '病源由湿热所致病状面目俱黄治法宜茵陈'
    out = s15.rule_punct(body)
    assert s15.strip_punct(out) == s15.strip_punct(body)   # 只加标点、逐字不改
    assert '。' in out and '，' in out


def test_s17_validator_guards():
    s17 = _load('s17_merge_llm')
    inp = '病源由湿热所致病状面目俱黄'
    assert s17.valid(inp, '病源由湿热所致，病状面目俱黄。', loose=True)      # 仅加标点 → 通过
    assert not s17.valid(inp, '本病由湿热之邪引起，症见面目发黄并伴小便短赤等症。', loose=True)  # 跑偏 → 拒
    assert not s17.valid(inp, '病源由湿热所致', loose=True)                  # 过短 → 拒
    assert s17.valid(inp, inp, loose=False) and not s17.valid(inp, '病源由湿热所致病状面目俱黄赤', loose=False)


# ── S18/S19 上下文重构：重构档校验 + 结构保真 ───────────────
def test_s19_rebuild_validator():
    s19 = _load('s19_merge_rebuild')
    src = '病源由湿热所致，病状面目俱黄，治法宜茵陈。'
    ok, why = s19.valid(src, '病源由湿热郁蒸所致，病状面目俱黄，治法宜茵陈。')
    assert ok, why                                                     # 合理重构 → 通过
    assert not s19.valid(src, '本病系湿热为患。')[0]                    # 过短 → 拒
    assert '缺标记' in s19.valid(src, '病源由湿热所致，病状面目俱黄。')[1]   # 丢 治法 标记 → 结构不保真
    runaway = '现代医学认为本病系湿热之邪蕴结中焦所致，临床以面目发黄为主症。' * 4
    assert not s19.valid(src, runaway)[0]                              # 写成另篇 → 重合/长度越界

