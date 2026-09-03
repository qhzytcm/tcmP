# -*- coding: utf-8 -*-
"""video_lecture2.py — 全程自动化演讲视频（含三线表页 + 更年期对比讲解）
结构: 原文讲点(19) + 表1女子页 + 表2男子页 + 表3对比页 + 表5更年期页 + 生长壮老已页
表格页: 三线表 PNG 全屏 + 专属讲解音频（阅读+理解+对比+精气神收束）
输出: 素问01-上古天真论.mp4 (完整演讲版)
"""
import asyncio
import re
import shutil
import sys
from pathlib import Path

import edge_tts
from PIL import Image

OUT_DIR = Path(r'C:\Users\DELL\textbook-project\drafts\cmrl\figures\book\video')
TABLES = OUT_DIR / 'tables'
FONT = r'C:\Windows\Fonts\msyh.ttc'

# ===== 表格页讲解音频（TTS 文本）=====
TABLE_TALKS = [
    ('表1-女子生命周期.png', 'zh-CN-XiaoxiaoNeural',
     '下面请看女子生命周期三线表。女子以七为纪，共七个阶段：七岁肾气盛，齿更发长；十四岁天癸至，任脉通，太冲脉盛，月事以时下，故有子；'
     '二十一岁肾气平均，真牙生而长极；二十八岁筋骨坚，身体盛壮，这是生理巅峰；三十五岁阳明脉衰，面始焦，发始堕；'
     '四十二岁三阳脉衰于上，面皆焦，发始白；四十九岁任脉虚，太冲脉衰少，天癸竭，地道不通，形坏而无子。'
     '女子生命周期，以肾气与天癸为主线，七个阶段，共四十九年。'),
    ('表2-男子生命周期.png', 'zh-CN-YunxiNeural',
     '再看男子生命周期三线表。男子以八为纪，共八个阶段：八岁肾气实，发长齿更；十六岁肾气盛，天癸至，精气溢泻，阴阳和，故能有子；'
     '二十四岁肾气平均，真牙生而长极；三十二岁筋骨隆盛，肌肉满壮，这是生理巅峰；四十岁肾气衰，发堕齿槁；'
     '四十八岁阳气衰竭于上，面焦，发鬓颁白；五十六岁肝气衰，筋不能动，天癸竭，精少，肾藏衰，形体皆极；六十四岁，齿发去。'
     '男子生命周期，同样以肾气与天癸为主线，八个阶段，共六十四年。'),
    ('表3-男女对比.png', 'zh-CN-XiaoxiaoNeural',
     '把两张表放在一起对比。相同之处：女子男子都以肾气与天癸为主线，盛衰轨迹都是拱形，先升、后峰、再降。'
     '不同之处：女子以七为纪，七阶段四十九年，周期短，变化快；男子以八为纪，八阶段六十四年，周期长，变化缓。'
     '女子二七初潮、七七绝经，标志明确；男子二八精溢、八八齿去，渐进无标。'),
    ('表5-更年期对比.png', 'zh-CN-XiaoxiaoNeural',
     '重点理解更年期。更年期，是壮阶段向老阶段过渡的转变期。女子从五七三十五岁到七七四十九岁，约十四年，变化快，'
     '以绝经为明确分界，以血为主；男子从五八四十岁到七八五十六岁，约十六年，变化缓，渐进衰退，以精为主。'
     '男女更年期既有共性也有差别：共性在于同处壮老过渡，天癸渐竭是共同主线，拱形对称；差别在于节奏与标志。'
     '理解男女更年期，要回到精气神三位一体：精是生命的物质基础，气是运行动力，神是主宰。肾精与天癸贯穿生命周期始终，'
     '守精、调气、养神，是渡过更年期、安享天年的根本。'),
    ('生长壮老已', 'zh-CN-YunxiNeural',
     '最后概括生长壮老已五阶段：生，生长发育，齿更、初潮、精溢；长，形体盛壮；壮，生理巅峰；老，面焦发堕齿槁；'
     '已，天癸竭，齿发去。五阶段沿拱形曲线展开，升、峰、降、终。' +
     '这就是上古天真论的生命观：以肾气与天癸为主线，以精气神三位一体为基石，顺应节律，形与神俱，度百岁乃去。'),
]

