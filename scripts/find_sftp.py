# -*- coding: utf-8 -*-
"""查找浪潮 sftp-server.exe 路径"""
import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('192.168.0.102', port=22, username='administrator',
          password='Cdy123456', timeout=10)
for cmd in ('dir /s /b C:\\Windows\\System32\\OpenSSH\\sftp-server.exe 2>nul',
            'dir /s /b "C:\\Program Files\\OpenSSH\\sftp-server.exe" 2>nul',
            'where /r C:\\ sftp-server.exe 2>nul | findstr /i sftp'):
    _, out, err = c.exec_command(cmd, timeout=60)
    o = out.read().decode('utf-8', errors='ignore').strip()
    print(f'$ {cmd}')
    print(o[:300] if o else '(no output)')
c.close()
