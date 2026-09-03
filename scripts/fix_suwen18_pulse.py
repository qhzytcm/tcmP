# -*- coding: utf-8 -*-
"""纠错: 素问18 段1 脉学频数语义精准化（2+1+2=5 分解 + 要素澄清）"""
import json
from pathlib import Path

D = Path(r'C:\Users\DELL\tcmP\docs\视频')
f = D / 'segs_suwen18.json'
segs = json.loads(f.read_text(encoding='utf-8'))

# 段 1 原 talk
s1 = segs[0]
print('段1 原 talk 前 200 字:')
print(s1['talk'][:200])

# 注入准确频数语义（保留原内容, 前缀补充）
clarify = ('这里先明确脉动的频数语义：人一呼，脉跳动两次；一吸，脉跳动两次；'
           '呼吸转换的定息之间，脉跳动一次。合起来，一呼再动两次，加定息一次，'
           '加一吸再动两次，共五次脉动，这就是平人脉搏跳动的频数，古称"呼吸定息脉五动"。'
           '请注意，这一语义只涉及脉搏的频数要素，并不涉及脉搏的其他要素——'
           '如节律是否整齐、有无结代；脉的长短是否恒定、有无短脉覆脉；'
           '脉的深浅是沉是浮——那些是另外的脉学要素，不可混为一谈。')

if '脉五动' not in s1['talk'] or '两次' not in s1['talk']:
    s1['talk'] = clarify + s1['talk']
    print('\n✅ 段1 已注入频数分解与要素澄清')
else:
    print('\n段1 已含频数语义, 无需注入')

f.write_text(json.dumps(segs, ensure_ascii=False, indent=1), encoding='utf-8')
print('segs_suwen18.json 已更新')
