# -*- coding: utf-8 -*-
"""测试 p01 文本 TTS（定位失败原因）"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, r'C:\Users\DELL\tcmP\scripts')
from video_lecture3 import SEGS

orig, note, talk = SEGS[0][3], SEGS[0][4], SEGS[0][5]
tts_text = orig + '。' + talk
print(f'p01 文本长度: {len(tts_text)} 字')
print('文本:', tts_text[:80], '...')


async def go():
    import edge_tts
    out = Path(r'C:\Users\DELL\AppData\Local\Temp\p01_test.mp3')
    try:
        await edge_tts.Communicate(tts_text, 'zh-CN-XiaoxiaoNeural', rate='-3%').save(str(out))
        print('完整文本 OK:', out.stat().st_size, 'B')
    except Exception as e:
        print('完整文本失败:', type(e).__name__, str(e)[:150])
        # 拆分测试: 原文 / 讲解 分开
        for label, part in (('原文', orig), ('讲解', talk)):
            try:
                p = Path(rf'C:\Users\DELL\AppData\Local\Temp\p01_{label}.mp3')
                await edge_tts.Communicate(part, 'zh-CN-XiaoxiaoNeural', rate='-3%').save(str(p))
                print(f'{label} 段 OK:', p.stat().st_size, 'B')
            except Exception as e2:
                print(f'{label} 段失败:', type(e2).__name__, str(e2)[:120])


asyncio.run(go())
