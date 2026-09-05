# -*- coding: utf-8 -*-
"""全量注音重生成: 遍历 2-81 篇, 含医学多音字(脏/藏象/恶/相傅)篇 → 重TTS(注音SSML) → 合成 → 同步
素问1 已单独完成（regen_suwen1_phoneme.py）
"""
import json
import shutil
import sys
import time
import traceback
from pathlib import Path

import paramiko

sys.path.insert(0, r'C:\Users\DELL\tcmP\scripts')
from batch_suwen import remote_tts, make_pages, render, CH_NAMES
from tts_phoneme import has_target

DOCS = Path(r'C:\Users\DELL\tcmP\docs\视频')
VIDEO = Path(r'C:\Users\DELL\textbook-project\drafts\cmrl\figures\book\video')
LOG = DOCS / 'phoneme_2_81.log'


def affected(ch):
    f = DOCS / f'segs_suwen{ch}.json'
    if not f.exists():
        return False
    segs = json.loads(f.read_text(encoding='utf-8'))
    return any(has_target(s.get('orig', '') + '。' + s.get('talk', '')) for s in segs)


def main():
    t0 = time.time()
    todo = [ch for ch in range(2, 82) if affected(ch)]
    print(f'受影响篇: {len(todo)} 篇 {todo[:10]}…')
    fail = []
    for ch in todo:
        try:
            seg_file = DOCS / f'segs_suwen{ch}.json'
            segs = json.loads(seg_file.read_text(encoding='utf-8'))
            # 删远程+本地 mp3（重 TTS 注音版）
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect('192.168.0.102', port=22, username='administrator',
                        password='Cdy123456', timeout=15)
            ssh.exec_command(f'del F:\\tcm\\tts_work\\suwen{ch}\\p*.mp3')[1].read()
            ssh.close()
            for p in (VIDEO / f'suwen{ch}').glob('p*.mp3'):
                p.unlink(missing_ok=True)
            wdir = remote_tts(ch, segs)
            make_pages(ch, segs, wdir)
            ok = render(ch, wdir)
            if ok:
                name = f'素问{ch}-{CH_NAMES[str(ch)]}'
                shutil.copy2(VIDEO / f'{name}.mp4', DOCS / f'{name}.mp4')
                print(f'✅ 素问{ch} 注音重生成')
            else:
                fail.append(ch)
        except Exception as e:
            fail.append(ch)
            print(f'❌ 素问{ch}: {type(e).__name__} {str(e)[:100]}')
            traceback.print_exc(limit=1)
        with open(LOG, 'a', encoding='utf-8') as f:
            f.write(f'{time.strftime("%H:%M:%S")} 素问{ch} {"FAIL" if ch in fail else "OK"}\n')
    print(f'注音批量结束: 成功 {len(todo)-len(fail)} 篇, 失败 {fail}, 耗时 {(time.time()-t0)/60:.0f} 分钟')


if __name__ == '__main__':
    main()
