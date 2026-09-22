# -*- coding: utf-8 -*-
"""
S77 正文清理器：去扫描污染噪声 + 标点整理（**确定性**）
规则（均先测后应用，禁改字义）：
  ① 汉字之间的空格 → 删（OCR 分词残留）
  ② 书眉残留「病源辞典」→ 删（正文不应含书名）
  ③ 段标记前导页码残渣（如「一九病源…」「四四」）→ 删
  ④ PDF 污染符号 # ○ 〇 ． · • ‥ + * 及零宽字符 → 删
  ⑤ 重复段标记 病源病源 → 病源
  ⑥ 多余空白折叠
"""
import re
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
from ocr_fix_rules import fix as _refix          # 校字规则（含 S80 形近讹字）

SYM = r'[#○〇．·•‥⋯+*﹃﹄【】「」『』]'   # 污染符号；**保留**中文引号 “”（LLM 正当使用）
PUNCT = '，。、；：？！'


def clean(t, drop_quotes=False):
    if not t:
        return t
    o = t
    o = o.replace('\u3000', ' ').replace('\ufeff', '').replace('\u200b', '')
    # ① **先**去汉字之间的空格（OCR 分词残留）——必须在去书眉/页码之前
    o = re.sub(r'(?<=[\u4e00-\u9fff])\s+(?=[\u4e00-\u9fff])', '', o)
    o = o.replace('病源辞典', '')                       # ② 书眉残留
    # ③ 段标记前的前导页码残渣（如「一九病源…」）
    o = re.sub(r'^[\s一二三四五六七八九十0-9]{1,6}(?=病源|病状|治法)', '', o)
    o = re.sub(SYM, '', o)                              # ④ 污染符号
    o = re.sub(r'[\[\]]', '', o)                        # ④b OCR 方括号残渣（[病源] 标记在 s72 之后才加）
    o = _refix(o)                                       # ⑤ 校字（形近讹字，幂等）
    o = re.sub(r'病源(?=病源)', '', o)                   # ⑥ 重复段标记
    o = re.sub(r'病状(?=病状)', '', o)
    o = re.sub(r'治法(?=治法)', '', o)
    o = re.sub(r'[ \t]{2,}', ' ', o)
    o = re.sub(r'\s+([，。、；：？！])', r'\1', o)
    o = re.sub(r'([，。、；：？！])\s+', r'\1', o)
    # ⑥ 全文无标点 → 末补句号（标点补全的最小保底；不动字词）
    if len(o.strip()) >= 8 and sum(o.count(c) for c in PUNCT) == 0:
        o = o.rstrip() + '。'
    o = o.strip()
    return o


def clean_toc(text, names):
    """目录串 → 干净名序。先剥点号/冒号噪声，再按**词表最长匹配**抽名，
    未命中的残片（OCR 页码残渣如「四四」「五」「七六六六五」）即被自然丢弃。"""
    S = re.sub(r'[.．·•‥⋯：:]+', '', text)
    S = S.replace('病源辞典', '')
    vocab = sorted(set(n for n in names if n and len(n) >= 2 and n != '病名待定'), key=len, reverse=True)
    out, i = [], 0
    while i < len(S):
        for nm in vocab:
            if S.startswith(nm, i):
                out.append(nm)
                i += len(nm)
                break
        else:
            i += 1
    # 去相邻重复（OCR 常把同一名重复）
    ded = [n for k, n in enumerate(out) if k == 0 or n != out[k - 1]]
    return ded


if __name__ == '__main__':
    import os, json
    ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    U = json.load(open(os.path.join(ROOT, 'data', 'pdf3_units_v2.json'), encoding='utf-8'))
    outs = {}
    for line in open(os.path.join(ROOT, 'data', 'pdf3_llm_out.jsonl'), encoding='utf-8', errors='replace'):
        line = line.strip()
        if line:
            try:
                r = json.loads(line)
            except Exception:
                continue
            if r['i'] not in outs or (r.get('ok') and not outs[r['i']].get('ok')):
                outs[r['i']] = r
    PUNCT = '，。、；：？！'
    n_clean = n_lost = 0
    for i, u in enumerate(U):
        r = outs.get(i)
        t = (r['out'] if (r and r.get('ok')) else u['body']) if r else u['body']
        c = clean(t)
        if c != t:
            n_clean += 1
            if len(c) < len(t) * 0.92:      # 删得过多 → 报警
                n_lost += 1
                if n_lost <= 6:
                    print(f'  [!] idx{i} 删减 {len(t)-len(c)} 字 ({len(t)}→{len(c)}) 【{u["name"]}】')
                    print(f'      原: {t[:70]}')
                    print(f'      后: {c[:70]}')
    print(f'\n被清理单元: {n_clean} / {len(U)} | 删减>8% 警示: {n_lost}')
    for i in (46, 92, 128, 168, 241, 414, 625):
        r = outs.get(i)
        t = (r['out'] if (r and r.get('ok')) else U[i]['body']) if r else U[i]['body']
        print(f'\nidx{i} 【{U[i]["name"]}】')
        print(f'  原: {t[:90]}')
        print(f'  后: {clean(t)[:90]}')
