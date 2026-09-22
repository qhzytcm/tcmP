# -*- coding: utf-8 -*-
"""
S55 平台 LLM 语义矫正（03 清晰底本·2941 单元）
· 走 tcmP 平台 LLM 接线（ollama qwen2.5:7b @192.168.0.102:11434）
· 可续跑：结果逐行追加 data/pdf3_llm_out.jsonl，重跑自动跳过已完成
· 客观护栏：长度比 ∈ [0.80,1.45] 且「新增汉字率」≤ 0.12 → 否则保留原文（记为 rej）
用法： python scripts/s55_llm_correct.py            # 全量
       python scripts/s55_llm_correct.py --limit 50  # 试跑
"""
import os, json, time, argparse, urllib.request
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ocr_fix_rules import fix as refix, CONFIRMED_HEADS     # 白名单护栏 + 回改
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UNITS = os.path.join(ROOT, 'data', 'pdf3_units_v2.json')
OUTL = os.path.join(ROOT, 'data', 'pdf3_llm_out.jsonl')
OLLAMA = os.environ.get('LLM_BASE_CHAT', 'http://192.168.0.102:11434/api/chat')
MODEL = os.environ.get('LLM_MODEL', 'qwen2.5:7b')
PUNCT = set('，。、；：？！「」『』（）《》·—…％%(),.;:?!\'"[]{}<>/\\| \n\t')

# 词目名白名单：这些名字**已考订**，输出中必须保持原样
_WL = '、'.join(CONFIRMED_HEADS.keys()) + '、病源辞典'
SYS = ('你是中医古籍OCR校勘专家。输入是《病源辞典》(1935,吴克潜编)一条目正文的 OCR 结果，'
       '存在形近讹字、串栏错序、缺标点。\n'
       '任务：**仅** ①改正形近讹字 ②理顺明显错序 ③补加标点。\n'
       '铁律：**不得新增原文没有的任何字词**；不得删除内容；不得改动方名/药名/剂量/数字；'
       '不得改写文意或补全你认为"应该"有的内容。保留「病源/病状/治法」标记。\n'
       f'**词目名白名单（已考订，必须原样保留，严禁替换为其它医学术语）**：{_WL}。\n'
       '只输出校正后的正文，无任何解释。')


def chat(text, timeout=900):
    req = urllib.request.Request(OLLAMA, data=json.dumps({
        'model': MODEL, 'stream': False,
        'options': {'temperature': 0, 'num_predict': 1500},
        'messages': [{'role': 'system', 'content': SYS}, {'role': 'user', 'content': text}]
    }, ensure_ascii=False).encode('utf-8'), headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode('utf-8'))['message']['content'].strip()


def guard(src, out):
    s = {c for c in src if c not in PUNCT}
    o = [c for c in out if c not in PUNCT]
    new = [c for c in o if c not in s]
    ratio = len(out) / max(1, len(src))
    nr = len(new) / max(1, len(o))
    ok = (0.80 <= ratio <= 1.45) and (nr <= 0.12) and bool(out)
    return ok, {'ratio': round(ratio, 2), 'new_rate': round(nr, 3),
                'new_sample': ''.join(new[:12])}


# 永久性跳过（不重试）：内容本身不适合送 LLM
PERMANENT_SKIP = {'too_short'}


def done_set():
    """已完成集合。**瞬时故障（URLError/超时/连接重置等）不入集合 → 自动重试**；
    仅永久性跳过项（too_short）与正常产出（ok / 护栏退回）才计入。"""
    ds = set()
    if os.path.exists(OUTL):
        for line in open(OUTL, encoding='utf-8', errors='replace'):
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except Exception:
                continue
            why = r.get('why')
            if why and why not in PERMANENT_SKIP:
                continue                       # 瞬时异常 → 重试
            ds.add(r['i'])
    return ds


LOCK = os.path.join(ROOT, 'data', 'pdf3_llm.lock')


