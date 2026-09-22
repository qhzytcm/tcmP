# -*- coding: utf-8 -*-
"""
S41 全量繁→简归一 → v15
① 对 head/body 统一 opencc t2s 转换
② **保护**：若某字的简体目标落在 CJK 扩展区（U+20000+，罕见字，仿宋无字形→豆腐块），
   则保留原字形（如 瞤/憹/喎 在中医文本中即为通行写法）
输出 data/bingyuan_terms_v15.json + dist/t2s_report.json
"""
import os, json
from collections import Counter
import opencc
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, 'dist'); os.makedirs(DIST, exist_ok=True)
t2s = opencc.OpenCC('t2s')


def safe_t2s(s):
    if not s:
        return s
    o = t2s.convert(s)
    if len(o) != len(s):
        return o
    out = []
    for a, c in zip(s, o):
        # 目标不在「常用汉字区」(U+4E00–9FFF) → 属扩展区罕见字，仿宋无字形 → 保留原字形
        # 例：喎→㖞(ExtA) / 瞤→𥆧(ExtB) / 憹→𢙐 / 齘→𬹼 / 勣→𪟝；中医文本通行用原字形
        if a != c and not (0x4E00 <= ord(c) <= 0x9FFF):
            out.append(a)
        else:
            out.append(c)
    return ''.join(out)


def main():
    d = json.load(open(os.path.join(ROOT, 'data', 'bingyuan_terms_v14.json'), encoding='utf-8'))
    pairs = Counter(); hn = bn = 0; kept = Counter()
    for t in d:
        h, b = t.get('head') or '', t.get('body') or ''
        nh, nb = safe_t2s(h), safe_t2s(b)
        if nh != h:
            t['head'] = nh; hn += 1
        if nb != b:
            t['body'] = nb; bn += 1
        if nh != h or nb != b:
            s, o = nh + nb, h + b
            if len(s) == len(o):
                for a, c in zip(o, s):
                    if a != c:
                        pairs[a + '→' + c] += 1
        # 统计被保护（未转）的罕见目标
        full = t2s.convert(h + b)
        cur = nh + nb
        if len(full) == len(cur):
            for a, c in zip(cur, full):
                if a != c:
                    kept[a + '→' + c] += 1
    json.dump(d, open(os.path.join(ROOT, 'data', 'bingyuan_terms_v15.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    rep = {'head_changed': hn, 'body_changed': bn, 'conversions': dict(pairs.most_common()),
           'protected_rare': dict(kept.most_common())}
    json.dump(rep, open(os.path.join(DIST, 't2s_report.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f'词目改动 {hn} 条 | 正文改动 {bn} 条 / 共 {len(d)} 条')
    print('\n已转换（繁→简）:')
    for k, n in pairs.most_common(24):
        print(f'  {k} ×{n}')
    print('\n受保护未转（目标为扩展区罕见字）:')
    for k, n in kept.most_common(12):
        print(f'  {k} ×{n}')
    # 复检：还有无常见繁体残留
    rest = Counter()
    for t in d:
        s = t2s.convert((t.get('head') or '') + (t.get('body') or ''))
        o = (t.get('head') or '') + (t.get('body') or '')
        if len(s) == len(o):
            for a, c in zip(o, s):
                if a != c:
                    rest[a] += 1
    print('\n仍存繁简差异的字:', dict(rest.most_common(12)) or '无')


if __name__ == '__main__':
    main()
