# -*- coding: utf-8 -*-
"""SW63-80 讲解音频内容重建：清理远程旧 TTS → 重生成 TTS/页面/合成 → 同步 docs。

前置: segs_suwen63-80.json 已是重建后的讲解文本（页码已清）
用法: python rebuild_63_80.py [起始篇,缺省63]
"""
import json
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, r"C:\Users\DELL\tcmP\scripts")
import paramiko
from batch_suwen import remote_tts, make_pages, render, sync_docs, CH_NAMES

VD = Path(r"C:\Users\DELL\tcmP\docs\视频")
VIDEO = Path(r"C:\Users\DELL\textbook-project\drafts\cmrl\figures\book\video")
VID_LEGACY = VIDEO / "_legacy_sw"
LOG = VD / "rebuild_63_80.log"
REMOTE = dict(hostname="192.168.0.102", port=22, username="administrator", password="Cdy123456")


def clear_remote(ch):
    """删除远程旧 mp3 强制重生成"""
    RWORK = rf"F:\tcm\tts_work\suwen{ch}"
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(**REMOTE, timeout=15)
    ssh.exec_command(f"if exist {RWORK} del /q {RWORK}\\p*.mp3")
    ssh.close()


def clear_local(ch):
    wdir = VIDEO / f"suwen{ch}"
    wdir.mkdir(exist_ok=True)
    for pat in ("p*.mp3", "p*.png", "seg*.mp4", "concat.txt"):
        for f in wdir.glob(pat):
            try:
                f.unlink()
            except OSError:
                pass
    return wdir


def archive_old_sw(ch, name):
    """旧 SWNN 命名的 mp4/.video 移入 _legacy_sw"""
    VID_LEGACY.mkdir(exist_ok=True)
    for fn in (f"素问{ch}-SW{ch}.mp4", f"素问{ch}-SW{ch}.video"):
        p = VIDEO / fn
        if p.exists():
            p.replace(VID_LEGACY / fn)


def main():
    start = int(sys.argv[1]) if len(sys.argv) > 1 else 63
    end = int(sys.argv[2]) if len(sys.argv) > 2 else 80
    ok_list, fail_list = [], []
    t0 = time.time()
    for ch in range(start, end + 1):
        name = CH_NAMES[str(ch)]
        jf = VD / f"segs_suwen{ch}.json"
        segs = json.loads(jf.read_text(encoding="utf-8"))
        print(f"\n######## 素问{ch} {name} ({len(segs)}段) ########")
        try:
            clear_remote(ch)
            wdir = clear_local(ch)
            remote_tts(ch, segs)
            make_pages(ch, segs, wdir)
            ok = render(ch, wdir)
            if ok:
                sync_docs(ch)
                archive_old_sw(ch, name)
                ok_list.append(ch)
                print(f"✅ 素问{ch} 完成 ({time.time()-t0:.0f}s)")
            else:
                fail_list.append(ch)
                print(f"❌ 素问{ch} 合成失败")
        except Exception as e:
            fail_list.append(ch)
            print(f"❌ 素问{ch} 异常: {type(e).__name__} {str(e)[:160]}")
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(f"{time.strftime('%m-%d %H:%M:%S')} 素问{ch} {'OK' if ch in ok_list else 'FAIL'}\n")
    print(f"\n重建结束: 成功 {len(ok_list)} 篇 {ok_list}; 失败 {fail_list}; 用时 {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
