# -*- coding: utf-8 -*-
"""
S48 第三份扫描件（最清晰）OCR 驱动，可续跑
PDF: 桌面 bycd\03-病源辞典.pdf  →  data/bingyuan3_ocr/page_XXXX.json
用法： python scripts/s48_ocr_pdf3.py --pages 0-29
"""
import os, json, time, argparse
import pymupdf

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PDF = r"C:\Users\DELL\Desktop\bycd\03-病源辞典.pdf"
OUT = os.path.join(ROOT, 'data', 'bingyuan3_ocr')
TMP = os.environ.get('TEMP', '.')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--limit', type=int, default=None)
    ap.add_argument('--pages', type=str, default=None, help='如 0-29')
    ap.add_argument('--stride', type=int, default=1)
    ap.add_argument('--dpi', type=int, default=300)
    a = ap.parse_args()

    os.makedirs(OUT, exist_ok=True)
    doc = pymupdf.open(PDF)
    total = doc.page_count
    if a.pages:
        lo, hi = a.pages.split('-'); rng = range(int(lo), int(hi) + 1)
    elif a.limit:
        rng = range(min(a.limit, total))
    else:
        rng = range(total)
    if a.stride > 1:
        rng = range(rng.start, rng.stop, a.stride)

    from rapidocr_onnxruntime import RapidOCR
    ocr = RapidOCR()
    done = skip = 0
    t0 = time.time()
    for i in rng:
        fp = os.path.join(OUT, f'page_{i:04d}.json')
        if os.path.exists(fp) and os.path.getsize(fp) > 20:
            skip += 1; continue
        try:
            pix = doc[i].get_pixmap(dpi=a.dpi)
            img = os.path.join(TMP, f'_ocr3_{os.getpid()}_{i:04d}.png')
            pix.save(img)
            res, _ = ocr(img)
            os.remove(img)
            lines = [{'text': r[1], 'box': r[0], 'score': round(float(r[2]), 3)} for r in (res or [])]
            json.dump({'page': i, 'w': doc[i].rect.width, 'h': doc[i].rect.height,
                       'dpi': a.dpi, 'n': len(lines), 'lines': lines},
                      open(fp, 'w', encoding='utf-8'), ensure_ascii=False)
            done += 1
            print(f'[{i}] {len(lines)} 行 | 完成 {done} 跳过 {skip} | {time.time()-t0:.0f}s', flush=True)
        except Exception as e:
            print(f'[{i}] ERR {type(e).__name__} {str(e)[:80]}', flush=True)
    print(f'DONE done={done} skip={skip} total={total} {time.time()-t0:.0f}s', flush=True)


if __name__ == '__main__':
    main()
