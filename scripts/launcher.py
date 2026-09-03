# -*- coding: utf-8 -*-
"""launcher.py — 桌面应用启动器（pywebview 加载本地课程 HTML）
打包: pyinstaller --onefile --windowed --name 素问01上古天真论课程 launcher.py
说明: 打包时 --add-data 附带 课程 HTML + mp4 + manifest + icons
"""
import os
import sys
from pathlib import Path


def base_dir():
    if getattr(sys, 'frozen', False):  # PyInstaller 打包后
        return Path(sys._MEIPASS)
    return Path(__file__).parent


def main():
    import webview
    base = base_dir()
    html = base / '素问01-上古天真论-视频课程.html'
    # 相对引用解析: pywebview 用 file:// 加载, mp4 同目录
    url = html.resolve().as_uri()
    webview.create_window(
        '黄帝内经·素问01·上古天真论',
        url,
        width=1280, height=800,
        min_size=(960, 600),
    )
    webview.start()


if __name__ == '__main__':
    main()
