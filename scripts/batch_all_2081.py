# -*- coding: utf-8 -*-
"""素问 20-81 全自动批量（每篇: 提取→远程TTS→合成→同步; 单篇失败续跑）
用法: python batch_all_2081.py [起始篇]  （默认 20）
"""
import json
import shutil
import sys
import time
import traceback
from pathlib import Path

sys.path.insert(0, r'C:\Users\DELL\tcmP\scripts')
from batch_suwen import remote_tts, make_pages, render, CH_NAMES

DOCS = Path(r'C:\Users\DELL\tcmP\docs\视频')
VIDEO = Path(r'C:\Users\DELL\textbook-project\drafts\cmrl\figures\book\video')
LOG = DOCS / 'batch_20_81.log'


def sheet_of(ch):
    return f'SW{ch}'


def extract_auto(ch):
    """自动分段提取（auto_segs 顺序分段法）"""
    from auto_segs import auto_extract
    return auto_extract(sheet_of(ch), ch)


def main():
    start = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    fail = []
    t0 = time.time()
    for ch in range(start, 82):
        try:
            segs = extract_auto(ch)
            if not segs:
                print(f'素问{ch}: 无内容跳过')
                continue
            wdir = VIDEO / f'suwen{ch}'
            remote_tts(ch, segs)
            make_pages(ch, segs, wdir)
            ok = render(ch, wdir)
            if ok:
                name = f'素问{ch}-{CH_NAMES[str(ch)]}'
                shutil.copy2(VIDEO / f'{name}.mp4', DOCS / f'{name}.mp4')
                print(f'✅ 素问{ch} 完成')
            else:
                fail.append(ch)
                print(f'❌ 素问{ch} 合成失败')
        except Exception as e:
            fail.append(ch)
            print(f'❌ 素问{ch} 异常: {type(e).__name__} {str(e)[:120]}')
            traceback.print_exc(limit=2)
        # 进度日志（每篇追加）
        with open(LOG, 'a', encoding='utf-8') as f:
            f.write(f'{time.strftime("%H:%M:%S")} 素问{ch} {"FAIL" if ch in fail else "OK"}\n')
        # 每 3 篇报告批次
        if (ch - start + 1) % 3 == 0:
            print(f'--- 批次 {(ch - start + 1) // 3}: 素问{ch - 2}-{ch} 完成 ({time.time()-t0:.0f}s) ---')
    print(f'全自动批量结束: 成功 {81 - start + 1 - len(fail)} 篇, 失败 {fail}')


if __name__ == '__main__':
    main()
