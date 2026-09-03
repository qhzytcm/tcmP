# -*- coding: utf-8 -*-
"""清洗后批量重生成: 删mp3(远程+本地) → 重TTS(段型) → 合成 → 同步
用法: python regen_batch.py 2,3,9,11
"""
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

chs = sys.argv[1].split(',')
for ch in chs:
    seg_file = DOCS / ('segs.json' if ch == '1' else f'segs_suwen{ch}.json')
    if not seg_file.exists():
        print(f'跳过 {ch}')
        continue
    segs = json.loads(seg_file.read_text(encoding='utf-8'))
    # 删全部 mp3（远程+本地）
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('192.168.0.102', port=22, username='administrator',
                password='Cdy123456', timeout=15)
    ssh.exec_command(f'del F:\\tcm\\tts_work\\suwen{ch}\\p*.mp3')[1].read()
    ssh.close()
    for p in (VIDEO / f'suwen{ch}').glob('p*.mp3'):
        p.unlink()
    print(f'素问{ch}: 缓存已清, 重 TTS ...')
    wdir = remote_tts(ch, segs)
    make_pages(ch, segs, wdir)
    render(ch, wdir)
    name = f'素问{ch}-{CH_NAMES[ch]}'
    shutil.copy2(VIDEO / f'{name}.mp4', DOCS / f'{name}.mp4')
    print(f'✅ 素问{ch} 重生成完成')
print('批处理完成')
