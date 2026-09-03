# -*- coding: utf-8 -*-
"""video_lecture.py — 讲课模式视频生成（素问01-上古天真论）
特点: 每幕按句拆分为讲点 → 每讲点一页 PPT 式大字画面 + TTS 音频 → 逐页短段 → 拼接
画面: 顶部章标/中部大字讲解/底部进度条/集次角标（高可读性, 适配纸张与网页）
输出: 素问01-上古天真论.mp4 (+ .video 副本)
"""
import argparse
import asyncio
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import edge_tts
from PIL import Image, ImageDraw, ImageFont

OUT_DIR = Path(r'C:\Users\DELL\textbook-project\drafts\cmrl\figures\book\video')
FONT = r'C:\Windows\Fonts\msyh.ttc'
FONT_BOLD = r'C:\Windows\Fonts\msyhbd.ttc'
W, H = 1920, 1080


def split_points(text):
    """按句拆分讲点（保留标点）"""
    parts = re.split(r'(?<=[。；！？])', text)
    return [p.strip() for p in parts if len(p.strip()) > 2]


def page_kind(text, role):
    """判定页类型: 原文页/金句页/解读页"""
    if '原文' in text[:6] or '曰' in text[:10] or '对曰' in text:
        return 'orig'   # 原文页(米黄底)
    if any(k in text for k in ('法于阴阳', '形与神俱', '精神内守', '德全不危',
                               '春夏养阳', '恬淡虚无')):
        return 'quote'  # 金句页(深色底)
    return 'plain'      # 解读页(白底)


def wrap(d, text, font, max_w):
    lines, cur = [], ''
    for ch in text:
        if d.textlength(cur + ch, font=font) > max_w:
            lines.append(cur)
            cur = ch
        else:
            cur += ch
    if cur:
        lines.append(cur)
    return lines


def make_page(role, text, idx, total, kind):
    img = Image.new('RGB', (W, H), '#faf8f2')
    d = ImageDraw.Draw(img)
    if kind == 'orig':
        bg, fg = '#fdf6e3', '#5d4037'
    elif kind == 'quote':
        bg, fg = '#2c3e50', '#f5f5f5'
    else:
        bg, fg = '#faf8f2', '#2c3e50'
    img = Image.new('RGB', (W, H), bg)
    d = ImageDraw.Draw(img)

    role_color = {'旁白': '#c0392b', '岐伯': '#1e8449', '案例': '#1a5276'}[role]
    role_name = {'旁白': '旁白 · 黄帝发问', '岐伯': '岐伯讲解', '案例': '临床案例'}[role]
    # 顶部章标
    d.rectangle([0, 0, W, 12], fill=role_color)
    f_small = ImageFont.truetype(FONT, 30)
    d.text((60, 40), f'《黄帝内经·素问》第 01 篇 · 上古天真论  |  {role_name}', font=f_small,
           fill='#7f8c8d')

    # 中部大字
    f_body = ImageFont.truetype(FONT_BOLD if kind == 'quote' else FONT, 52)
    lines = wrap(d, text, f_body, W - 220)
    y = 300 if len(lines) <= 4 else 180
    for ln in lines[:7]:
        d.text((110, y), ln, font=f_body, fill=fg)
        y += 84

    # 底部进度条
    bar_w = W - 220
    d.rectangle([110, H - 90, 110 + bar_w, H - 78], fill='#ecf0f1')
    d.rectangle([110, H - 90, 110 + int(bar_w * idx / total), H - 78], fill=role_color)
    f_foot = ImageFont.truetype(FONT, 26)
    d.text((110, H - 64), f'第 {idx}/{total} 讲点  |  tcmP 讲课模式', font=f_foot, fill='#95a5a6')
    d.text((W - 420, H - 64), '素问01 · 上古天真论', font=f_foot, fill='#95a5a6')
    return img


async def tts_one(voice, text, out_mp3, retries=4):
    for attempt in range(retries):
        try:
            await edge_tts.Communicate(text, voice, rate='-5%').save(str(out_mp3))
            return out_mp3
        except Exception as e:
            if attempt == retries - 1:
                raise
            print(f'    TTS 重试 {attempt + 1}: {type(e).__name__}')
            await asyncio.sleep(2 * (attempt + 1))


def parse_script(md: Path):
    t = md.read_text(encoding='utf-8')
    seg = re.findall(r'【(旁白|岐伯|案例)】(.+?)(?=\n【|\Z)', t, re.S)
    voices = {'旁白': 'zh-CN-XiaoxiaoNeural', '岐伯': 'zh-CN-YunxiNeural',
              '案例': 'zh-CN-XiaoxiaoNeural'}
    return [(role, voices[role], txt.strip().replace('\n', ''))
            for role, txt in seg if txt.strip()]


def main():
    md = Path(r'C:\Users\DELL\tcmP\docs\视频\素问01-上古天真论-讲解文案.md')
    segs = parse_script(md)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    work = OUT_DIR / 'lecture'
    work.mkdir(exist_ok=True)

    # ① 拆讲点
    points = []  # (role, voice, text, kind)
    for role, voice, text in segs:
        for p in split_points(text):
            points.append((role, voice, p, page_kind(p, role)))
    print(f'讲点总数: {len(points)}')
    if len(points) > 60:
        points = points[:60]
        print('（截断至 60 讲点）')

    # ② TTS + ③ 页面
    from moviepy import AudioFileClip, ImageClip, concatenate_videoclips
    from moviepy.audio.AudioClip import concatenate_audioclips
    from moviepy.audio.io.AudioFileClip import AudioFileClip as _AFC

    clips = []
    total = len(points)
    for i, (role, voice, text, kind) in enumerate(points, 1):
        mp3 = work / f'p{i:03d}.mp3'
        if not mp3.exists():
            asyncio.run(tts_one(voice, text, mp3))
        img = make_page(role, text, i, total, kind)
        png = work / f'p{i:03d}.png'
        img.save(str(png))
        audio = _AFC(str(mp3))
        clip = ImageClip(str(png), duration=audio.duration + 0.5).with_audio(audio)
        clips.append(clip)
        if i % 8 == 0 or i == total:
            print(f'  讲点 {i}/{total} 就绪')

    # ④ 拼接
    final = concatenate_videoclips(clips, method='compose')
    out = OUT_DIR / '素问01-上古天真论.mp4'
    final.write_videofile(str(out), fps=24, codec='libx264', audio_codec='aac',
                          temp_audiofile=str(work / 't.m4a'), logger=None)
    vcopy = OUT_DIR / '素问01-上古天真论.video'
    import shutil
    shutil.copy2(out, vcopy)
    print(f'✅ 讲课版成片: {out.name} ({out.stat().st_size // (1024*1024)}MB, {final.duration:.0f} 秒)')
    print(f'✅ .video 副本: {vcopy.name}')


if __name__ == '__main__':
    main()
