# -*- coding: utf-8 -*-
"""
S69 病名↔内容 一致性核查（**确定性**，替代危险的编辑距离提案）

判据（用户规格「目录词条-正文病名-**内容对应**」）：
  真病名的字，**应当出现在本条正文里**（如「大肠咳」→ 正文须有「咳」）。
  · 名字的字在正文中缺失 → **可疑**（误识/误切）
  · 全面扫描"可疑名"，供逐条人工/规则判定；**不自动改字**（禁编造）
"""
import os, re, json
from collections import Counter
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, 'dist')
UNITS = json.load(open(os.path.join(ROOT, 'data', 'pdf3_units_v2.json'), encoding='utf-8'))
# 虚字/通用字不参与一致性判定
STOP = set('一二三四五六七八九十上下内外阴阳太少中大小病证症痛毒风热寒湿气血咳泄痧瘤疽'
           '之的不与和及或然者为以於于其有无所')


def core(name):
    return set(c for c in name if c not in STOP)


def main():
    susp, ok = [], 0
    for i, u in enumerate(UNITS):
        n, b = (u.get('name') or '').strip(), (u.get('body') or '')
        if not n or n == '病名待定' or len(n) < 2:
            continue
        cs = core(n)
        if not cs:
            ok += 1
            continue
        miss = [c for c in cs if c not in b]
        if miss:
            susp.append({'i': i, 'name': n, 'miss': ''.join(miss), 'in_body': len(cs) - len(miss), 'tot': len(cs)})
        else:
            ok += 1
    print(f'单元 {len(UNITS)} | 名↔内容 一致 {ok} | **可疑 {len(susp)}**')
    print('\n=== 可疑名（名字的字在正文中缺失）前 36 条 ===')
    for s in susp[:36]:
        u = UNITS[s['i']]
        print(f"  {s['i']+1:04d}【{s['name']}】缺[{s['miss']}]  {u['body'][:46]}")
    json.dump(susp, open(os.path.join(DIST, 'pdf3_name_content_audit.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    print(f'\n→ dist/pdf3_name_content_audit.json（{len(susp)} 条）')


if __name__ == '__main__':
    main()
