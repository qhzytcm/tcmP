# -*- coding: utf-8 -*-
"""素问1 注音重生成: batch_suwen.remote_tts(注音) → v3 → ffmpeg 合成 → 同步"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, r'C:\Users\DELL\tcmP\scripts')
from batch_suwen import remote_tts

DOCS = Path(r'C:\Users\DELL\tcmP\docs\视频')
VIDEO = Path(r'C:\Users\DELL\textbook-project\drafts\cmrl\figures\book\video')

segs = json.loads((DOCS / 'segs.json').read_text(encoding='utf-8'))
# 删旧远程+本地 mp3（重 TTS 注音版）
import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.0.102', port=22, username='administrator',
            password='Cdy123456', timeout=15)
ssh.exec_command('del F:\\tcm\\tts_work\\suwen1\\p*.mp3')[1].read()
ssh.close()
for p in (VIDEO / 'suwen1').glob('p*.mp3'):
    p.unlink(missing_ok=True)

wdir = remote_tts('1', segs)  # 注音版（含 SSML）
# 拷到 v3
for i in range(1, 11):
    src = VIDEO / 'suwen1' / f'p{i:02d}.mp3'
    if src.exists():
        shutil.copy2(src, VIDEO / 'v3' / f'p{i:02d}.mp3')
# ffmpeg 合成
subprocess.run([sys.executable, r'C:\Users\DELL\tcmP\scripts\video_lecture3_ff.py'],
               capture_output=True, text=True, encoding='utf-8', timeout=900)
for ext in ('mp4', 'video'):
    shutil.copy2(VIDEO / f'素问01-上古天真论.{ext}', DOCS / f'素问01-上古天真论.{ext}')
print('✅ 素问1 注音版完成')
