# -*- coding: utf-8 -*-
"""深度医学语义核查: 全部已生成篇 要素混淆/术语错误"""
import json
import re
from pathlib import Path

D = Path(r'C:\Users\DELL\tcmP\docs\视频')
issues = []

for ch in range(1, 20):
    f = D / f'segs_suwen{ch}.json' if ch != 1 else D / 'segs.json'
    if not f.exists():
        continue
    segs = json.loads(f.read_text(encoding='utf-8'))
    for i, s in enumerate(segs, 1):
        text = (s.get('orig', '') + '。' + s.get('talk', ''))
        # ① 脉学: 频数句是否混入其他要素断言
        if ('脉' in text and ('动' in text)) and ('结代' in text or '覆脉' in text):
            if '频数' not in text and '要素' not in text:
                issues.append(f'素问{ch}段{i}: 脉动句混入结代/覆脉(无要素澄清)')
        # ② 数值锚点核对（常见: 女子七/男子八/五动/三动）
        if re.search(r'脉[五三二一]动', text) and re.search(r'节律|整齐', text):
            issues.append(f'素问{ch}段{i}: 脉动数与节律同句(疑混淆)')
        # ③ 占位/异常
        if '（讲解）' in text or len(s.get('talk', '')) < 20:
            issues.append(f'素问{ch}段{i}: 讲解占位/过短')
        # ④ 术语重复堆叠（异常长无标点）
        if len(s.get('talk', '')) > 0 and '。' not in s['talk'][:80] and len(s['talk']) > 150:
            issues.append(f'素问{ch}段{i}: 长句无标点(语义流断裂)')

print(f'核查 19 篇完成, 发现 {len(issues)} 项:')
for it in issues:
    print('  -', it)