def acquire_lock(force=False):
    """单实例锁：防两个进程并发写同一 JSONL（实测会把文件写坏）。
    Windows 上 os.kill(pid,0) 探测不可靠 → **锁文件存在即拒绝**；
    确需重跑请先删锁或加 --force-unlock。"""
    import atexit
    if os.path.exists(LOCK) and not force:
        try:
            pid = open(LOCK, encoding='utf-8').read().strip()
        except Exception:
            pid = '?'
        print(f'[ABORT] 检测到锁 {LOCK}（pid={pid}）。'
              f'若确认无实例在跑，请删除该锁文件或加 --force-unlock。', flush=True)
        raise SystemExit(2)
    open(LOCK, 'w', encoding='utf-8').write(str(os.getpid()))
    atexit.register(lambda: os.path.exists(LOCK) and os.remove(LOCK))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--limit', type=int, default=None)
    ap.add_argument('--force-unlock', action='store_true')
    ap.add_argument('--only-complete', action='store_true',
                    help='仅矫正「三段齐备」的单元（跳过残缺碎片，约省 40% 时间）')
    ap.add_argument('--redo-nopunct', action='store_true',
                    help='**只重跑「当前最优文本无标点」的单元**（标点补全专项）')
    a = ap.parse_args()
    acquire_lock(force=a.force_unlock)
    units = json.load(open(UNITS, encoding='utf-8'))
    if a.only_complete:
        keep = sum(1 for u in units if all(u['has'].values()))
        print(f'[--only-complete] 仅矫正三段齐备单元：{keep} / {len(units)}', flush=True)
    if a.redo_nopunct:
        # 找出当前最优文本无标点的单元 → 从已完成集合剔除 → 触发重跑
        best = {}
        if os.path.exists(OUTL):
            for line in open(OUTL, encoding='utf-8', errors='replace'):
                line = line.strip()
                if not line:
                    continue
                try:
                    r = json.loads(line)
                except Exception:
                    continue
                if r['i'] not in best or (r.get('ok') and not best[r['i']].get('ok')):
                    best[r['i']] = r
        PUNCT = '，。、；：？！'
        tgt = set()
        for i, u in enumerate(units):
            r = best.get(i)
            t = (r['out'] if (r and r.get('ok')) else u['body']) if r else u['body']
            if sum(t.count(c) for c in PUNCT) == 0 and len(t) >= 8:
                tgt.add(i)
        print(f'[--redo-nopunct] 目标（无标点）单元：{len(tgt)}', flush=True)
        globals()['_REDO'] = tgt
    ds = done_set()
    if globals().get('_REDO'):
        _r = set(globals()['_REDO'])
        ds -= _r                                  # 目标集从「已完成」剔除 → 触发重跑
        print(f'[--redo-nopunct] 已从完成集剔除 {len(_r)} 个 → 待处理 {len(_r)}', flush=True)
    print(f'单元 {len(units)} | 已完成 {len(ds)} | 待处理 {len(units)-len(ds)}', flush=True)
    t0 = time.time(); n = ok = rej = err = 0
    with open(OUTL, 'a', encoding='utf-8') as f:
        for i, u in enumerate(units):
            if i in ds:
                continue
            if globals().get('_REDO') is not None and i not in globals()['_REDO']:
                continue                      # --redo-nopunct：只跑目标集
            if a.only_complete and not all(u['has'].values()):
                continue
            if a.limit and n >= a.limit:
                break
            src = u.get('body') or ''
            if len(src) < 8:
                f.write(json.dumps({'i': i, 'ok': False, 'why': 'too_short', 'out': src},
                                   ensure_ascii=False) + '\n'); f.flush()
                n += 1; rej += 1; continue
            n += 1
            try:
                out = chat(src)
                out = refix(out)          # ③ 后置护栏：白名单回改（如 痃癖→丁奚疳）
                g, info = guard(src, out)
                f.write(json.dumps({'i': i, 'ok': g, 'out': out if g else src, 'g': info},
                                   ensure_ascii=False) + '\n')
                ok += g; rej += (not g)
            except Exception as e:
                f.write(json.dumps({'i': i, 'ok': False, 'why': type(e).__name__,
                                    'out': src}, ensure_ascii=False) + '\n')
                err += 1
            f.flush()
            if n % 10 == 0:
                sp = n / max(1e-9, time.time() - t0)
                print(f'  {n} 条 | ok {ok} rej {rej} err {err} | {sp:.2f} 条/s | '
                      f'剩约 {(len(units)-len(ds)-n)/max(1e-9,sp)/3600:.1f} h', flush=True)
    print(f'DONE 处理 {n} | ok {ok} | 护栏退回 {rej} | 异常 {err} | {time.time()-t0:.0f}s', flush=True)


if __name__ == '__main__':
    main()
