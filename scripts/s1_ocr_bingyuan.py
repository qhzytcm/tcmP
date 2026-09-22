# -*- coding: utf-8 -*-
"""
S1 病源辭典 OCR 驱动（可续跑）
渲染每页 → RapidOCR → 逐页 JSON。已存在的页跳过（便于断点续跑）。
用法：
    python scripts/s1_ocr_bingyuan.py                 # 全部页
    python scripts/s1_ocr_bingyuan.py --limit 60      # 前60页
    python scripts/s1_ocr_bingyuan.py --pages 0-99    # 指定页范围
"""
import fitz, os, sys, json, time, argparse

PDF = r"C:\Users\DELL\Desktop\NLC416-06jh009124-2588_病源辭典.pdf"
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'bingyuan_ocr')
TMP = os.environ.get('TEMP', '.')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--limit', type=int, default=None)
    ap.add_argument('--pages', type=str, default=None, help='如 0-99')
    ap.add_argument('--dpi', type=int, default=300)
    a = ap.parse_args()

    os.makedirs(OUT, exist_ok=True)
    doc = fitz.open(PDF)
    total = doc.page_count
    if a.pages:
        lo, hi = a.pages.split('-'); rng = range(int(lo), int(hi) + 1)
    elif a.limit:
        rng = range(min(a.limit, total))
    else:
        rng = range(total)

    from rapidocr_onnxruntime import RapidOCR
    ocr = RapidOCR()

    done = skip = 0
    t_all = time.time()
    for i in rng:
        fp = os.path.join(OUT, f'page_{i:04d}.json')
        if os.path.exists(fp) and os.path.getsize(fp) > 20:
            skip += 1
            continue
        try:
            pix = doc[i].get_pixmap(dpi=a.dpi)
            img = os.path.join(TMP, f'_ocr_{i:04d}.png')
            pix.save(img)
            res, _ = ocr(img)
            os.remove(img)
            lines = []
            for r in (res or []):
                box, txt, score = r[0], r[1], r[2]
                lines.append({'text': txt, 'box': box, 'score': round(float(score), 3)})
            rec = {'page': i, 'w': doc[i].rect.width, 'h': doc[i].rect.height,
                   'dpi': a.dpi, 'n': len(lines), 'lines': lines}
            with open(fp, 'w', encoding='utf-8') as f:
                json.dump(rec, f, ensure_ascii=False)
            done += 1
            el = time.time() - t_all
            print(f'[{i}] OCR {len(lines)} 行 | 本次完成 {done} 跳过 {skip} | 用时 {el:.0f}s', flush=True)
        except Exception as e:
            print(f'[{i}] ERROR {e}', flush=True)
    doc.close()
    print(f'DONE total_pages={total} done={done} skipped={skip} in {time.time()-t_all:.0f}s', flush=True)


if __name__ == '__main__':
    main()
