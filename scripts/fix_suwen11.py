# -*- coding: utf-8 -*-
"""修复素问11 段4: 重提取 → 删段4 mp3(远程+本地) → 重TTS → 重合成 → HTML"""
import json
import sys
from pathlib import Path

import paramiko

sys.path.insert(0, r'C:\Users\DELL\tcmP\scripts')
from auto_segs import auto_extract
from batch_suwen import remote_tts, make_pages, render, CH_NAMES

DOCS = Path(r'C:\Users\DELL\tcmP\docs\视频')
VIDEO = Path(r'C:\Users\DELL\textbook-project\drafts\cmrl\figures\book\video')
ch = '11'

segs = auto_extract('11-五藏别论', ch)
# 段 4 检查
s4 = segs[3]
print(f'段4: 原文{len(s4["orig"])}字 讲解{len(s4["talk"])}字')

# 删段 4 mp3（远程+本地）
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.0.102', port=22, username='administrator', password='Cdy123456', timeout=15)
ssh.exec_command(f'del F:\\tcm\\tts_work\\suwen{ch}\\p04.mp3')[1].read()
ssh.close()
(VIDEO / f'suwen{ch}' / 'p04.mp3').unlink(missing_ok=True)

wdir = remote_tts(ch, segs)  # 只段 4 重 TTS（其余已存在跳过）
make_pages(ch, segs, wdir)
render(ch, wdir)
print('✅ 素问11 修复完成')
