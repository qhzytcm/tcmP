# -*- coding: utf-8 -*-
"""检查 A800 编码器引擎状态"""
import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('192.168.0.102', port=22, username='administrator',
          password='Cdy123456', timeout=10)
for cmd in ('nvidia-smi -q -d ENCODER 2>&1 | findstr /i "encoder video"',
            'nvidia-smi 2>&1 | findstr /i "A800"',
            'ffmpeg -hide_banner -h encoder=h264_nvenc 2>&1 | findstr /i "supported"'):
    _, out, err = c.exec_command(cmd, timeout=60)
    o = out.read().decode('utf-8', errors='ignore').strip()
    print(f'$ {cmd[:60]}')
    print(o[:400] if o else '(no output)')
    print('---')
c.close()
