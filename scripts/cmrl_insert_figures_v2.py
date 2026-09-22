# -*- coding: utf-8 -*-
"""cmrl_insert_figures_v2.py — PNG 插图（图题居中黑体 / 图体 PNG / 图注左顶格）

布局（对应正文段落处插入 3 行）:
  [图题行] 文本: 图 N-X 标题（居中、黑体）
  [图体行] PNG 浮动图锚定, 行高=图高
  [图注行] 文本: 图注：...（左对齐、顶格、自动换行）
用法: python scripts/cmrl_insert_figures_v2.py [--remove-gif] [--ch N | --all]
"""
import argparse
import math
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from cmrl_merge import CHAP_META  # noqa: E402
from cmrl_update_xlsx import DRAFTS, XLSX  # noqa: E402

FIGDIR = DRAFTS / 'figures'
IMG_W = 420


def locate_figures_v2(ch: int):
    """返回 [(fig_filename, para_idx, caption, note), ...]
    段计数与 v1(locate_figures) 完全一致(已验证 45/45 锚点); 额外提取图题/图注文字"""
    d = DRAFTS / f'ch{ch:02d}'
    figs = []
    para_idx = 0
    cur_caption = None
    for f in sorted(d.glob('0*-1.*.md')):
        lines = f.read_text(encoding='utf-8').splitlines()
        pending = None
        for ln in lines:
            s = ln.strip()
            m = re.search(r'\]\((?:\.\./)?figures/ch\d+/(fig\d+-\d+\.(?:png|gif))\)', s)
            if m:
                pending = [m.group(1), para_idx, cur_caption or '', '']
                cur_caption = None
                continue
            if s.startswith('**图'):
                cur_caption = s.strip('*').strip()
                continue
            if s.startswith(('#', '![', '图注：', '【图')) or not s:
                if s.startswith('图注：') and pending:
                    pending[3] = s
                continue
            if pending:
                figs.append(tuple(pending))
                pending = None
            para_idx += 1
        if pending and pending[3]:
            figs.append((pending[0], max(0, para_idx - 1), pending[2], pending[3]))
    return figs


def remove_gif_images():
    """移除全部已插入的 GIF 浮动图"""
    from openpyxl import load_workbook
    wb = load_workbook(XLSX)
    removed = 0
    for sn in wb.sheetnames:
        ws = wb[sn]
        imgs = getattr(ws, '_images', None) or []
        if imgs:
            removed += len(imgs)
            ws._images.clear()
    wb.save(XLSX)
    print(f'[remove] 移除 {removed} 幅 GIF 浮动图')
    return removed


def insert_figures(ch: int):
    from openpyxl import load_workbook
    from openpyxl.drawing.image import Image as XLImage
    from openpyxl.styles import Alignment, Font
    from PIL import Image as PImg
    prefix, sheet_name, title = CHAP_META[ch]
    figs = locate_figures_v2(ch)
    if not figs:
        print(f'[ch{ch:02d}] 未定位到图块')
        return 0
    wb = load_workbook(XLSX)
    ws = wb[sheet_name]
    if getattr(ws, '_images', None):
        print(f'[ch{ch:02d}] {sheet_name} 已含图, 跳过（幂等）')
        wb.close()
        return 0
    # 阶段1: 按段索引降序一次性插入所有图块行(3行/图), 不写内容
    for _, para_idx, _, _ in sorted(figs, key=lambda x: -x[1]):
        ws.insert_rows(3 + para_idx, 3)
    # 阶段2: 计算最终行(3+para_idx+段更小图数×3), 统一写文本+锚图
    inserted = 0
    for fig_name, para_idx, caption, note in sorted(figs, key=lambda x: x[1]):
        png = FIGDIR / f'ch{ch:02d}' / fig_name
        if not png.exists():
            print(f'  [MISS] {png}')
            continue
        smaller = sum(1 for _, p, _, _ in figs if p < para_idx)
        base_row = 3 + para_idx + smaller * 3
        # 图题行: 居中黑体
        c_cell = ws.cell(base_row, 3, caption)
        c_cell.font = Font(name='黑体', size=12, bold=False)
        c_cell.alignment = Alignment(horizontal='center', vertical='center')
        ws.row_dimensions[base_row].height = 22
        # 图注行: 左顶格自动换行
        n_cell = ws.cell(base_row + 2, 3, note)
        n_cell.font = Font(name='黑体', size=10)
        n_cell.alignment = Alignment(horizontal='left', vertical='top', wrap_text=True)
        n_rows = max(1, math.ceil(len(note) / 44))
        ws.row_dimensions[base_row + 2].height = n_rows * 14 + 6
        # 图体行: PNG 浮动图 + 行高
        w, h = PImg.open(png).size
        img = XLImage(str(png))
        img.width = IMG_W
        img.height = int(IMG_W * h / w)
        ws.add_image(img, f'C{base_row + 1}')
        ws.row_dimensions[base_row + 1].height = img.height * 0.75
        inserted += 1
        print(f'  [图] {fig_name} → {sheet_name} 段{para_idx} 行{base_row}-{base_row+2} '
              f'({img.width}x{img.height}px)')
    wb.save(XLSX)
    print(f'[ch{ch:02d}] {sheet_name}: 插入 {inserted} 幅 PNG 图')
    return inserted


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--remove-gif', action='store_true', help='先移除全部 GIF 图')
    ap.add_argument('--ch', type=int)
    ap.add_argument('--all', action='store_true')
    args = ap.parse_args()
    if args.remove_gif:
        remove_gif_images()
    chs = range(1, 11) if args.all else [args.ch]
    total = 0
    for ch in chs:
        total += insert_figures(ch)
    print(f'合计插入 {total} 幅 PNG')
