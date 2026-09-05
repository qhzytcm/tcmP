# -*- coding: utf-8 -*-
"""远程测试 edge-tts SSML phoneme 注音（脏 zàng）"""
import paramiko

script = '''# -*- coding: utf-8 -*-
import asyncio, edge_tts, os
async def main():
    # 对照: 普通文本
    await edge_tts.Communicate('五脏六腑，心肝脾肺肾。', 'zh-CN-XiaoxiaoNeural', rate='-3%').save(r'F:\\tcm\\tts_work\\t1.mp3')
    # SSML phoneme (sapi 音标, 4=去声)
    ssml = '<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="zh-CN">' \\
           '<phoneme alphabet="sapi" ph="zang 4">脏</phoneme>腑，' \\
           '<phoneme alphabet="sapi" ph="zang 4">五脏</phoneme>六腑。</speak>'
    await edge_tts.Communicate(ssml, 'zh-CN-XiaoxiaoNeural', rate='-3%').save(r'F:\\tcm\\tts_work\\t2.mp3')
    print('S1', os.path.getsize(r'F:\\tcm\\tts_work\\t1.mp3'))
    print('S2', os.path.getsize(r'F:\\tcm\\tts_work\\t2.mp3'))
asyncio.run(main())
'''

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.0.102', port=22, username='administrator',
            password='Cdy123456', timeout=15)
sftp = ssh.open_sftp()
with sftp.open('F:/tcm/tts_work/phoneme_test.py', 'w') as f:
    f.write(script)
sftp.close()
_, out, err = ssh.exec_command('python F:\\tcm\\tts_work\\phoneme_test.py', timeout=180)
print(out.read().decode('utf-8', errors='ignore'))
e = err.read().decode('utf-8', errors='ignore')
if e:
    print('ERR:', e[-400:])
ssh.close()
