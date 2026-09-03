# -*- coding: utf-8 -*-
"""连接浪潮 192.168.0.102 确认 A800 GPU"""
import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    c.connect('192.168.0.102', port=22, username='administrator',
              password='Cdy123456', timeout=10)
    for cmd in ('nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader',
                'ffmpeg -hide_banner -encoders 2>nul | findstr nvenc'):
        _, out, err = c.exec_command(cmd, timeout=30)
        print(f'$ {cmd}')
        print(out.read().decode('utf-8', errors='ignore').strip()[:400])
        print(err.read().decode('utf-8', errors='ignore').strip()[:200])
    c.close()
except Exception as e:
    print('连接失败:', type(e).__name__, str(e)[:200])
