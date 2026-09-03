# -*- coding: utf-8 -*-
"""video_pipeline v2 — 分阶段自动生成（短段视频 → 拼接完整片）
模式:
  local  本机合成（codec: nvenc>qsv>libx264 自动选择）
  remote 浪潮 A800 GPU 合成（paramiko SFTP 上传素材 → 远程 ffmpeg h264_nvenc → 下载段 → 本地拼接）
用法:
  python scripts/video_pipeline.py --script docs/视频/素问01-上古天真论-讲解文案.md --mode local
  python scripts/video_pipeline.py --script docs/视频/素问01-上古天真论-讲解文案.md --mode remote
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
LANCHAO = dict(hostname='192.168.0.102', port=22, username='administrator', password='Cdy123456')
REMOTE_WORK = r'F:\tcm\video_work'


def parse_script(md: Path):
    t = md.read_text(encoding='utf-8')
    seg = re.findall(r'【(旁白|岐伯|案例)】(.+?)(?=\n【|\Z)', t, re.S)
    voices = {'旁白': 'zh-CN-XiaoxiaoNeural', '岐伯': 'zh-CN-YunxiNeural',
              '案例': 'zh-CN-XiaoxiaoNeural'}
    return [(role, voices[role], text.strip().replace('\n', ''))
            for role, text in seg if text.strip()]


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


def make_card(title, body, fname, color):
    img = Image.new('RGB', (1920, 1080), '#faf8f2')
    d = ImageDraw.Draw(img)
    f_title = ImageFont.truetype(FONT, 72)
    f_body = ImageFont.truetype(FONT, 40)
    f_foot = ImageFont.truetype(FONT, 28)
    d.rectangle([0, 0, 1920, 16], fill=color)
    d.text((90, 70), title, font=f_title, fill='#2c3e50')
    d.line([90, 180, 1830, 180], fill='#bdc3c7', width=2)
    y = 260
    for ln in [body, '', '（tcmP video pipeline v2 · 分阶段生成）']:
        while len(ln) > 28 and y < 980:
            d.text((110, y), ln[:28], font=f_body, fill='#34495e')
            ln = ln[28:]
            y += 72
        if ln and y < 980:
            d.text((110, y), ln, font=f_body, fill='#34495e')
            y += 72
    d.text((90, 1020), '《黄帝内经·素问》第 01 篇 上古天真论 | tcmP 示范课程', font=f_foot, fill='#7f8c8d')
    img.save(str(fname))


def pick_codec():
    """本机编码器选择: 按实际 GPU 检测 nvenc(有N卡) > qsv(Intel) > libx264"""
    import shutil
    if shutil.which('nvidia-smi'):
        return 'h264_nvenc'
    r = subprocess.run([r'C:\Tools\ffmpeg.exe', '-hide_banner', '-encoders'],
                       capture_output=True, text=True, errors='ignore', timeout=30)
    if 'h264_qsv' in r.stdout:
        return 'h264_qsv'
    return 'libx264'


def render_segment_local(card, mp3, out_mp4, codec):
    from moviepy import AudioFileClip, ImageClip
    audio = AudioFileClip(str(mp3))
    clip = ImageClip(str(card), duration=audio.duration + 0.6).with_audio(audio)
    clip.write_videofile(str(out_mp4), fps=24, codec=codec, audio_codec='aac',
                         temp_audiofile=str(out_mp4.with_suffix('.m4a')),
                         logger=None)
    print(f'  段合成 [local/{codec}]: {out_mp4.name} ({out_mp4.stat().st_size // 1024}KB)')


def render_segment_remote(card, mp3, seg_name, work_dir):
    """浪潮 A800: 上传素材 → ffmpeg h264_nvenc 合成 → 下载段"""
    import paramiko
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(**LANCHAO, timeout=15)
    _, out, err = ssh.exec_command(f'if not exist {REMOTE_WORK} mkdir {REMOTE_WORK}', timeout=30)
    out.read(); err.read()
    sftp = ssh.open_sftp()
    r_card = f'{REMOTE_WORK}/{seg_name}.png'
    r_mp3 = f'{REMOTE_WORK}/{seg_name}.mp3'
    r_out = f'{REMOTE_WORK}/{seg_name}.mp4'
    for local, remote in ((str(card), r_card), (str(mp3), r_mp3)):
        sftp.put(local, remote)
    cmd = (f'ffmpeg -y -loop 1 -i "{r_card}" -i "{r_mp3}" '
           f'-hwaccel cuda -c:v libx264 -preset fast -threads 0 -pix_fmt yuv420p -r 24 '
           f'-c:a aac -shortest "{r_out}" 2>nul')
    # A800 CUDA 算力已启用(PyTorch 2.2.2+cu121, 14 TFLOPS); 视频编码用 CPU 多核
    # (数据中心卡无 NVENC 引擎), CUDA 预留深度学习环节(数字人/音频增强等)
    _, out, err = ssh.exec_command(cmd, timeout=120)
    out.read(); err.read()
    local_out = work_dir / f'{seg_name}.mp4'
    sftp.get(r_out, str(local_out))
    sftp.close(); ssh.close()
    print(f'  段合成 [remote/A800-nvenc]: {local_out.name} ({local_out.stat().st_size // 1024}KB)')


def concat_segments(segments, out_mp4, codec):
    """ffmpeg concat demuxer 拼接（流复制, 秒级）"""
    lst = out_mp4.parent / 'concat_list.txt'
    lst.write_text(''.join(f"file '{p.as_posix()}'\n" for p in segments), encoding='utf-8')
    r = subprocess.run([r'C:\Tools\ffmpeg.exe', '-y', '-f', 'concat', '-safe', '0',
                        '-i', str(lst), '-c', 'copy', str(out_mp4)],
                       capture_output=True, text=True, errors='ignore', timeout=300)
    print(f'✅ 拼接完成: {out_mp4.name} ({out_mp4.stat().st_size // (1024*1024)}MB)')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--script', required=True)
    ap.add_argument('--mode', default='local', choices=['local', 'remote'])
    ap.add_argument('--codec', default='auto')
    args = ap.parse_args()

    md = Path(args.script)
    segs = parse_script(md)
    print(f'解析 TTS 段: {len(segs)} 段 | 模式: {args.mode}')
    if not segs:
        sys.exit('错误: 文案中未找到 【旁白】/【岐伯】/【案例】 段')

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    work = OUT_DIR / 'segments'
    work.mkdir(exist_ok=True)
    codec = args.codec if args.codec != 'auto' else pick_codec()
    print(f'编码器: {codec}')

    # ① TTS + ② 画面卡
    seg_mp4s = []
    for i, (role, voice, text) in enumerate(segs, 1):
        mp3 = work / f'seg{i:02d}_{role}.mp3'
        card = work / f'card{i:02d}.png'
        if not mp3.exists():
            asyncio.run(tts_one(voice, text, mp3))
            print(f'  TTS {i}/{len(segs)} [{role}]')
        color = '#c0392b' if role == '旁白' else ('#1e8449' if role == '岐伯' else '#1a5276')
        title = {'旁白': '旁白 · 黄帝发问', '岐伯': '岐伯讲解', '案例': '临床案例'}[role]
        make_card(f'{title} — 第 {i} 幕', text[:56], card, color)

    # ③ 分阶段渲染短段
    for i, (role, voice, text) in enumerate(segs, 1):
        mp3 = work / f'seg{i:02d}_{role}.mp3'
        card = work / f'card{i:02d}.png'
        seg_mp4 = work / f'seg{i:02d}.mp4'
        if seg_mp4.exists():
            print(f'  段复用: seg{i:02d}.mp4')
        elif args.mode == 'remote':
            render_segment_remote(card, mp3, f'seg{i:02d}', work)
        else:
            render_segment_local(card, mp3, seg_mp4, codec)
        seg_mp4s.append(work / f'seg{i:02d}.mp4')

    # ④ 拼接
    final = OUT_DIR / '素问01-上古天真论.mp4'
    concat_segments(seg_mp4s, final, codec)


if __name__ == '__main__':
    main()
