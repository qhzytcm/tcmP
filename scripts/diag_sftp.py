# -*- coding: utf-8 -*-
"""诊断浪潮 SFTP 子系统 + 尝试 sftp-server"""
import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('192.168.0.102', port=22, username='administrator',
          password='Cdy123456', timeout=10)
for cmd in ('where sftp-server', 'type C:\\ProgramData\\ssh\\sshd_config | findstr -i sftp',
            'net start | findstr -i ssh'):
    _, out, err = c.exec_command(cmd, timeout=30)
    print(f'$ {cmd}')
    o = out.read().decode('utf-8', errors='ignore').strip()
    e = err.read().decode('utf-8', errors='ignore').strip()
    print(o[:300] if o else '(no output)')
    if e:
        print('ERR:', e[:200])
c.close()
