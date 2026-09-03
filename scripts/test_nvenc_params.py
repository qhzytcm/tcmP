# -*- coding: utf-8 -*-
"""测试 A800 NVENC 参数组合"""
import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('192.168.0.102', port=22, username='administrator',
          password='Cdy123456', timeout=10)

cmds = [
    # 变体1: 默认 preset
    'ffmpeg -y -loop 1 -i F:\\tcm\\video_work\\seg01.png -i F:\\tcm\\video_work\\seg01.mp3 -c:v h264_nvenc -pix_fmt yuv420p -r 24 -c:a aac -shortest F:\\tcm\\video_work\\t1.mp4',
    # 变体2: libx264 对照（确认素材/链路 OK）
    'ffmpeg -y -loop 1 -i F:\\tcm\\video_work\\seg01.png -i F:\\tcm\\video_work\\seg01.mp3 -c:v libx264 -pix_fmt yuv420p -r 24 -c:a aac -shortest F:\\tcm\\video_work\\t2.mp4',
]
for cmd in cmds:
    _, out, err = c.exec_command(cmd, timeout=90)
    o = out.read().decode('utf-8', errors='ignore').strip()
    e = err.read().decode('utf-8', errors='ignore').strip()
    ok = 'Conversion failed' not in e and 'error' not in e.lower()
    print(f'{"✅" if ok else "❌"} {cmd[20:70]}...')
    if not ok:
        lines = [ln for ln in e.splitlines() if 'error' in ln.lower() or 'nvdec' in ln.lower() or 'nvenc' in ln.lower()]
        print('  ', ' | '.join(lines[-2:])[:250])
    # 检查输出
    _, out2, _ = c.exec_command('dir F:\\tcm\\video_work\\t*.mp4', timeout=30)
    print('  ', out2.read().decode('utf-8', errors='ignore').strip().splitlines()[-3:])
c.close()
