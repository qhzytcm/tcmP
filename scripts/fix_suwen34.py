# -*- coding: utf-8 -*-
"""修复素问3/4占位段: 重提取 → 删占位段mp3(远程+本地) → 重TTS+合成"""
import json
import sys
from pathlib import Path

import paramiko

sys.path.insert(0, r'C:\Users\DELL\tcmP\scripts')
from batch_suwen import extract, remote_tts, make_pages, render, sync_docs, CH_NAMES

VIDEO = Path(r'C:\Users\DELL\textbook-project\drafts\cmrl\figures\book\video')
DOCS = Path(r'C:\Users\DELL\tcmP\docs\视频')

for ch in ('3', '4'):
    print(f'\n===== 素问{ch} {CH_NAMES[ch]} =====')
    segs = extract(ch)  # 重新提取（含兜底）
    # 找占位段
    bad = [i for i, s in enumerate(segs, 1)
           if '（讲解）' in s.get('talk', '') or len(s.get('talk', '')) < 40]
    print('占位段:', bad or '无')
    if not bad:
        continue
    # 删占位段 mp3（远程 + 本地）
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('192.168.0.102', port=22, username='administrator',
                password='Cdy123456', timeout=15)
    for i in bad:
        ssh.exec_command(f'del F:\\tcm\\tts_work\\suwen{ch}\\p{i:02d}.mp3')[1].read()
        (VIDEO / f'suwen{ch}' / f'p{i:02d}.mp3').unlink(missing_ok=True)
    ssh.close()
    # 重 TTS（只占位段——remote_tts 全跑但已存在跳过）→ 页面 → 合成
    wdir = remote_tts(ch, segs)
    make_pages(ch, segs, wdir)
    render(ch, wdir)
    sync_docs(ch)
print('✅ 修复完成')
