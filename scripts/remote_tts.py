# -*- coding: utf-8 -*-
"""浪潮 A800 远程 TTS（不同公网 IP, 规避本机 edge-tts 限流）
流程: ①远程装 edge-tts → ②上传 10 段文本 → ③远程逐段 TTS → ④下载 mp3
"""
import sys
from pathlib import Path

import paramiko

sys.path.insert(0, r'C:\Users\DELL\tcmP\scripts')
from video_lecture3 import SEGS

REMOTE = dict(hostname='192.168.0.102', port=22, username='administrator',
              password='Cdy123456')
RWORK = r'F:\tcm\tts_work'
LOCAL = Path(r'C:\Users\DELL\textbook-project\drafts\cmrl\figures\book\video\v3')

# 生成 10 段文本（远程脚本内嵌）
segs_text = []
for i, seg in enumerate(SEGS, 1):
    orig, note, talk = seg[3], seg[4], seg[5]
    voice = 'zh-CN-YunxiNeural' if i in (3, 5, 6, 9, 10) else 'zh-CN-XiaoxiaoNeural'
    segs_text.append((i, voice, orig + '。' + talk))

# 远程 TTS 脚本（Python 3.8, edge-tts）
remote_script = f'''
# -*- coding: utf-8 -*-
import asyncio, edge_tts, os, sys, json
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
            await asyncio.sleep(5 * (attempt + 1))
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
    print('REMOTE_TTS_DONE', ok, '/', len(SEGS))

asyncio.run(main())
'''

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(**REMOTE, timeout=15)

# ① 装 edge-tts
print('① 安装远程 edge-tts ...')
_, out, err = ssh.exec_command(
    'python -m pip install edge-tts --quiet 2>&1 | tail -1', timeout=300)
o = out.read().decode('utf-8', errors='ignore').strip()
print('   ', o[:120] if o else '已装')

# ② 上传脚本
sftp = ssh.open_sftp()
try:
    sftp.stat(RWORK)
except IOError:
    ssh.exec_command(f'mkdir {RWORK}')[1].read()
with sftp.open(f'{RWORK}/tts_all.py', 'w') as f:
    f.write(remote_script)
sftp.close()
print('② 脚本已上传')

# ③ 远程执行
print('③ 远程逐段 TTS（新 IP 无限流）...')
_, out, err = ssh.exec_command(f'python {RWORK}\\tts_all.py', timeout=900)
lines = out.read().decode('utf-8', errors='ignore').strip().splitlines()
for ln in lines:
    print('   ', ln)
e = err.read().decode('utf-8', errors='ignore').strip()
if e and 'Error' in e:
    print('ERR:', e[-300:])

# ④ 下载 mp3
print('④ 下载 mp3 ...')
sftp = ssh.open_sftp()
n = 0
for i in range(1, 11):
    rp = f'{RWORK}/p{i:02d}.mp3'
    lp = LOCAL / f'p{i:02d}.mp3'
    try:
        sftp.get(rp, str(lp))
        n += 1
    except Exception:
        pass
sftp.close()
ssh.close()
print(f'✅ 下载 {n}/10 段 mp3')
