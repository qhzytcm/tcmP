# -*- coding: utf-8 -*-
"""登录浪潮 → A800 状态 → CUDA 算力验证"""
import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('192.168.0.102', port=22, username='administrator',
          password='Cdy123456', timeout=15)
print('✅ 局域网 SSH 登录浪潮 192.168.0.102 成功')

cmds = [
    ('A800 状态', 'nvidia-smi --query-gpu=name,memory.used,memory.total,utilization.gpu --format=csv,noheader'),
    ('Python 环境', 'python --version 2>&1'),
    ('PyTorch CUDA', 'python -c "import torch; print(torch.__version__, torch.cuda.is_available(), torch.cuda.get_device_name(0))" 2>&1'),
]
for label, cmd in cmds:
    _, out, err = c.exec_command(cmd, timeout=60)
    o = out.read().decode('utf-8', errors='ignore').strip()
    e = err.read().decode('utf-8', errors='ignore').strip()
    print(f'[{label}] {o[:200] if o else e[:200]}')
c.close()
