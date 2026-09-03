# -*- coding: utf-8 -*-
"""素问 11-81 自动批量（每次 3 篇）: 自动分段 → 远程TTS → ffmpeg合成 → 同步
用法: python batch_auto.py --range 11-13
"""
import argparse
import shutil
import subprocess
import sys
from pathlib import Path

import paramiko

sys.path.insert(0, r'C:\Users\DELL\tcmP\scripts')
from auto_segs import auto_extract
from batch_suwen import remote_tts, make_pages, render, sync_docs, CH_NAMES

XLSX = r'C:\Users\DELL\Desktop\HDNJ音频理解(2).xls'
DOCS = Path(r'C:\Users\DELL\tcmP\docs\视频')
VIDEO = Path(r'C:\Users\DELL\textbook-project\drafts\cmrl\figures\book\video')


def sheet_of(ch):
    if ch <= 15:
        return f'{ch}-{CH_NAMES[str(ch)]}'
    return f'SW{ch}'


def video_name(ch):
    return f'素问{ch}-{CH_NAMES[str(ch)]}'


def extract_auto(ch):
    sheet = sheet_of(ch)
    segs = auto_extract(sheet, ch)
    if not segs:
        print(f'[{sheet}] 无内容, 跳过')
        return None
    return segs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--range', required=True, help='如 11-13')
    args = ap.parse_args()
    a, b = map(int, args.range.split('-'))
    for ch in range(a, b + 1):
        name = video_name(ch)
        print(f'\n######## 素问{ch} {name} ########')
        segs = extract_auto(ch)
        if not segs:
            continue
        wdir = VIDEO / f'suwen{ch}'
        remote_tts(ch, segs)  # 复用 batch_suwen（suwen{ch} 目录）
        make_pages(ch, segs, wdir)
        ok = render(ch, wdir)
        if ok:
            # 同步 docs（命名: 素问{ch}[-名].mp4）
            src = VIDEO / f'{name}.mp4'
            shutil.copy2(src, DOCS / f'{name}.mp4')
            print(f'已同步 docs: {name}.mp4')


if __name__ == '__main__':
    main()
