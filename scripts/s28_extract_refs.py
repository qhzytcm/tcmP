# -*- coding: utf-8 -*-
"""
S28 从「醒了么(张仲景)」4 个资产抽取中医药病因辨证规范
输出： data/tcm_ref_lexicon.json （规范术语词表）
       data/tcm_ref_conventions.md （体例约定简报，供 LLM 提示词引用）
"""
import os, re, json
from collections import Counter
D = r'C:\Users\DELL\Desktop\醒了么(张仲景)'
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ── 1. 核心规范术语（依资产中的体系直接给定）──
SIX_XIE = ['风', '寒', '暑', '湿', '燥', '火', '热']
SEVEN_QING = ['怒', '喜', '悲', '思', '恐', '忧', '惊']
WU_ZANG = ['肝', '心', '脾', '肺', '肾']
LIU_FU = ['胆', '胃', '小肠', '大肠', '膀胱', '三焦']
QI_HENG = ['脑', '髓', '骨', '脉', '女子胞']
STAGES = ['感', '侵', '传', '化', '损']          # 五阶段：感→侵→传→化→损
BENG_TERMS = ['病机', '传变', '表证', '里证', '卫气', '营气', '气血', '津液', '阴阳', '五行',
              '虚实', '寒热', '表里', '脏腑', '经络', '气滞', '血瘀', '痰湿', '水饮', '内陷',
              '化热', '伤津', '耗气', '动血', '闭脱', '逆传', '直中', '内伤', '外感',
              '六淫', '七情', '不内外因', '三因', '正虚', '邪实', '阴阳失调', '气血失和']

# ── 2. 从 4 个资产中再抽取：出现在"病因/病机"语境的高频中医词 ──
CJL = re.compile(r'[\u4e00-\u9fff]{2,6}')
skip = re.compile(r'[０-９0-9A-Za-z_×∈≥≤\(\)\[\]{}|/\\=＋+\-—·：:；;，,。\.、"\'%]')
words = Counter()
def feed(txt):
    for w in CJL.findall(txt or ''):
        if len(w) >= 2 and not skip.search(w):
            words[w] += 1

try:
    import openpyxl, xlrd
    for f in ('内因七情.xlsx', '外因六淫.xlsx'):
        wb = openpyxl.load_workbook(os.path.join(D, f), read_only=True, data_only=True)
        for ws in wb.worksheets:
            for row in ws.iter_rows(values_only=True):
                for c in row:
                    if isinstance(c, str):
                        feed(c)
        wb.close()
    for f in ('黄帝内经全文.xls',):
        wb = xlrd.open_workbook(os.path.join(D, f), on_demand=True)
        for name in wb.sheet_names():
            ws = wb.sheet_by_name(name)
            for i in range(ws.nrows):
                for j in range(ws.ncols):
                    v = ws.cell_value(i, j)
                    if isinstance(v, str):
                        feed(v)
        wb.release_resources()
except Exception as e:
    print('抽取部分失败:', type(e).__name__, str(e)[:120])

# 过滤出"医学味"的词：含 病/证/气/血/肝/心/脾/肺/肾/风/寒/暑/湿/燥/火/热/虚/实/痰/瘀/阴/阳 等
KEY = re.compile(r'[病证气血肝心脾肺肾风寒暑湿燥火热虚实痰瘀阴阳脏腑经络卫营津液]')
cand = [w for w, n in words.items() if n >= 3 and KEY.search(w) and 2 <= len(w) <= 5]
core = sorted(set(SIX_XIE + SEVEN_QING + WU_ZANG + LIU_FU + QI_HENG + BENG_TERMS + STAGES))
lex = {'core': core, 'extracted_top': sorted(cand, key=lambda w: -words[w])[:600],
       'stats': {'total_words': len(words), 'candidates': len(cand)}}
json.dump(lex, open(os.path.join(ROOT, 'data', 'tcm_ref_lexicon.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print('核心术语:', len(core), '| 抽取出候选:', len(cand))
print('高频候选前30:', cand[:30])

conv = """# 中医药病因辨证体例约定（源自「醒了么(张仲景)」资产）

## 一、三因辨证总纲
- **外因（六淫）**：风、寒、暑、湿、燥、火（热）。六邪索引 k∈{风,寒,热,燥,湿,暑}
- **内因（七情）**：怒、喜、悲、思、恐、忧、惊。七情伤脏：怒伤肝、喜伤心、思伤脾、悲忧伤肺、恐惊伤肾
- **不内外因**：饮食劳倦、跌扑金刃、虫兽所伤、房室不节

## 二、六淫致病五阶段（外因）
S1 感（屏障接触·卫气受扰）→ S2 侵（侵入·表证）→ S3 传（传变入脏腑）→ S4 化（深化·物质化）→ S5 损（损耗·崩解）

## 三、七情致病五阶段（内因）
刺激感应 → 脏腑响应 → 情绪涌现 → 情绪劫持 → 病机固着

## 四、脏腑定位
- 五脏：肝、心、脾、肺、肾；六腑：胆、胃、小肠、大肠、膀胱、三焦
- 七情伤脏：怒→肝／喜→心／思→脾／悲忧→肺／恐惊→肾

## 五、病机规范用语
表证·里证·半表半里；卫分·气分·营分·血分；气滞·血瘀·痰湿·水饮；
化热·伤津·耗气·动血·内陷·逆传·直中；正虚·邪实·虚实夹杂；阴阳失调·气血失和

## 六、校正判据（用于《病源辞典》正文）
1. **病因术语规范化**：「风寒」「风热」「湿热」「暑湿」「燥火」「痰湿」等复合病因须用规范词序。
2. **病机用语规范化**：「气血不足」而非「气血缺乏」；「肝气郁结」而非「肝气郁滞」；「津液亏耗」而非「津液耗损」。
3. **脏腑/经络名规范化**：手少阴心经、足阳明胃经等十二正经名；「手少阴经病」不可写作「手少除经病」。
4. **症状与病机分层**：症状（如「恶寒发热」）属病状；病机（如「风寒束表」）属病源。
5. **参见条保留**：「参见××条」照旧，不改写为现代白话。
"""
open(os.path.join(ROOT, 'data', 'tcm_ref_conventions.md'), 'w', encoding='utf-8').write(conv)
print('已写 data/tcm_ref_lexicon.json 与 data/tcm_ref_conventions.md')
