# -*- coding: utf-8 -*-
"""诊断远程 ffmpeg 合成失败原因"""
import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('192.168.0.102', port=22, username='administrator',
          password='Cdy123456', timeout=10)

# 检查素材与 ffmpeg
for cmd in ('dir F:\\tcm\\video_work\\seg01.*',
            'ffmpeg -version 2>&1 | findstr /i version',
            'ffmpeg -y -loop 1 -i F:\\tcm\\video_work\\seg01.png -i F:\\tcm\\video_work\\seg01.mp3 -c:v h264_nvenc -preset p4 -pix_fmt yuv420p -r 24 -c:a aac -shortest F:\\tcm\\video_work\\t1.mp4'):
    _, out, err = c.exec_command(cmd, timeout=90)
    o = out.read().decode('utf-8', errors='ignore').strip()
    e = err.read().decode('utf-8', errors='ignore').strip()
    print(f'$ {cmd[:80]}...')
    print('OUT:', o[-300:] if o else '(none)')
    print('ERR:', e[-400:] if e else '(none)')
    print('---')
c.close()
