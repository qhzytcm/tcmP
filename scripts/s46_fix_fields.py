# -*- coding: utf-8 -*-
"""
S46 补修遗漏字段 → v18（覆盖）
① `alias` 字段（别名列表）也施加全部校字规则
② `front_matter.json` 凡例/自序文本同步（原先举例「痘疗」→「痘疔」）
③ 「疗→疔」改为**循环至稳定**，处理相邻情形（如「疔疗例」）
"""
import os, json, re
from collections import Counter
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, 'dist')
SEQ = [
    ('太阳嘛病', '太阳经病'),
    ('牛身不途', '半身不遂'), ('半身不途', '半身不遂'),
    ('牛身不肌', '半身不遂'), ('半身不肌', '半身不遂'),
    ('牛身', '半身'), ('不途', '不遂'),
    ('气咂', '气呃'), ('咂逆', '呃逆'),
    ('欢', '咳'),
]
RX_LIAO = re.compile(r'(?<![治医疗])疗(?!法|效|程)')


def fix_text(s, log, tag):
    o = s
    for a, b in SEQ:
        if a in o:
            log[f'[{tag}] {a}→{b}'] += o.count(a)
            o = o.replace(a, b)
    for _ in range(4):                       # 循环至稳定（处理相邻）
        n = len(RX_LIAO.findall(o))
        if not n:
            break
        log[f'[{tag}] 疗→疔'] += n
        o = RX_LIAO.sub('疔', o)
    return o


def main():
    d = json.load(open(os.path.join(ROOT, 'data', 'bingyuan_terms_v17.json'), encoding='utf-8'))
    log = Counter(); ents = set()
    for t in d:
        ch = False
        for f in ('head', 'body', 'parent'):
            s = t.get(f)
            if s:
                o = fix_text(s, log, f)
                if o != s:
                    t[f] = o; ch = True
        # ① alias 列表
        if t.get('alias'):
            na = [fix_text(a, log, 'alias') for a in t['alias']]
            if na != t['alias']:
                t['alias'] = na; ch = True
        if ch:
            ents.add(t['no'])
    json.dump(d, open(os.path.join(ROOT, 'data', 'bingyuan_terms_v18.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    # ② 前置件文本
    fp = os.path.join(ROOT, 'data', 'front_matter.json')
    fm = json.load(open(fp, encoding='utf-8'))
    flog = Counter()
    fm['preface'] = [fix_text(p, flog, 'preface') for p in fm['preface']]
    fm['notes'] = [[k, fix_text(v, flog, 'notes')] for k, v in fm['notes']]
    json.dump(fm, open(fp, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    for k, v in flog.items():
        print('  前置件', k, '×', v)
    # 复检
    rest = Counter()
    for t in d:
        s = ((t.get('head') or '') + (t.get('body') or '') + (t.get('parent') or '') + ''.join(t.get('alias') or []))
        for a, b in SEQ:
            rest[a] += s.count(a)
        rest['疗(非治疗类)'] += len(RX_LIAO.findall(s))
    for p in fm['preface']:
        rest['疗(非治疗类)'] += len(RX_LIAO.findall(p))
    for k, v in fm['notes']:
        rest['疗(非治疗类)'] += len(RX_LIAO.findall(v))
    json.dump({'changes': dict(log.most_common()), 'entries_changed': len(ents), 'remaining': dict(rest)},
              open(os.path.join(DIST, 'v12_fix_report.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('改动条目:', len(ents), '/', len(d))
    for k, v in log.most_common():
        print(f'  {k}  ×{v}')
    print('复检残留:', dict(rest))


if __name__ == '__main__':
    main()
