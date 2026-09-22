# -*- coding: utf-8 -*-
"""
S15 按语义群追加标点（V4）
双引擎：
  · rule：确定性语义群切分（瞬时，**逐字不改**）——覆盖全量
  · llm ：浪潮 ollama 精修（缓存/可续跑；仅接受"去标点后逐字恒等"的输出）
合并：有合格 LLM 结果用 LLM，否则用 rule。
输入 data/bingyuan_terms_v3.json → 输出 data/bingyuan_terms_v4.json
"""
import os, re, json, argparse, urllib.request, time
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, 'dist'); os.makedirs(DIST, exist_ok=True)
BASE = 'http://192.168.0.102:11434'
CACHE = os.path.join(ROOT, 'data', 'llm_punct_cache.json')
PUNCT = '，。；、：？！“”‘’（）《》〈〉·—…,.!?;:()[]"\'　 \n\t'
RX = re.compile('[' + re.escape(PUNCT) + ']')
SENT = '⟦{}⟧'
MODEL = 'qwen2.5:7b'

# ── 语义群标点（规则引擎）──
MARK = re.compile(r'([病满润游漏瑞烤浏消荆房痛]源)|(病[状默送肤选迭达跋然])|([治洛活浩照浴跆沼陪邵路阁]法)')
CONN = re.compile(r'(故|因而|以致|所致|是以|因此|盖|夫|若|如|或|及|并|则|又|再|乃|遂|即|但|而不|如由|中因|是以)')
ADVICE = re.compile(r'(宜|用|服|忌|参看|参见|另|外治|敷|灸|针)')


def strip_punct(s):
    return RX.sub('', s)


def rule_punct(body):
    """按语义群切分：标记断句 → 连接词/治法词前加逗。**只插入标点，逐字保留（含标记）**。"""
    if not body:
        return body

    def inner(t):
        t = ADVICE.sub(lambda m: ('，' if m.start() > 3 else '') + m.group(0), t)
        t = CONN.sub(lambda m: ('，' if m.start() > 3 else '') + m.group(0), t)
        t = re.sub(r'，{2,}', '，', t)
        return t.strip('，')

    hits = [(m.start(), m.end()) for m in MARK.finditer(body)]
    segs = []
    if hits:
        if hits[0][0] > 0:
            segs.append(body[:hits[0][0]])
        for idx, (s, e) in enumerate(hits):
            nxt = hits[idx + 1][0] if idx + 1 < len(hits) else len(body)
            segs.append(body[s:nxt])          # 含标记本身，不丢字
    else:
        segs = [body]
    res = '。'.join(inner(s) for s in segs if s)
    return res + ('。' if res and not res.endswith('。') else '')


# ── LLM 引擎 ──
SYS = ('你是中医古籍整理专家。为每条正文按语义群添加标点（，。；、：），规则：\n'
       '1) 只添加标点，**绝对不得增删或替换任何文字（含数字）**；\n'
       '2) 逐条输出，每条以 ⟦编号⟧ 开头，编号与条数必须与输入完全一致；\n'
       '3) 只输出结果，不要任何解释或空行。\n')


def call(prompt, timeout=600):
    req = urllib.request.Request(
        BASE + '/v1/chat/completions',
        data=json.dumps({'model': MODEL, 'messages': [{'role': 'user', 'content': prompt}],
                         'temperature': 0, 'max_tokens': 4096, 'stream': False}).encode('utf-8'),
        headers={'Content-Type': 'application/json'})
    r = urllib.request.urlopen(req, timeout=timeout)
    return json.loads(r.read().decode('utf-8'))['choices'][0]['message']['content']


def parse_batch(out):
    return {m.group(1): m.group(2).strip()
            for m in re.finditer(r'⟦(\d{4})⟧(.*?)(?=⟦\d{4}⟧|\Z)', out, re.S)}


def llm_one(batch, cache):
    inp = '\n'.join(SENT.format(t['no']) + t['body'] for t in batch)
    try:
        got = parse_batch(call(SYS + '\n输入：\n' + inp))
    except Exception as e:
        return f'{type(e).__name__}:{str(e)[:60]}'
    ok = 0
    for t in batch:
        c = got.get(t['no'], '')
        if c and strip_punct(c) == strip_punct(t['body']):
            cache[t['no']] = c; ok += 1
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--terms', default=os.path.join(ROOT, 'data', 'bingyuan_terms_v3.json'))
    ap.add_argument('--out', default=os.path.join(ROOT, 'data', 'bingyuan_terms_v4.json'))
    ap.add_argument('--engine', choices=['rule', 'llm', 'merge'], default='merge')
    ap.add_argument('--batch', type=int, default=8)
    ap.add_argument('--workers', type=int, default=8)
    ap.add_argument('--limit', type=int, default=0)
    a = ap.parse_args()

    terms = json.load(open(a.terms, encoding='utf-8'))
    cache = json.load(open(CACHE, encoding='utf-8')) if os.path.exists(CACHE) else {}
    print(f'词条 {len(terms)} | 引擎 {a.engine} | 缓存 {len(cache)}')

    if a.engine in ('llm', 'merge'):
        todo = [t for t in terms if t['no'] not in cache and (t.get('body') or '')]
        if a.limit:
            todo = todo[:a.limit]
        batches = [todo[i:i + a.batch] for i in range(0, len(todo), a.batch)]
        t0 = time.time(); total_ok = 0; done = 0
        with ThreadPoolExecutor(max_workers=a.workers) as ex:
            for r in ex.map(lambda b: llm_one(b, cache), batches):
                done += 1; total_ok += r if isinstance(r, int) else 0
                if done % 20 == 0:
                    print(f'  ..{done}/{len(batches)} 批 ok={total_ok} 用时{int(time.time()-t0)}s')
                    json.dump(cache, open(CACHE, 'w', encoding='utf-8'), ensure_ascii=False)
        json.dump(cache, open(CACHE, 'w', encoding='utf-8'), ensure_ascii=False)
        print(f'  LLM 批完成 {done}/{len(batches)} 合格 {total_ok} 用时{int(time.time()-t0)}s')

    n_rule = n_llm = 0
    for t in terms:
        r = rule_punct(t.get('body') or '')
        c = cache.get(t['no'], '')
        if c and strip_punct(c) == strip_punct(t.get('body') or ''):
            t['body'] = c; t['punct_src'] = 'llm'; n_llm += 1
        else:
            t['body'] = r; t['punct_src'] = 'rule'; n_rule += 1
    json.dump(terms, open(a.out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    rep = {'engine': a.engine, 'llm': n_llm, 'rule': n_rule, 'cache': len(cache)}
    json.dump(rep, open(os.path.join(DIST, 'llm_punct_report.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    print('完成:', rep)
    for t in terms[:2]:
        print(f"  {t['no']}[{t['punct_src']}]: {t['body'][:90]}")


if __name__ == '__main__':
    main()
