# -*- coding: utf-8 -*-
"""素问 2-5 篇批量流水线: Excel提取 → segs.json → 远程TTS → ffmpeg合成 → 同步
用法: python batch_suwen.py --chapter 2|3|4|5  （或 --all）
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, r'C:\Users\DELL\tcmP\scripts')
from segs_def_suwen2_5 import SEG_DEFS
from segs_def_suwen6_10 import SEG_DEFS_6_10
SEG_DEFS.update(SEG_DEFS_6_10)

XLSX = r'C:\Users\DELL\Desktop\HDNJ音频理解(2).xls'
DOCS = Path(r'C:\Users\DELL\tcmP\docs\视频')
VIDEO = Path(r'C:\Users\DELL\textbook-project\drafts\cmrl\figures\book\video')
FF = r'C:\Tools\ffmpeg.exe'
TABLES = VIDEO / 'tables'

CH_NAMES = {'2': '四气调神大论', '3': '生气通天论', '4': '金匮真言论', '5': '阴阳应象大论',
            '6': '阴阳离合论', '7': '阴阳别论', '8': '灵兰秘典论',
            '9': '六节藏象论', '10': '五藏生成篇',
            '11': '五藏别论', '12': '异法方宜论', '13': '移精变气论',
            '14': '汤液醪醴论', '15': '玉版论要'}
CH_NAMES.update({str(i): f'SW{i}' for i in range(16, 82)})
try:
    from ch_names_81 import CH_NAMES_STR as _CN81
    CH_NAMES.update(_CN81)
except Exception:
    pass


def clean_part(p):
    p = re.sub(r'^Hermes独立理解《[^》]+》：.*?。', '', p)
    p = re.sub(r'^[一二三四五六七八九十]+、', '', p)
    p = p.replace('（鼓掌）', '').replace('（笑）', '')
    return p.strip()


def build_orig(sents, kws):
    picked = [s for s in sents if any(k in s for k in kws)]
    merged = []
    for s in picked:
        if not s:
            continue
        dup = False
        for i, m in enumerate(merged):
            if s in m or m in s:
                if len(s) > len(m):
                    merged[i] = s
                dup = True
                break
        if not dup:
            merged.append(s)
    return '，'.join(merged)


def build_talk(notes, unds, summary, kws):
    parts = []
    for n in notes:
        if n.startswith('Hermes独立理解'):
            continue
        if any(k in n for k in kws) and len(n) > 14:
            parts.append(clean_part(n))
    parts += [clean_part(u) for u in unds if len(u) > 6 and any(k in u for k in kws)]
    for sp in re.split(r'[①②③④⑤⑥]', summary):
        if any(k in sp for k in kws) and len(sp) > 12:
            parts.append(clean_part(sp.strip()))
    seen, out = [], []
    for p in parts:
        if not p:
            continue
        if any(p == q or (len(p) > 20 and (p in q or q in p)) for q in seen):
            continue
        seen.append(p)
        out.append(p)
    talk = '。'.join(out)
    if len(talk) > 480:
        talk = talk[:480] + '。'
    if len(talk) <= 40:
        # 兜底: 取总结分段第一长段（保证讲解非占位; 40字边界也触发）
        for sp in re.split(r'[①②③④⑤⑥⑦]', summary):
            sp = clean_part(sp.strip())
            if len(sp) > 40:
                talk = sp[:240]
                break
    return talk if len(talk) > 40 else '（讲解）'


def extract(ch):
    sheet = f'{ch}-{CH_NAMES[str(ch)]}'
    df = pd.read_excel(XLSX, sheet_name=sheet)
    orig_sents, notes, unds, summary = [], [], [], ''
    for v in df['文本内容'].dropna():
        t = str(v).strip()
        if t.startswith('原文-'):
            orig_sents.append(t[3:].strip())
        elif t.startswith('注释-'):
            notes.append(t[3:].strip())
        elif t.startswith('理解-'):
            unds.append(t[3:].strip())
        elif t.startswith('总结-'):
            summary = t[3:].strip()
    segs = []
    for title, orig_kws, talk_kws in SEG_DEFS[sheet]:
        segs.append({'title': title, 'orig': build_orig(orig_sents, orig_kws),
                     'talk': build_talk(notes, unds, summary, talk_kws)})
    out = DOCS / f'segs_suwen{ch}.json'
    out.write_text(json.dumps(segs, ensure_ascii=False, indent=1), encoding='utf-8')
    total = sum(len(s['orig']) + len(s['talk']) for s in segs)
    print(f'[{sheet}] 十段提取完成, 总字数 {total}')
    return segs


def seg_style(i, title, talk):
    """段型→(rate, pitch)（tcm-lecture-spirit 规范）"""
    jinju = any(k in talk for k in ('法于阴阳', '德全不危', '恬惔虚无', '阴平阳秘',
                                    '精神内守', '真气从之', '阴阳者天地之道'))
    if i <= 2:
        return ('-5%', '+0Hz')   # 开篇/设问: 沉稳引入
    if jinju:
        return ('-8%', '+2Hz')   # 金句: 加重强调
    if i >= 9:
        return ('-6%', '-1Hz')   # 收束: 余音
    return ('-3%', '+0Hz')       # 主体: 平稳清晰


def remote_tts(ch, segs):
    """浪潮远程 TTS（独立目录 tts_work/suwen{ch}; 段型 rate/pitch 差异化）"""
    import paramiko
    REMOTE = dict(hostname='192.168.0.102', port=22, username='administrator',
                  password='Cdy123456')
    RWORK = rf'F:\tcm\tts_work\suwen{ch}'
    segs_text = []
    for i, seg in enumerate(segs, 1):
        voice = 'zh-CN-YunxiNeural' if i in (3, 5, 6, 9, 10) else 'zh-CN-XiaoxiaoNeural'
        text = (seg['orig'] + '。' + seg['talk']).replace('，，', '，').replace('。。', '。')
        from tts_phoneme import apply_phoneme
        text = apply_phoneme(text)   # 医学多音字注音（脏zàng/藏象/恶wù/相傅xiàng）
        rate, pitch = seg_style(i, seg['title'], seg['talk'])
        segs_text.append((i, voice, text, rate, pitch))
    script = f'''
# -*- coding: utf-8 -*-
import asyncio, edge_tts, os
WORK = r'{RWORK}'
SEGS = {segs_text!r}
async def tts_one(voice, text, rate, pitch, out, retries=6):
    for attempt in range(retries):
        try:
            await edge_tts.Communicate(text, voice, rate=rate, pitch=pitch).save(out)
            if os.path.getsize(out) > 8 * 1024:
                return True
            os.remove(out)
        except Exception:
            await asyncio.sleep(4 * (attempt + 1))
    return False
async def main():
    ok = 0
    for i, voice, text, rate, pitch in SEGS:
        out = os.path.join(WORK, f'p{{i:02d}}.mp3')
        if os.path.exists(out) and os.path.getsize(out) > 8 * 1024:
            ok += 1; continue
        if await tts_one(voice, text, rate, pitch, out):
            ok += 1
        await asyncio.sleep(2)
    print('REMOTE_TTS_DONE', ok, '/', len(SEGS))
asyncio.run(main())
'''
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(**REMOTE, timeout=15)
    ssh.exec_command(f'if not exist {RWORK} mkdir {RWORK}')[1].read()
    sftp = ssh.open_sftp()
    with sftp.open(f'{RWORK}/tts.py', 'w') as f:
        f.write(script)
    sftp.close()
    _, out, err = ssh.exec_command(f'python {RWORK}\\tts.py', timeout=1200)
    lines = out.read().decode('utf-8', errors='ignore').strip().splitlines()
    for ln in lines:
        print('   ', ln)
    e = err.read().decode('utf-8', errors='ignore').strip()
    if e and 'Error' in e:
        print('ERR:', e[-200:])
    sftp = ssh.open_sftp()
    wdir = VIDEO / f'suwen{ch}'
    wdir.mkdir(exist_ok=True)
    n = 0
    for i in range(1, 11):
        try:
            sftp.get(f'{RWORK}/p{i:02d}.mp3', str(wdir / f'p{i:02d}.mp3'))
            n += 1
        except Exception:
            pass
    sftp.close()
    ssh.close()
    print(f'  TTS 下载 {n}/10')
    return wdir


def make_pages(ch, segs, wdir):
    """每段 1 张标题页（+三线表段附加表页——素问2-5 暂无表, 用文字页）"""
    from PIL import Image, ImageDraw, ImageFont
    FONT = r'C:\Windows\Fonts\msyh.ttc'
    FB = r'C:\Windows\Fonts\msyhbd.ttc'
    W, H = 1920, 1080

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

    for i, seg in enumerate(segs, 1):
        img = Image.new('RGB', (W, H), '#faf8f2')
        d = ImageDraw.Draw(img)
        f_t = ImageFont.truetype(FB, 56)
        f_o = ImageFont.truetype(FB, 40)
        f_k = ImageFont.truetype(FONT, 32)
        d.rectangle([0, 0, W, 14], fill='#1e8449')
        d.text((70, 50), f'黄帝内经·素问{ch}·{CH_NAMES[str(ch)]}  |  {seg["title"]}', font=f_t, fill='#2c3e50')
        d.line([70, 140, W - 70, 140], fill='#bdc3c7', width=2)
        y = 190
        for ln in wrap(d, seg['orig'], f_o, W - 160):
            d.text((80, y), ln, font=f_o, fill='#5d4037')
            y += 62
        y += 16
        d.text((80, y), '【讲解】', font=f_k, fill='#1e8449')
        y += 52
        for ln in wrap(d, seg['talk'], f_k, W - 160)[:10]:
            d.text((80, y), ln, font=f_k, fill='#34495e')
            y += 56
            if y > 1010:
                break
        img.save(wdir / f'p{i:02d}.png')


def render(ch, wdir):
    """ffmpeg CLI 合成（静图+音频→段mp4→concat; 避免 moviepy 长视频卡死）"""
    FF = r'C:\Tools\ffmpeg.exe'
    seg_mp4s = []
    for i in range(1, 11):
        mp3 = wdir / f'p{i:02d}.mp3'
        png = wdir / f'p{i:02d}.png'
        seg = wdir / f'seg{i:02d}.mp4'
        r = subprocess.run([FF, '-y', '-loop', '1', '-i', str(png), '-i', str(mp3),
                            '-c:v', 'libx264', '-preset', 'fast', '-pix_fmt', 'yuv420p',
                            '-r', '24', '-c:a', 'aac', '-shortest', str(seg)],
                           capture_output=True, text=True, errors='ignore', timeout=300)
        if not seg.exists() or seg.stat().st_size < 10 * 1024:
            print(f'  ❌ 段 {i} 失败: {r.stderr[-150:]}')
            return False
        seg_mp4s.append(seg)
    lst = wdir / 'concat.txt'
    lst.write_text(''.join(f"file '{p.as_posix()}'\n" for p in seg_mp4s), encoding='utf-8')
    out = VIDEO / f'素问{ch}-{CH_NAMES[str(ch)]}.mp4'
    subprocess.run([FF, '-y', '-f', 'concat', '-safe', '0', '-i', str(lst),
                    '-c', 'copy', str(out)], capture_output=True, text=True,
                   errors='ignore', timeout=300)
    if out.exists() and out.stat().st_size > 3 * 1024 * 1024:
        shutil.copy2(out, VIDEO / f'素问{ch}-{CH_NAMES[str(ch)]}.video')
        print(f'✅ 素问{ch} 成片: {out.name} ({out.stat().st_size // (1024*1024)}MB)')
        return True
    print('❌ 拼接失败')
    return False


def sync_docs(ch):
    name = CH_NAMES[str(ch)]
    shutil.copy2(VIDEO / f'素问{ch}-{name}.mp4', DOCS / f'素问{ch}-{name}.mp4')
    print(f'已同步 docs: 素问{ch}-{name}.mp4')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--chapter', choices=['2', '3', '4', '5', '6', '7', '8', '9', '10'])
    ap.add_argument('--all', action='store_true')
    args = ap.parse_args()
    chs = ['2', '3', '4', '5', '6', '7', '8', '9', '10'] if args.all else [args.chapter]
    for ch in chs:
        print(f'\n######## 素问{ch} {CH_NAMES[str(ch)]} ########')
        segs = extract(ch)
        wdir = remote_tts(ch, segs)
        make_pages(ch, segs, wdir)
        render(ch, wdir)
        sync_docs(ch)


if __name__ == '__main__':
    main()
