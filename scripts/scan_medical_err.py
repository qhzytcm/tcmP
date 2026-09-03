# -*- coding: utf-8 -*-
"""扫描已生成 segs 的医学语义错误（脉学/术语/数值要素归类）"""
import json
import re
from pathlib import Path

D = Path(r'C:\Users\DELL\tcmP\docs\视频')

# ① 脉学语义检查（SW17-19: 素问17/18/19）
print('===== 素问 17/18/19 脉学语义扫描 =====')
for ch in (17, 18, 19):
    f = D / f'segs_suwen{ch}.json'
    if not f.exists():
        continue
    segs = json.loads(f.read_text(encoding='utf-8'))
    print(f'\n--- 素问{ch} ---')
    for i, s in enumerate(segs, 1):
        text = s['orig'] + '。' + s['talk']
        # 脉动/呼吸/频数相关
        if any(k in text for k in ('脉再动', '脉一动', '呼吸定息', '一呼', '一吸', '脉五动', '再脉')):
            print(f'  段{i}: {text[:150]}')
            # 要素检查: 频数句是否混入其他要素（节律/长短/深浅）
            if '节律' in text or '结代' in text or '短脉' in text or '覆脉' in text or '浮' in text or '沉' in text:
                if '脉再动' in text or '呼吸定息' in text:
                    print('    ⚠ 频数语义段混入其他要素词（需核对）')

# ② 全部 19 篇术语/数值抽查（常见错误模式）
print('\n===== 全部篇 术语/数值异常模式 =====')
pat_bad = [
    (r'脉[一二三四五六七八九十]?动', '脉动数'),
    (r'一呼[^，。]*脉', '呼吸-脉关系'),
    (r'呼吸定息[^，。]*', '呼吸定息'),
]
for ch in range(1, 20):
    f = D / f'segs_suwen{ch}.json' if ch != 1 else D / 'segs.json'
    if not f.exists():
        continue
    segs = json.loads(f.read_text(encoding='utf-8'))
    for i, s in enumerate(segs, 1):
        text = s['orig'] + '。' + s['talk']
        for pat, label in pat_bad:
            for m in re.finditer(pat, text):
                print(f'  素问{ch} 段{i} [{label}]: {m.group(0)[:60]}')