W, H = 1920, 1080


def make_table_page(png_src, out_png):
    """三线表 PNG 适配为全屏页（白底居中）"""
    img = Image.open(png_src)
    w, h = img.size
    scale = min((W - 160) / w, (H - 140) / h)
    nw, nh = int(w * scale), int(h * scale)
    img = img.resize((nw, nh), Image.LANCZOS)
    canvas = Image.new('RGB', (W, H), '#ffffff')
    canvas.paste(img, ((W - nw) // 2, (H - nh) // 2 + 20))
    canvas.save(out_png)
    return out_png


async def tts_one(voice, text, out_mp3, retries=4):
    for attempt in range(retries):
        try:
            await edge_tts.Communicate(text, voice, rate='-3%').save(str(out_mp3))
            return out_mp3
        except Exception as e:
            if attempt == retries - 1:
                raise
            print(f'    TTS 重试 {attempt + 1}: {type(e).__name__}')
            await asyncio.sleep(2 * (attempt + 1))


def split_points(text):
    parts = re.split(r'(?<=[。；！？])', text)
    return [p.strip() for p in parts if len(p.strip()) > 2]


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
    work = OUT_DIR / 'lecture2'
    work.mkdir(exist_ok=True)

    from moviepy import AudioFileClip, ImageClip, concatenate_videoclips
    from moviepy.audio.io.AudioFileClip import AudioFileClip as _AFC

    # ① 原文讲点（复用 lecture 页）
    from video_lecture import make_page, page_kind
    sys.path.insert(0, str(Path(r'C:\Users\DELL\tcmP\scripts')))

    clips = []
    n = 0
    # A. 原文讲点
    for role, voice, text in segs:
        for p in split_points(text):
            n += 1
            mp3 = work / f'p{n:03d}.mp3'
            if not mp3.exists():
                asyncio.run(tts_one(voice, p, mp3))
            img = make_page(role, p, n, 100, page_kind(p, role))
            png = work / f'p{n:03d}.png'
            img.save(str(png))
            audio = _AFC(str(mp3))
            clips.append(ImageClip(str(png), duration=audio.duration + 0.5).with_audio(audio))
    print(f'原文讲点: {n}')

    # B. 表格页（三线表全屏 + 讲解音频）
    for i, (tbl, voice, talk) in enumerate(TABLE_TALKS, 1):
        n += 1
        mp3 = work / f'p{n:03d}.mp3'
        if not mp3.exists():
            asyncio.run(tts_one(voice, talk, mp3))
        if tbl == '生长壮老已':
            # 生长壮老已页: 大字总结卡
            from video_lecture import make_page
            img = make_page('岐伯', talk, n, 100, 'quote')
        else:
            png = make_table_page(TABLES / tbl, work / f'p{n:03d}.png')
            img = Image.open(png)
        png = work / f'p{n:03d}.png'
        img.save(str(png))
        audio = _AFC(str(mp3))
        clips.append(ImageClip(str(png), duration=audio.duration + 0.6).with_audio(audio))
        print(f'表格页 {i}/5: {tbl} ({audio.duration:.0f}秒)')

    # ② 拼接
    final = concatenate_videoclips(clips, method='compose')
    out = OUT_DIR / '素问01-上古天真论.mp4'
    final.write_videofile(str(out), fps=24, codec='libx264', audio_codec='aac',
                          temp_audiofile=str(work / 't.m4a'), logger=None)
    shutil.copy2(out, OUT_DIR / '素问01-上古天真论.video')
    print(f'✅ 完整演讲版: {out.name} ({out.stat().st_size // (1024*1024)}MB, {final.duration:.0f} 秒, {n} 讲点)')


if __name__ == '__main__':
    main()
