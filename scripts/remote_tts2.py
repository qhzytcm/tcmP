# -*- coding: utf-8 -*-
"""浪潮 A800 远程 TTS（数据源: segs.json 原文+讲解; 远程 IP 无限流）"""
import json
import sys
from pathlib import Path

import paramiko

SEGS = json.loads(Path(r'C:\Users\DELL\tcmP\docs\视频\segs.json').read_text(encoding='utf-8'))
REMOTE = dict(hostname='192.168.0.102', port=22, username='administrator',
              password='Cdy123456')
RWORK = r'F:\tcm\tts_work'
LOCAL = Path(r'C:\Users\DELL\textbook-project\drafts\cmrl\figures\book\video\v3')

# 十段: (i, voice, 原文+讲解文本)
segs_text = []
for i, seg in enumerate(SEGS, 1):
    voice = 'zh-CN-YunxiNeural' if i in (3, 5, 6, 9, 10) else 'zh-CN-XiaoxiaoNeural'
    text = (seg['orig'] + '。' + seg['talk']).replace('，，', '，').replace('。。', '。')
    segs_text.append((i, voice, text))
    print(f'段 {i} [{seg["title"]}] {len(text)}字')

remote_script = f'''
# -*- coding: utf-8 -*-
import asyncio, edge_tts, os
WORK = r'{RWORK}'
SEGS = {segs_text!r}

async def tts_one(voice, text, out, retries=6):
    for attempt in range(retries):
        try:
            await edge_tts.Communicate(text, voice, rate='-3%').save(out)
            if os.path.getsize(out) > 8 * 1024:
                return True
            os.remove(out)
        except Exception as e:
            print(f'  retry {{attempt+1}}: {{type(e).__name__}}')
            await asyncio.sleep(4 * (attempt + 1))
    return False

async def main():
    ok = 0
    for i, voice, text in SEGS:
        out = os.path.join(WORK, f'p{{i:02d}}.mp3')
        if os.path.exists(out) and os.path.getsize(out) > 8 * 1024:
            print(f'p{{i:02d}} 已存在'); ok += 1; continue
        if await tts_one(voice, text, out):
            print(f'p{{i:02d}} OK {{os.path.getsize(out)//1024}}KB'); ok += 1
        else:
            print(f'p{{i:02d}} FAIL')
        await asyncio.sleep(3)
    print('REMOTE_TTS_DONE', ok, '/', len(SEGS))

asyncio.run(main())
'''

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(**REMOTE, timeout=15)
sftp = ssh.open_sftp()
try:
    sftp.stat(RWORK)
except IOError:
    ssh.exec_command(f'mkdir {RWORK}')[1].read()
with sftp.open(f'{RWORK}/tts_all.py', 'w') as f:
    f.write(remote_script)
sftp.close()

print('远程逐段 TTS ...')
_, out, err = ssh.exec_command(f'python {RWORK}\\tts_all.py', timeout=1200)
for ln in out.read().decode('utf-8', errors='ignore').strip().splitlines():
    print('   ', ln)
e = err.read().decode('utf-8', errors='ignore').strip()
if e and 'Error' in e:
    print('ERR:', e[-300:])

print('下载 mp3 ...')
sftp = ssh.open_sftp()
n = 0
for i in range(1, 11):
    try:
        sftp.get(f'{RWORK}/p{i:02d}.mp3', str(LOCAL / f'p{i:02d}.mp3'))
        n += 1
    except Exception:
        pass
sftp.close()
ssh.close()
print(f'✅ 下载 {n}/10 段')
