# -*- coding: utf-8 -*-
"""素问1 神韵版重生成: segs.json + seg_style(rate/pitch) → 远程TTS → ffmpeg合成 → 同步"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

import paramiko

sys.path.insert(0, r'C:\Users\DELL\tcmP\scripts')
from batch_suwen import seg_style

DOCS = Path(r'C:\Users\DELL\tcmP\docs\视频')
VIDEO = Path(r'C:\Users\DELL\textbook-project\drafts\cmrl\figures\book\video')
FF = r'C:\Tools\ffmpeg.exe'
RWORK = r'F:\tcm\tts_work\suwen1'

segs = json.loads((DOCS / 'segs.json').read_text(encoding='utf-8'))
print(f'素问1 segs: {len(segs)} 段')

# ① 远程 TTS（段型参数）
segs_text = []
for i, seg in enumerate(segs, 1):
    voice = 'zh-CN-YunxiNeural' if i in (3, 5, 6, 9, 10) else 'zh-CN-XiaoxiaoNeural'
    text = (seg['orig'] + '。' + seg['talk']).replace('，，', '，').replace('。。', '。')
    rate, pitch = seg_style(i, seg['title'], seg['talk'])
    segs_text.append((i, voice, text, rate, pitch))
    print(f'  段{i} [{seg["title"]}] {rate}/{pitch}')

script = f'''
# -*- coding: utf-8 -*-
import asyncio, edge_tts, os
WORK = r'{RWORK}'
SEGS = {segs_text!r}
async def tts_one(voice, text, rate, pitch, out, retries=6):
    for attempt in range(retries):
        try:
            await edge_tts.Communicate(text, voice, rate=rate, pitch=pitch).save(out)
            if os.path.getsize(out) > 8 * 1024:
                return True
            os.remove(out)
        except Exception:
            await asyncio.sleep(4 * (attempt + 1))
    return False
async def main():
    ok = 0
    for i, voice, text, rate, pitch in SEGS:
        out = os.path.join(WORK, f'p{{i:02d}}.mp3')
        if await tts_one(voice, text, rate, pitch, out):
            ok += 1
        await asyncio.sleep(2)
    print('REMOTE_TTS_DONE', ok, '/', len(SEGS))
asyncio.run(main())
'''
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.0.102', port=22, username='administrator',
            password='Cdy123456', timeout=15)
ssh.exec_command(f'if not exist {RWORK} mkdir {RWORK}')[1].read()
sftp = ssh.open_sftp()
with sftp.open(f'{RWORK}/tts_spirit.py', 'w') as f:
    f.write(script)
sftp.close()
print('远程 TTS（神韵参数）...')
_, out, err = ssh.exec_command(f'python {RWORK}\\tts_spirit.py', timeout=1200)
for ln in out.read().decode('utf-8', errors='ignore').strip().splitlines():
    print('   ', ln)
e = err.read().decode('utf-8', errors='ignore').strip()
if e and 'Error' in e:
    print('ERR:', e[-200:])
# 下载到 v3（复用现有页面）
sftp = ssh.open_sftp()
for i in range(1, 11):
    try:
        sftp.get(f'{RWORK}/p{i:02d}.mp3', str(VIDEO / 'v3' / f'p{i:02d}.mp3'))
    except Exception:
        pass
sftp.close()
ssh.close()
print('下载完成')

# ② ffmpeg 合成（v3 页面 + 新 mp3）
subprocess.run([sys.executable, r'C:\Users\DELL\tcmP\scripts\video_lecture3_ff.py'],
               capture_output=True, text=True, encoding='utf-8', timeout=900)
# ③ 同步
for ext in ('mp4', 'video'):
    shutil.copy2(VIDEO / f'素问01-上古天真论.{ext}', DOCS / f'素问01-上古天真论.{ext}')
print('✅ 素问1 神韵版已同步 docs')
