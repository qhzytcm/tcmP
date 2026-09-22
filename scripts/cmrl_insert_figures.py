# -*- coding: utf-8 -*-
"""cmrl_insert_figures.py — 把章节插图(GIF)插入 Excel 对应正文段落行

流程:
  1. 读各章正文 md, 定位每个图块(图题/**图 N-X**、图体/![...])在正文段序列中的位置
  2. PNG → GIF 转换 (PIL, figures/chNN/figN-X.gif)
  3. openpyxl 打开 xlsx, 在对应段落行(表头+章行后, 正文段行)上方插入浮动图
  4. 图锚定列 C(内容列), 宽 420px, 高按原比例
用法: python scripts/cmrl_insert_figures.py [--ch N | --all]
"""
import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from cmrl_merge import CHAP_META  # noqa: E402
from cmrl_update_xlsx import DRAFTS, XLSX  # noqa: E402

FIGDIR = DRAFTS / 'figures'
IMG_W = 420  # 插入图宽(px)


def locate_figures(ch: int):
    """返回 [(fig_filename, body_para_index), ...] 图块位置映射
    锚定: 图块前最近正文段; 兼容 ../ 相对路径; 文件末尾图块结算"""
    d = DRAFTS / f'ch{ch:02d}'
    figs = []
    para_idx = 0          # 正文段计数(与 parse_md 顺序一致)
    for f in sorted(d.glob('0*-1.*.md')):
        lines = f.read_text(encoding='utf-8').splitlines()
        pending = None    # (fig_path, 图块前段落索引)
        for ln in lines:
            s = ln.strip()
            m = re.search(r'\]\((?:\.\./)?figures/ch\d+/(fig\d+-\d+\.(?:png|gif))\)', s)
            if m:
                pending = (m.group(1), para_idx)
                continue
            if s.startswith(('#', '![', '图注：', '【图')) or not s:
                continue
            if s.startswith('**图'):
                continue
            # 图块后第一个正文行 → 结算(锚定图块前段落)
            if pending:
                figs.append(pending)
                pending = None
            para_idx += 1
        if pending:   # 文件末尾图块: 锚定最后段落
            figs.append((pending[0], max(0, para_idx - 1)))
    return figs


def png_to_gif(png: Path) -> Path:
    from PIL import Image
    gif = png.with_suffix('.gif')
    img = Image.open(png).convert('RGB')
    img.save(gif, 'GIF')
    return gif


def insert_figures(ch: int):
    from openpyxl import load_workbook
    from openpyxl.drawing.image import Image as XLImage
    prefix, sheet_name, title = CHAP_META[ch]
    figs = locate_figures(ch)
    if not figs:
        print(f'[ch{ch:02d}] 未定位到图块')
        return 0
    wb = load_workbook(XLSX)
    ws = wb[sheet_name]
    if getattr(ws, '_images', None):
        print(f'[ch{ch:02d}] {sheet_name} 已含 {len(ws._images)} 幅图, 跳过（幂等）')
        wb.close()
        return 0
    inserted = 0
    for fig_name, para_idx in figs:
        png = FIGDIR / f'ch{ch:02d}' / fig_name.split('/')[-1]
        if not png.exists():
            print(f'  [MISS] {png}')
            continue
        gif = png_to_gif(png)
        img = XLImage(str(gif))
        # 按原比例缩放宽度
        from PIL import Image as PImg
        w, h = PImg.open(png).size
        img.width = IMG_W
        img.height = int(IMG_W * h / w)
        row = 3 + para_idx   # 表头1 + 章行2 → 正文段从第3行起
        anchor = f'C{row}'
        ws.add_image(img, anchor)
        inserted += 1
        print(f'  [图] {fig_name} → {sheet_name}!{anchor} (段{para_idx}, {img.width}x{img.height})')
    wb.save(XLSX)
    print(f'[ch{ch:02d}] {sheet_name}: 插入 {inserted} 幅 GIF 图')
    return inserted


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--ch', type=int)
    ap.add_argument('--all', action='store_true')
    args = ap.parse_args()
    chs = range(1, 11) if args.all else [args.ch]
    total = 0
    for ch in chs:
        total += insert_figures(ch)
    print(f'合计插入 {total} 幅')
