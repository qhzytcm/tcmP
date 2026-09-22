# -*- coding: utf-8 -*-
"""
S8 版式与页码专用检测
检测「16开双栏 从左到右横排 简体 5号仿宋」：
  1) 页面尺寸 ≈ 196.75×273mm（16开）
  2) 双栏（文本块 x 呈两簇）
  3) 横排（行框宽>高）
  4) 仿宋字体存在
  5) 5号 = 10.5pt 存在
  6) 页码升序、连续、无缺漏/重号
输出：dist/layout_check.json
"""
import os, re, json, argparse
import fitz

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, 'dist')


def check(pdf):
    rep = {'checks': [], 'ok': True}

    def ck(n, c, d=''):
        rep['checks'].append({'name': n, 'pass': bool(c), 'detail': str(d)})
        if not c:
            rep['ok'] = False

    doc = fitz.open(pdf)
    N = doc.page_count
    ck('PDF 打开且页数>0', N > 0, f'{N} 页')

    # 尺寸（mm）
    r0 = doc[0].rect
    w_mm, h_mm = r0.width / 72 * 25.4, r0.height / 72 * 25.4
    ck('16开页面尺寸(196.75×273mm±3)', abs(w_mm - 196.75) < 3 and abs(h_mm - 273) < 3,
       f'{w_mm:.1f}×{h_mm:.1f}mm')

    # 字体/字号/横排/双栏 抽样若干页
    fonts, sizes = set(), set()
    col_ok_pages = 0
    ltr_ok_pages = 0
    sampled = list(range(min(N, 30)))
    for i in sampled:
        d = doc[i].get_text('dict')
        xs = []
        for b in d['blocks']:
            for l in b.get('lines', []):
                for s in l['spans']:
                    fonts.add(s['font']); sizes.add(round(s['size'], 1))
                x0, y0, x1, y1 = l['bbox']
                if (x1 - x0) > (y1 - y0):
                    ltr_ok_pages += 1  # 该行横排
                xs.append(x0)
        # 双栏：x0 分两簇（左栏 x≈MARGIN, 右栏 x≈PAGE/2）
        if xs:
            left = sum(1 for x in xs if x < r0.width / 2)
            right = len(xs) - left
            if left >= 3 and right >= 3:
                col_ok_pages += 1
    ck('仿宋字体存在', any('Fang' in f or 'FangSong' in f.lower() for f in fonts), f'{sorted(fonts)}')
    ck('5号(10.5pt)字号存在', any(abs(s - 10.5) < 0.1 for s in sizes), f'{sorted(sizes)[:8]}')
    ck('横排(存在 宽>高 的文本行)', ltr_ok_pages > 0, f'{ltr_ok_pages} 行')
    ck('双栏(抽样页左右两簇 x)', col_ok_pages >= max(1, len(sampled) // 2),
       f'{col_ok_pages}/{len(sampled)} 页')

    # 页码：抽 "— N —" 或纯数字页脚
    pages_with_num, nums = 0, []
    for i in range(N):
        t = doc[i].get_text('text')
        m = re.findall(r'—\s*(\d+)\s*—', t)
        if m:
            pages_with_num += 1
            nums.append(int(m[-1]))
    ck('页码存在于多数页', pages_with_num >= N * 0.8, f'{pages_with_num}/{N}')
    ck('页码升序', nums == sorted(nums), f'{nums[:8]}…')
    ck('页码连续无缺', (not nums) or nums == list(range(nums[0], nums[0] + len(nums))),
       f'首={nums[0] if nums else "-"} 末={nums[-1] if nums else "-"} 共{len(nums)}')
    ck('页码无重号', len(nums) == len(set(nums)), f'去重后 {len(set(nums))}')
    doc.close()

    json.dump(rep, open(os.path.join(DIST, 'layout_check.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    for c in rep['checks']:
        print(('  PASS ' if c['pass'] else '  FAIL ') + c['name'] + (f"  [{c['detail']}]" if c['detail'] else ''))
    print('LAYOUT OK' if rep['ok'] else 'LAYOUT FAILED')
    return rep


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--pdf', default=os.path.join(DIST, 'bingyuan_kepu.pdf'))
    a = ap.parse_args()
    check(a.pdf)
