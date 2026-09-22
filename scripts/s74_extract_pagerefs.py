# -*- coding: utf-8 -*-
"""
S74 从 Word 处理过的副本中**抽出已解析的真实页码**（PAGEREF 域缓存值）→ JSON
用途：Word 保存会改写字体/样式，故不能直接交付 Word 处理后的 docx；
     改为「Word 算页码 → 抽值 → 回注到 s72 干净重出的文件」两遍法。
输出：dist/pdf3_pagerefs.json  {书签名: 页码}
"""
import os, re, json, sys, zipfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, 'dist')


def extract(docx):
    """兼容两种形态：
    ① python-docx 写的 fldSimple：<w:fldSimple w:instr=" PAGEREF name \\h ">…<w:t>N</w:t>
    ② Word 保存后转成的复杂域：fldChar begin → instrText → separate → <w:t>N</w:t> → end
    """
    z = zipfile.ZipFile(docx)
    x = z.read('word/document.xml').decode('utf-8')
    out = {}
    # ① fldSimple
    for m in re.finditer(r'<w:fldSimple[^>]*w:instr="\s*PAGEREF\s+(\S+)[^"]*"[^>]*>(.*?)</w:fldSimple>',
                         x, re.S):
        t = re.findall(r'<w:t[^>]*>([^<]*)</w:t>', m.group(2))
        if t and t[0].strip().isdigit():
            out[m.group(1)] = int(t[0].strip())
    # ② 复杂域：instrText 之后、end 之前的第一个数字
    for m in re.finditer(r'<w:instrText[^>]*>\s*PAGEREF\s+(\S+)\s[^<]*</w:instrText>(.*?)'
                         r'<w:fldChar[^>]*w:fldCharType="end"', x, re.S):
        t = re.findall(r'<w:t[^>]*>\s*(\d+)\s*</w:t>', m.group(2))
        if t:
            out[m.group(1)] = int(t[-1])
    return out


if __name__ == '__main__':
    src = sys.argv[1] if len(sys.argv) > 1 else r'C:\Users\DELL\Desktop\BYCD.docx'
    d = extract(src)
    print('抽出页码:', len(d))
    e = {k: v for k, v in d.items() if re.fullmatch(r'e\d{4}', k)}
    print('  词条域:', len(e))
    vals = sorted(e.values())
    print('  页码范围:', vals[0] if vals else '-', '~', vals[-1] if vals else '-')
    print('  升序违规:', sum(1 for a, b in zip(vals, vals[1:]) if b < a))
    print('  样本:', [f'{k}={v}' for k, v in list(e.items())[:5]])
    json.dump(d, open(os.path.join(DIST, 'pdf3_pagerefs.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=0)
    print('→ dist/pdf3_pagerefs.json')
