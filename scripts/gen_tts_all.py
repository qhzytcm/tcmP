# -*- coding: utf-8 -*-
"""分段独立 TTS（每段间隔 20s 规避限流）+ 失败重试"""
import asyncio
import sys
import time
from pathlib import Path

sys.path.insert(0, r'C:\Users\DELL\tcmP\scripts')
from video_lecture3 import SEGS, tts_one

WORK = Path(r'C:\Users\DELL\textbook-project\drafts\cmrl\figures\book\video\v3')


async def gen_one(i, text, voice):
    mp3 = WORK / f'p{i:02d}.mp3'
    if mp3.exists() and mp3.stat().st_size > 8 * 1024:
        print(f'  p{i:02d} 已存在, 跳过')
        return True
    for attempt in range(3):
        try:
            await tts_one(voice, text, mp3, retries=4)
            print(f'  p{i:02d} OK ({mp3.stat().st_size // 1024}KB)')
            return True
        except Exception as e:
            print(f'  p{i:02d} 第{attempt + 1}轮失败: {type(e).__name__}; 等60s')
            time.sleep(60)
    print(f'  p{i:02d} ❌ 最终失败')
    return False


def main():
    voices = {i: ('zh-CN-YunxiNeural' if i in (3, 5, 6, 9, 10) else 'zh-CN-XiaoxiaoNeural')
              for i in range(1, 11)}
    ok = True
    for i, seg in enumerate(SEGS, 1):
        orig, note, talk = seg[3], seg[4], seg[5]
        text = orig + '。' + talk
        print(f'段 {i}: {len(text)}字')
        if not asyncio.run(gen_one(i, text, voices[i])):
            ok = False
        time.sleep(20)  # 段间 20s 间隔
    print('全部完成:', '✅' if ok else '⚠ 有失败')


if __name__ == '__main__':
    main()
