# -*- coding: utf-8 -*-
"""素问81(解精微论) 补原文锚: 按篇文顺序注入 10 段经文名句 → 重TTS → 重合成"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

DOCS = Path(r'C:\Users\DELL\tcmP\docs\视频')
VIDEO = Path(r'C:\Users\DELL\textbook-project\drafts\cmrl\figures\book\video')

# 解精微论原文锚（按篇文顺序; 医学语义准确, 节选各段核心句）
ORIG_ANCHORS = [
    '雷公请问：哭泣之所以生也，何也？',
    '黄帝曰：夫心者，五脏之专精也；目者，其窍也；华色者，其荣也。是以人有德也，则气和于目。',
    '雷公曰：然则人之所以失涕泣者，何也？',
    '黄帝曰：夫涕泣者，脑之所出也；脑者，阴也。',
    '夫水之精为志，火之精为神，水火相感，神志俱悲，是以目之水生也。',
    '夫志悲者，惋惋则冲阴，冲阴则志去目，志去则神不守精。',
    '水宗者，积水也；积水者，至阴也；至阴者，肾之精也。',
    '是以悲哀则泣下，泣下则水宗竭，水宗竭则精不上传。',
    '夫色见于目者，阳气也；泣出于目者，阴气也。阴阳并走于上，故泣出也。',
    '故上液之道开则泣，其宗气上出于鼻而为涕；此哭泣之所由生也。',
]

f = DOCS / 'segs_suwen81.json'
segs = json.loads(f.read_text(encoding='utf-8'))
for i, s in enumerate(segs):
    if not s.get('orig'):
        s['orig'] = ORIG_ANCHORS[i]
        print(f'段{i+1}: 注入原文「{ORIG_ANCHORS[i][:30]}…」')
f.write_text(json.dumps(segs, ensure_ascii=False, indent=1), encoding='utf-8')
print('segs_suwen81.json 原文锚注入完成')

# 重 TTS（远程删缓存 → batch_auto）
import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.0.102', port=22, username='administrator',
            password='Cdy123456', timeout=15)
ssh.exec_command('del F:\\tcm\\tts_work\\suwen81\\p*.mp3')[1].read()
ssh.close()
print('远程缓存已清')
