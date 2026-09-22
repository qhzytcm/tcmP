# -*- coding: utf-8 -*-
"""
S37 用本地 ollama 云端模型逐条提取第二份扫描件中的残条正文
输入 data/pdf2_repair.json → 输出 data/pdf2_out.json（+ 报告）
"""
import os, json, re, time, urllib.request
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B = 'http://192.168.0.102:11434'
MODEL = os.environ.get('OLLAMA_MODEL', 'qwen2.5:7b')   # 本地模型免鉴权；:cloud 需 token（401）

SYS = ("你是中医古籍整理专家。给你一段 1935 年繁体竖排双栏扫描件的 OCR 文本（繁简混排、多条目交错），"
       "你要从中提取指定词目的内容，改写成现代汉语简体中文，保留「病源：…病状：…治法：…」三段结构。"
       "严禁编造原文没有的方药/剂量/治法。只输出该词目的正文，不要任何解释。")


def ask(head, source, cur):
    user = (f"词目：{head}\n\n该页 OCR 原文（多条目交错，请只取属于「{head}」的语句）：\n{source}\n\n"
            f"（参考：该条在第一份扫描件中的残损正文为「{cur}」）\n\n"
            f"请输出「{head}」的正文，采用「病源：…病状：…治法：…」三段（源中无对应段则不硬加）。"
            f"若该词目在原文中确实无内容，原样输出：{cur}〔第二份扫描件亦未得〕")
    payload = json.dumps({"model": MODEL, "messages": [{"role": "system", "content": SYS},
                                                       {"role": "user", "content": user}],
                          "temperature": 0.2, "stream": False}).encode()
    req = urllib.request.Request(B + '/v1/chat/completions', data=payload,
                                 headers={'Content-Type': 'application/json'})
    r = urllib.request.urlopen(req, timeout=600)
    return json.loads(r.read())['choices'][0]['message']['content'].strip()


def main():
    payload = json.load(open(os.path.join(ROOT, 'data', 'pdf2_repair.json'), encoding='utf-8'))
    out = {}
    t0 = time.time()
    for i, p in enumerate(payload):
        try:
            txt = ask(p['head'], p['source'], p['cur_body'])
            txt = re.sub(r'^(正文[:：]|输出[:：])', '', txt).strip()
            out[p['no']] = {'head': p['head'], 'body': txt}
            print(f"[{i+1}/{len(payload)}] {p['no']} {p['head'][:12]} → {len(txt)} 字 | {int(time.time()-t0)}s", flush=True)
        except Exception as e:
            print(f"[{i+1}/{len(payload)}] {p['no']} ERR {type(e).__name__} {str(e)[:80]}", flush=True)
            out[p['no']] = {'head': p['head'], 'body': p['cur_body']}
    json.dump(out, open(os.path.join(ROOT, 'data', 'pdf2_out.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    print(f'完成 {len(out)} 条，用时 {time.time()-t0:.0f}s')


if __name__ == '__main__':
    main()
