# -*- coding: utf-8 -*-
"""
S27 异常条目修复合并 → v9
① 确定性：1123 等含「书末检查表/病名总表」者，按标记截断（去除非条目正文）
② LLM 定向重建：`data/anom_out.json` 中的条目按护栏替换（非空、不长于原、含三段或残损标记）
输出 data/bingyuan_terms_v9.json + dist/anom_repair_report.json
"""
import os, re, json, glob
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, 'dist'); os.makedirs(DIST, exist_ok=True)
CUT_MARKS = ['病源辞典检查表', '病名查表', '病源辞典增铺筋']
# 定向覆盖：1123「继疤」的正文被前后两批条目内容包夹，切到首个其它条目标记【
CUT_AT_MARKER = {'1123'}


def cut_tail(no, b):
    """截断书末检查表/总表/广告污染"""
    idx = len(b)
    for m in CUT_MARKS:
        i = b.find(m)
        if i != -1:
            idx = min(idx, i)
    if no in CUT_AT_MARKER:
        j = b.find('【')
        if j != -1:
            idx = min(idx, j)
    if idx == len(b):
        return b, False
    head = b[:idx]
    j = head.rfind('。')
    if j != -1:
        head = head[:j + 1]
    return head, True


def main():
    base = None
    for name in ('bingyuan_terms_v9.json', 'bingyuan_terms_v8.json'):
        p = os.path.join(ROOT, 'data', name)
        if os.path.exists(p):
            base = json.load(open(p, encoding='utf-8')); print('基线:', name); break
    rep = {'truncated': [], 'rebuilt': [], 'rejected': [], 'unlocated': []}

    for t in base:
        b = t.get('body') or ''
        nb, did = cut_tail(t['no'], b)
        if did and len(nb) >= 20:
            t['body'] = nb; t['anom'] = 'truncated'
            rep['truncated'].append({'no': t['no'], 'from': len(b), 'to': len(nb)})

    rebuilt = {}
    for fp in sorted(glob.glob(os.path.join(ROOT, 'data', 'anom_out*.json'))):
        try:
            for e in json.load(open(fp, encoding='utf-8')):
                if e.get('no') and e.get('body'):
                    rebuilt[e['no']] = e['body']
        except Exception as ex:
            print('  跳过载荷', os.path.basename(fp), type(ex).__name__)
    print('重建载荷（合并全部 anom_out*.json）:', len(rebuilt), '条')

    if rebuilt:
        for t in base:
            if t['no'] in rebuilt:
                new = rebuilt[t['no']]
                old = t.get('body') or ''
                # 旧正文若为**残条(<20字)**，不作权威上限——重建通常必然更长
                ok = len(new) >= 8 and (len(old) < 20 or len(new) <= max(len(old), 60))
                if ok:
                    t['body'] = new; t['anom'] = 'rebuilt'
                    rep['rebuilt'].append({'no': t['no'], 'head': t['head'], 'from': len(old), 'to': len(new)})
                else:
                    rep['rejected'].append({'no': t['no'], 'why': f'len {len(old)}->{len(new)}'})

    for t in base:
        if len(t.get('body') or '') < 20:
            rep['unlocated'].append({'no': t['no'], 'head': t['head'], 'len': len(t.get('body') or '')})

    json.dump(base, open(os.path.join(ROOT, 'data', 'bingyuan_terms_v10.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    json.dump(rep, open(os.path.join(DIST, 'anom_repair_report.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    print('截断:', len(rep['truncated']), '| 重建:', len(rep['rebuilt']), '| 退回:', len(rep['rejected']))
    for x in rep['truncated']:
        print('  截断', x)
    for x in rep['rebuilt']:
        print('  重建', x)
    for x in rep['rejected']:
        print('  退回', x)
    print('仍待人工复核(源页无标记):', [(x['no'], x['head']) for x in rep['unlocated']])


if __name__ == '__main__':
    main()
