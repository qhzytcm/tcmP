# -*- coding: utf-8 -*-
"""纠错重生成: 素问1/4/6/18（受影响段重TTS + 重合成 + 同步）"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

import paramiko

sys.path.insert(0, r'C:\Users\DELL\tcmP\scripts')
from batch_suwen import remote_tts, make_pages, render, CH_NAMES

DOCS = Path(r'C:\Users\DELL\tcmP\docs\视频')
VIDEO = Path(r'C:\Users\DELL\textbook-project\drafts\cmrl\figures\book\video')

# 受影响段: 篇 → [段号]
AFFECTED = {'1': [3], '4': [6, 7, 9], '6': [4], '18': [1]}

for ch, segs_list in AFFECTED.items():
    # 读取 segs（素问1 用 segs.json）
    seg_file = DOCS / 'segs.json' if ch == '1' else DOCS / f'segs_suwen{ch}.json'
    segs = json.loads(seg_file.read_text(encoding='utf-8'))

    # 删受影响段 mp3（远程 + 本地 suwen{ch}）
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('192.168.0.102', port=22, username='administrator',
                password='Cdy123456', timeout=15)
    for i in segs_list:
        ssh.exec_command(f'del F:\\tcm\\tts_work\\suwen{ch}\\p{i:02d}.mp3')[1].read()
        (VIDEO / f'suwen{ch}' / f'p{i:02d}.mp3').unlink(missing_ok=True)
    ssh.close()

    # 重 TTS（段型参数, 只受影响段重生成）
    wdir = remote_tts(ch, segs)

    if ch == '1':
        # 素问1 用 v3 页面 + video_lecture3_ff 合成
        # 拷贝 mp3 到 v3（remote_tts 下载到 suwen1——v3 用）
        for i in range(1, 11):
            src = VIDEO / 'suwen1' / f'p{i:02d}.mp3'
            if src.exists():
                shutil.copy2(src, VIDEO / 'v3' / f'p{i:02d}.mp3')
        subprocess.run([sys.executable, r'C:\Users\DELL\tcmP\scripts\video_lecture3_ff.py'],
                       capture_output=True, text=True, encoding='utf-8', timeout=900)
        for ext in ('mp4', 'video'):
            shutil.copy2(VIDEO / f'素问01-上古天真论.{ext}', DOCS / f'素问01-上古天真论.{ext}')
        print(f'✅ 素问1 重生成完成')
    else:
        make_pages(ch, segs, wdir)
        render(ch, wdir)
        name = f'素问{ch}-{CH_NAMES[ch]}'
        shutil.copy2(VIDEO / f'{name}.mp4', DOCS / f'{name}.mp4')
        print(f'✅ 素问{ch} 重生成完成')
print('全部纠错重生成完成')
