# -*- coding: utf-8 -*-
"""修复浪潮 sshd_config (sftp 子系统绝对路径) + 重启 sshd"""
import paramiko
import time

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('192.168.0.102', port=22, username='administrator',
          password='Cdy123456', timeout=10)

ps = (r"$f='C:\ProgramData\ssh\sshd_config'; "
      r"$t=Get-Content $f -Raw; "
      r"$t=$t -replace 'Subsystem\s+sftp\s+.*', 'Subsystem sftp C:\Windows\System32\OpenSSH\sftp-server.exe'; "
      r"Set-Content $f $t -Encoding ascii; "
      r"Get-Content $f | Select-String -Pattern 'Subsystem'")
_, out, err = c.exec_command(f'powershell -Command "{ps}"', timeout=30)
print('修改后:', out.read().decode('utf-8', errors='ignore').strip())
e = err.read().decode('utf-8', errors='ignore').strip()
if e:
    print('ERR:', e[:200])

# 重启 sshd（新连接执行, 避免断当前）
c.close()
time.sleep(1)
c2 = paramiko.SSHClient()
c2.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c2.connect('192.168.0.102', port=22, username='administrator',
           password='Cdy123456', timeout=10)
_, out, err = c2.exec_command('powershell -Command "Restart-Service sshd -Force"', timeout=60)
out.read(); err.read()
c2.close()
print('sshd 已重启')

# 测试 SFTP
time.sleep(3)
c3 = paramiko.SSHClient()
c3.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c3.connect('192.168.0.102', port=22, username='administrator',
           password='Cdy123456', timeout=10)
try:
    sftp = c3.open_sftp()
    sftp.listdir('/')
    print('SFTP 协商: ✅ 成功')
    sftp.close()
except Exception as ex:
    print('SFTP 协商: ❌', type(ex).__name__, str(ex)[:150])
c3.close()
