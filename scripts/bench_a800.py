# -*- coding: utf-8 -*-
"""A800 CUDA 基准: 上传脚本到浪潮执行"""
import paramiko

BENCH = r'''
import torch, time
print('PyTorch', torch.__version__, '| CUDA', torch.cuda.is_available())
x = torch.randn(8192, 8192, device='cuda')
y = torch.randn(8192, 8192, device='cuda')
torch.cuda.synchronize()
t0 = time.time()
for _ in range(5):
    z = x @ y
torch.cuda.synchronize()
dt = (time.time() - t0) / 5
print('A800 matmul 8192^2: %.1f ms/次 (%.1f TFLOPS)' % (dt * 1000, 2 * 8192 ** 3 / dt / 1e12))
'''

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('192.168.0.102', port=22, username='administrator',
          password='Cdy123456', timeout=15)
sftp = c.open_sftp()
with sftp.open(r'F:\tcm\video_work\bench.py', 'w') as f:
    f.write(BENCH)
sftp.close()
_, out, err = c.exec_command('python F:\\tcm\\video_work\\bench.py', timeout=180)
print(out.read().decode('utf-8', errors='ignore').strip())
e = err.read().decode('utf-8', errors='ignore').strip()
if e:
    print('ERR:', e[:300])
c.close()
