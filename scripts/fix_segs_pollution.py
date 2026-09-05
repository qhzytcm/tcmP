# -*- coding: utf-8 -*-
"""素问 segs json 污染修复：TAIL/MIX 型篇 —— 截断 talk 中的 Hermes 段与广告句，保留正常讲解。
- Hermes 段：从 'Hermes独立理解' 出现处截断（保留其前讲解文本）
- 广告句：整句剔除（含 人纪求真/应用商店/视频一听就懂 等推广语）
- 修复范围：27 篇（17,29,36,38,39-62 区间内非 FULL 篇），由 classify 自动判定
- FULL 篇（57,63-80）不在此处理（需源数据重生成）
用法: python fix_segs_pollution.py [--apply]
"""
import json
import re
from pathlib import Path

VD = Path(r"C:\Users\DELL\tcmP\docs\视频")
HERMES_START = "Hermes独立理解"
HERMES_RE = re.compile(r"Hermes独立理解《[^》]*》\s*[（(]?追加内容[）)]?[:：]?|Hermes独立理解《[^》]*》[:：]")
# 广告句：常见推广语整体剔除（含前后标点）
AD_PAT = re.compile(
    r"搜索人[纪际]求真下载使用吧[。！]?|快到手机应用商店搜索人纪求真下载使用吧[。！]?"
    r"|你是否遇到过视频一听就懂[，、。！]?|视频一听就懂[，、。！]?"
    r"|告别学了后面忘了前边的问题[。！]?"
    r"|他能帮你快速梳理知识框架[。！]?|它能帮你快速梳理知识框架[。！]?"
    r"|帮你快速梳理知识框架[。！]?|让零散的知识点一目了然[。！]?"
    r"|快速梳理知识框架[。！]?|人纪求真[。！]?|手机应用商店搜索[。！]?"
)

FIX = [17, 29, 36, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49,
       50, 51, 52, 53, 54, 55, 56, 58, 59, 60, 61, 62]


def fix_talk(talk):
    if not talk:
        return talk
    # 1) 去广告句（优先整句，防 Hermes 段内残留）
    t = AD_PAT.sub('', talk)
    # 2) 截断 Hermes 段（含"追加内容"与直接拼接两种形态）
    m = HERMES_RE.search(t)
    if m:
        t = t[:m.start()]
    # 3) 若截断后仍有裸 'Hermes独立理解'（无《》形态）兜底
    idx = t.find(HERMES_START)
    if idx > 0:
        t = t[:idx]
    # 4) 最小干预：仅清理截断处产生的悬挂标点/空白，不做句号规范化
    t = re.sub(r'[，。；、\s]+$', '', t)
    return t


def main():
    apply = '--apply' in __import__('sys').argv
    report = []
    for ch in FIX:
        f = VD / f'segs_suwen{ch}.json'
        if not f.exists():
            report.append((ch, 'MISSING', ''))
            continue
        data = json.loads(f.read_text(encoding='utf-8'))
        changed = 0
        for s in data:
            # talk: Hermes 截断 + 广告剔除
            old = s.get('talk', '')
            new = fix_talk(old)
            if new != old:
                s['talk'] = new
                changed += 1
            # orig: 广告剔除（保留原文内容）
            oo = s.get('orig', '')
            on = AD_PAT.sub('', oo)
            on = re.sub(r'[，。；、\s]+$', '', on)
            if on != oo:
                s['orig'] = on
                changed += 1
        out = json.dumps(data, ensure_ascii=False, indent=1)
        if apply:
            f.write_text(out, encoding='utf-8')
        report.append((ch, 'OK' if changed else 'NOCHG',
                       f'{changed}字段修复'))
    for ch, st, msg in report:
        print(f'素问{ch:>2}: {st}  {msg}')


if __name__ == '__main__':
    main()
