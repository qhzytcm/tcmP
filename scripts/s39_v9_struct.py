# -*- coding: utf-8 -*-
"""
S39 V9 结构改版 → v14
① 三段论拆分：正文中「治法：…」之后又出现「病源：」者，视为**无独立病名的连续三段论**，
   切分为独立条目（病名待定），排在父条目之后。
② 多级笔画排序：首字→第二字→第三字…（Unihan kTotalStrokes）
③ 别名抽取：即/俗称/又名/一名/亦名/俗名 + 命中现有词目（限定义式位置，防"即消"类误配）
④ 重编号 0001..N
输出 data/bingyuan_terms_v14.json + dist/v9_struct_report.json
"""
import os, re, json
from collections import Counter
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, 'dist'); os.makedirs(DIST, exist_ok=True)
S = json.load(open(os.path.join(ROOT, 'data', 'strokes.json'), encoding='utf-8'))
RX_SRC = re.compile(r'病源[:：]')
RX_ZHI = re.compile(r'治法[:：]')
# 别名定义式标记（高置信）
ALIAS_PATS = [('即俗名', r'即俗名([\u4e00-\u9fff]{2,6})'), ('俗称', r'俗称([\u4e00-\u9fff]{2,6})'),
              ('又名', r'又名([\u4e00-\u9fff]{2,6})'), ('一名', r'一名([\u4e00-\u9fff]{2,6})'),
              ('亦名', r'亦名([\u4e00-\u9fff]{2,6})'), ('俗名', r'俗名([\u4e00-\u9fff]{2,6})'),
              ('即', r'[，,、。；;]即([\u4e00-\u9fff]{2,6})'), ('即', r'^([\u4e00-\u9fff]{2,6})即'),
              ('即', r'即([\u4e00-\u9fff]{2,6})[，,、。；;（(]'), ('即', r'即([\u4e00-\u9fff]{2,6})也'),
              ('又', r'又([\u4e00-\u9fff]{2,6})者'), ('谓', r'俗谓([\u4e00-\u9fff]{2,6})')]


def st(ch):
    v = S.get(ch)
    if isinstance(v, int):
        return v
    if isinstance(v, list) and v:
        return v[0]
    return 999


def skey(head):
    return [st(c) for c in head] or [999]


def split_entry(t):
    """按「治法之后又见病源」切分"""
    b = t.get('body') or ''
    pos_z = [m.start() for m in RX_ZHI.finditer(b)]
    pos_s = [m.start() for m in RX_SRC.finditer(b)]
    if not pos_z:
        return [b]
    cut = sorted(set(s for s in pos_s if s > pos_z[0]))
    if not cut:
        return [b]
    parts, prev = [], 0
    for c in cut:
        parts.append(b[prev:c]); prev = c
    parts.append(b[prev:])
    return [p for p in parts if len(p.strip()) >= 12]


def main():
    src = json.load(open(os.path.join(ROOT, 'data', 'bingyuan_terms_v13.json'), encoding='utf-8'))
    heads = {t['head'] for t in src}
    out, nsplit = [], 0
    for t in src:
        parts = split_entry(t)
        base = {'head': t['head'], 'body': parts[0], 'icd11': t.get('icd11'), 'fts5': t.get('fts5'),
                'ver': t.get('ver'), 'srcver': t.get('ver')}
        # 别名
        al = set()
        for tag, p in ALIAS_PATS:
            for m in re.finditer(p, parts[0]):
                a = m.group(1).strip('，,、。')
                if a in heads and a != t['head']:
                    al.add(a)
        if al:
            base['alias'] = sorted(al)
        out.append(base)
        for k, p in enumerate(parts[1:], 1):
            out.append({'head': '病名待定', 'body': p, 'parent': t['head'], 'parent_no': t['no'],
                        'seq': k, 'ver': 'v9split'})
            nsplit += 1

    # 多级笔画排序（病名待定 继承父词目的笔画键 + 次序）
    def sortkey(e):
        if e['head'] == '病名待定':
            p = next((x for x in out if x['head'] == e['parent']), None)
            return (skey(p['head']) if p else [999], 1, e['seq'])
        return (skey(e['head']), 0, 0)

    out.sort(key=sortkey)
    for i, e in enumerate(out, 1):
        e['no'] = f'{i:04d}'
    json.dump(out, open(os.path.join(ROOT, 'data', 'bingyuan_terms_v14.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    nalias = sum(1 for e in out if e.get('alias'))
    rep = {'src': len(src), 'total': len(out), 'split_new': nsplit, 'alias_entries': nalias,
           'alias_total': sum(len(e['alias']) for e in out if e.get('alias')),
           'sample_alias': [(e['no'], e['head'], e['alias']) for e in out if e.get('alias')][:20]}
    json.dump(rep, open(os.path.join(DIST, 'v9_struct_report.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    print(f"原 {len(src)} 条 → 拆分新增 {nsplit} 条 → 合计 {len(out)} 条")
    print(f"含别名条目 {nalias} 条 / 别名 {rep['alias_total']} 个")
    for x in rep['sample_alias'][:12]:
        print('  ', x)


if __name__ == '__main__':
    main()
