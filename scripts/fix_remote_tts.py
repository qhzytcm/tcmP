# -*- coding: utf-8 -*-
"""修复远程 edge-tts 安装（python -m pip + 验证）"""
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.0.102', port=22, username='administrator',
            password='Cdy123456', timeout=15)

cmds = [
    ('python 路径', 'where python'),
    ('安装 edge-tts', 'python -m pip install edge-tts 2>&1 | findstr /i "successfully error"'),
    ('验证', 'python -c "import edge_tts; print(edge_tts.__version__ if hasattr(edge_tts, \\"__version__\\") else \\"OK\\")" 2>&1'),
]
for label, cmd in cmds:
    _, out, err = ssh.exec_command(cmd, timeout=300)
    o = out.read().decode('utf-8', errors='ignore').strip()
    e = err.read().decode('utf-8', errors='ignore').strip()
    print(f'[{label}] {o[:200] if o else "(无输出)"}')
    if e and label == '验证':
        print('   ERR:', e[-200:])
ssh.close()
