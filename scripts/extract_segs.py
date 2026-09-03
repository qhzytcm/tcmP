# -*- coding: utf-8 -*-
"""从 HDNJ音频理解(2).xls 提取 1-上古天真论 十段（原文+讲解）
原文: "原文-" 短句按十段关键词归类拼接
讲解: "注释-"/"理解-"/"总结-" 段按十段关键词提取合并（数据源忠实）
输出: docs/视频/segs.json（十段: 段题/原文/讲解/角色/类型）
"""
import json
import re
from pathlib import Path

import pandas as pd

X = r'C:\Users\DELL\Desktop\HDNJ音频理解(2).xls'
df = pd.read_excel(X, sheet_name='1-上古天真论')

# 收集三类内容
orig_sents, notes, unds, summary = [], [], [], ''
for v in df['文本内容'].dropna():
    t = str(v).strip()
    if t.startswith('原文-'):
        orig_sents.append(t[3:].strip())
    elif t.startswith('注释-'):
        notes.append(t[3:].strip())
    elif t.startswith('理解-'):
        unds.append(t[3:].strip())
    elif t.startswith('总结-'):
        summary = t[3:].strip()

print(f'原文短句 {len(orig_sents)} / 注释 {len(notes)} / 理解 {len(unds)}')

# ===== 十段定义（段题 + 原文关键词 + 讲解关键词）=====
SEG_DEF = [
    ('第一段 · 开篇', ['生而神灵', '弱而能言', '成而登天'],
     ['开篇', '黄帝', '生而神灵']),
    ('第二段 · 发问', ['余闻上古之人', '春秋皆度百岁', '时世异耶', '人将失之'],
     ['发问', '时世异', '半百', '百岁']),
    ('第三段 · 总答', ['法于阴阳', '和于术数', '食饮有节', '起居有常', '不妄作劳', '形与神俱'],
     ['法于阴阳', '术数', '食饮', '起居', '天年', '总答']),
    ('第四段 · 论今人', ['今时之人不然也', '以酒为浆', '以妄为常', '醉以入房', '以欲竭其精', '半百而衰'],
     ['今时之人', '以酒为浆', '竭其精', '半百', '今人']),
    ('第五段 · 圣人教下', ['虚邪贼风', '恬惔虚无', '真气从之', '精神内守', '病安从来'],
     ['恬惔虚无', '真气从之', '精神内守', '虚邪', '病安']),
    ('第六段 · 德全不危', ['志闲而少欲', '心安而不惧', '形劳而不倦', '德全不危', '高下不相慕'],
     ['志闲', '少欲', '心安', '德全', '美其食', '朴']),
    ('第七段 · 女子七纪', ['女子七岁', '二七', '天癸至', '月事', '七七', '地道不通'],
     ['女子', '七岁', '天癸', '月事', '七七', '任脉']),
    ('第八段 · 男子八纪', ['丈夫八岁', '二八', '精气溢泻', '八八', '齿发去'],
     ['丈夫', '八岁', '精气', '八八', '齿发']),
    ('第九段 · 贤人圣人', ['贤人', '法则天地', '圣人', '处天地之和', '八风之理', '亦可以百数'],
     ['贤人', '圣人', '法则天地', '八风', '百数']),
    ('第十段 · 至人真人', ['至人', '淳德全道', '真人', '提挈天地', '把握阴阳', '寿敝天地'],
     ['至人', '真人', '提挈天地', '寿敝', '道生']),
]

# ===== 原文: 短句归类拼接 =====
def match_sent(sent, kws):
    return any(k in sent for k in kws)

def build_orig(sents, kws):
    """收集含关键词的原文短句（智能去重: 子串/高度重叠保留长者）"""
    picked = []
    for s in sents:
        if match_sent(s, kws):
            picked.append(s)
    merged = []
    for s in picked:
        if not s:
            continue
        dup = False
        for i, m in enumerate(merged):
            if s in m or m in s:
                # 保留较长者
                if len(s) > len(m):
                    merged[i] = s
                dup = True
                break
        if not dup:
            merged.append(s)
    return '，'.join(merged)


def clean_part(p):
    """清洗: 去 Hermes 独立理解引言重复/括号噪音"""
    p = re.sub(r'^Hermes独立理解《上古天真论》：通读原文、译文与对话全程后，我以系统科学视角重新梳理此篇的内在逻辑。', '', p)
    p = re.sub(r'^[一二三四五六七八九十]+、', '', p)
    p = p.replace('（鼓掌）', '').replace('（笑）', '')
    return p.strip()


def build_talk(notes, unds, summary, kws):
    """讲解: 注释段(白话)优先 + 理解条目 + 总结相关（去重清洗）"""
    parts = []
    # ① 注释段（逐句白话讲解; 排除 Hermes 独立理解长文总纲）
    for n in notes:
        if n.startswith('Hermes独立理解'):
            continue
        if match_sent(n, kws) and len(n) > 14:
            parts.append(clean_part(n))
    # ② 理解条目（生活化）
    parts += [clean_part(u) for u in unds if len(u) > 6 and match_sent(u, kws)]
    # ③ 总结分段
    for sp in re.split(r'[①②③④⑤⑥]', summary):
        if match_sent(sp, kws) and len(sp) > 12:
            parts.append(clean_part(sp.strip()))
    # 去重（完全相同/包含）
    seen, out = [], []
    for p in parts:
        if not p:
            continue
        if any(p == q or (len(p) > 20 and (p in q or q in p)) for q in seen):
            continue
        seen.append(p)
        out.append(p)
    talk = '。'.join(out)
    if len(talk) > 480:
        talk = talk[:480] + '。'
    return talk if len(talk) > 40 else '（讲解）'


segs = []
for title, orig_kws, talk_kws in SEG_DEF:
    orig = build_orig(orig_sents, orig_kws)
    talk = build_talk(notes, unds, summary, talk_kws)
    segs.append({'title': title, 'orig': orig, 'talk': talk})
    print(f'\n{title}')
    print(f'  原文({len(orig)}字): {orig[:90]}...' if len(orig) > 90 else f'  原文: {orig}')
    print(f'  讲解({len(talk)}字): {talk[:70]}...')

OUT = Path(r'C:\Users\DELL\tcmP\docs\视频\segs.json')
OUT.write_text(json.dumps(segs, ensure_ascii=False, indent=1), encoding='utf-8')
print(f'\n✅ 已保存: {OUT.name}')
