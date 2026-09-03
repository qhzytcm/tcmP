# -*- coding: utf-8 -*-
"""video_lecture3_ff.py — v3 合成（ffmpeg CLI: 静图+音频→段mp4→concat）
利用 v3/ 已有产物（p01-10.mp3 + *_ppt.png + *_table.png）
"""
import subprocess
import sys
from pathlib import Path

OUT = Path(r'C:\Users\DELL\textbook-project\drafts\cmrl\figures\book\video')
WORK = OUT / 'v3'
FF = r'C:\Tools\ffmpeg.exe'

# 段配置: (mp3, [画面页按音频时长均分])
SEG_PAGES = {
    1: ['p01_ppt.png'], 2: ['p02_ppt.png'], 3: ['p03_ppt.png'],
    4: ['p04_ppt.png'], 5: ['p05_ppt.png'], 6: ['p06_ppt.png'],
    7: ['p07_ppt.png', 'p07_table.png'],
    8: ['p08_ppt.png', 'p08_table.png'],
    9: ['p09_ppt.png'], 10: ['p10_ppt.png'],
}


def seg_duration(mp3):
    r = subprocess.run([FF, '-i', str(mp3)], capture_output=True, text=True,
                       errors='ignore', timeout=60)
    for ln in r.stderr.splitlines():
        if 'Duration' in ln:
            hms = ln.split('Duration:')[1].split(',')[0].strip()
            h, m, s = hms.split(':')
            return int(h) * 3600 + int(m) * 60 + float(s)
    return 30.0


def render_seg(idx, pages):
    mp3 = WORK / f'p{idx:02d}.mp3'
    dur = seg_duration(mp3)
    per = dur / len(pages)
    seg_mp4s = []
    for j, pg in enumerate(pages):
        out_seg = WORK / f'seg{idx:02d}_{j}.mp4'
        # 音频切片 + 静图循环合成
        t0, t1 = j * per, min((j + 1) * per + 0.4, dur)
        r = subprocess.run([
            FF, '-y', '-loop', '1', '-i', str(WORK / pg),
            '-ss', f'{t0:.2f}', '-t', f'{t1 - t0:.2f}', '-i', str(mp3),
            '-c:v', 'libx264', '-preset', 'fast', '-pix_fmt', 'yuv420p', '-r', '24',
            '-c:a', 'aac', '-shortest', str(out_seg),
        ], capture_output=True, text=True, errors='ignore', timeout=300)
        if not out_seg.exists() or out_seg.stat().st_size < 10 * 1024:
            print(f'  ❌ 段 {idx} 页 {j} 失败: {r.stderr[-200:]}')
            return None
        seg_mp4s.append(out_seg)
    print(f'  段 {idx}: {dur:.0f}秒 × {len(pages)}页 OK')
    return seg_mp4s


def main():
    all_segs = []
    for idx in range(1, 11):
        segs = render_seg(idx, SEG_PAGES[idx])
        if not segs:
            sys.exit(1)
        all_segs.extend(segs)
    # concat
    lst = WORK / 'concat.txt'
    lst.write_text(''.join(f"file '{p.as_posix()}'\n" for p in all_segs), encoding='utf-8')
    out = OUT / '素问01-上古天真论.mp4'
    r = subprocess.run([FF, '-y', '-f', 'concat', '-safe', '0', '-i', str(lst),
                        '-c', 'copy', str(out)], capture_output=True, text=True,
                       errors='ignore', timeout=300)
    if out.exists() and out.stat().st_size > 5 * 1024 * 1024:
        import shutil
        shutil.copy2(out, OUT / '素问01-上古天真论.video')
        mins = seg_duration(out) / 60
        print(f'✅ v3 成片: {out.name} ({out.stat().st_size // (1024*1024)}MB, {mins:.1f} 分钟)')
        print(f'   时长目标 10-15 分钟: {"✅达标" if 10 <= mins <= 15 else "⚠需调整"}')
    else:
        print('❌ 拼接失败:', r.stderr[-300:])
        sys.exit(1)


if __name__ == '__main__':
    main()
