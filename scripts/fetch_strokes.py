# -*- coding: utf-8 -*-
"""下载 Unihan kTotalStrokes → data/strokes.json（笔画数表）"""
import os, json, io, urllib.request, zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'data', 'strokes.json')
URL = 'https://www.unicode.org/Public/UCD/latest/ucd/Unihan.zip'

if os.path.exists(OUT):
    print('已存在:', OUT, os.path.getsize(OUT))
    raise SystemExit(0)

print('下载', URL)
data = urllib.request.urlopen(URL, timeout=120).read()
print('zip bytes:', len(data))
z = zipfile.ZipFile(io.BytesIO(data))
name = [n for n in z.namelist() if 'IRGSources' in n][0]
print('读取', name)
strokes = {}
with z.open(name) as f:
    for line in io.TextIOWrapper(f, encoding='utf-8'):
        if 'kTotalStrokes' not in line or line.startswith('#'):
            continue
        parts = line.rstrip('\n').split('\t')
        if len(parts) < 3:
            continue
        cp = parts[0]
        if not cp.startswith('U+'):
            continue
        ch = chr(int(cp[2:], 16))
        v = parts[2].split()          # 可为 "8" 或 "8 9"(简繁异体)
        try:
            strokes[ch] = int(v[0])
        except Exception:
            pass
json.dump(strokes, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False)
print('笔画表条目:', len(strokes), '→', OUT)


def stroke_of(ch):
    return strokes.get(ch)


if __name__ == '__main__':
    for t in '病源辞典中风寒热':
        print(t, strokes.get(t))
