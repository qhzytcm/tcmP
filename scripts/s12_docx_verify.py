# -*- coding: utf-8 -*-
"""
S12 docx 页码标注校验（稳健版 v2）
① Word COM 只做：打开 docx、Repaginate、导出 PDF（Word 自身分页）
② 纯 Python：从 docx XML 用**域状态机**读 PAGEREF 值（兼容 fldChar 拆散的 instrText）
           用 pymupdf 在导出 PDF 里定位词条实际页
③ 断言 标注页 == 实际页；页码 ∈ 1..总页（证明非原著）
输出：dist/docx_verify.json
"""
import os, re, json, argparse, zipfile, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, 'dist'); os.makedirs(DIST, exist_ok=True)
DESKTOP = r'C:\Users\DELL\Desktop'
WD_EXPORT_PDF = 17
TOK = re.compile(r'<w:fldChar[^>]*w:fldCharType="(\w+)"|<w:instrText[^>]*>(.*?)</w:instrText>|<w:t[^>]*>(.*?)</w:t>', re.S)


def export_pdf(docx, pdf):
    import win32com.client as w32
    import pythoncom
    last = None
    for attempt in range(4):
        word = None
        try:
            pythoncom.CoInitialize()
            word = w32.DispatchEx('Word.Application'); word.Visible = False
            word.DisplayAlerts = 0
            try:
                word.Options.UpdateFieldsAtPrint = False
            except Exception:
                pass
            d = word.Documents.Open(docx, ReadOnly=True)
            time.sleep(20)                      # 打开含 2800+ 域时 Word 需后台重算，先静置
            for _ in range(4):
                try:
                    d.Repaginate(); break
                except Exception:
                    time.sleep(5)
            pages = d.ComputeStatistics(2)
            if os.path.exists(pdf):
                os.remove(pdf)
            d.ExportAsFixedFormat(pdf, WD_EXPORT_PDF)
            d.Close(False)
            return pages
        except Exception as e:
            last = e
            time.sleep(4)
        finally:
            try:
                if word is not None:
                    word.Quit()
            except Exception:
                pass
    raise last


def read_pagerefs(docx):
    """域状态机：begin 收指令 → separate 收结果 → end 落库。兼容指令被拆成多段。"""
    xml = zipfile.ZipFile(docx).read('word/document.xml').decode('utf-8')
    out, instr, result, state = {}, [], [], None
    for m in TOK.finditer(xml):
        if m.group(1):                                   # fldChar
            t = m.group(1)
            if t == 'begin':
                instr, result, state = [], [], 'instr'
            elif t == 'separate':
                state = 'result'
            elif t == 'end':
                code = ''.join(instr)
                mm = re.search(r'PAGEREF\s+(\S+)', code)
                if mm:
                    num = re.sub(r'[^0-9]', '', ''.join(result))
                    if num:
                        out.setdefault(mm.group(1).strip(), int(num))
                instr, result, state = [], [], None
        elif state == 'instr' and m.group(2) is not None:
            instr.append(m.group(2))
        elif state == 'result' and m.group(3) is not None:
            result.append(m.group(3))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--docx', default=os.path.join(DESKTOP, '病源辞典_简体科普版_上下文重构V3.docx'))
    ap.add_argument('--terms', default=os.path.join(ROOT, 'data', 'bingyuan_terms_v5.json'))
    a = ap.parse_args()
    import fitz

    rep = {'docx': os.path.basename(a.docx), 'checks': [], 'ok': True}

    def ck(n, c, d=''):
        rep['checks'].append({'name': n, 'pass': bool(c), 'detail': str(d)})
        if not c:
            rep['ok'] = False

    terms = json.load(open(a.terms, encoding='utf-8'))
    heads = {t['no']: t['head'] for t in terms}
    pdf = os.path.join(DIST, '_v3_export.pdf')

    pages = export_pdf(a.docx, pdf)
    rep['pages'] = pages
    ck('docx 总页 > 0', pages > 0, f'{pages} 页')

    doc = fitz.open(pdf)
    texts = [doc[i].get_text('text') for i in range(doc.page_count)]
    doc.close()
    ck('导出 PDF 页数 == Word 分页数', len(texts) == pages, f'{len(texts)} vs {pages}')

    claims = read_pagerefs(a.docx)
    ck('PAGEREF 域读取(≥1800)', len(claims) >= 1800, f'{len(claims)} 个域')

    def first_page(pat, start=0):
        rx = re.compile(pat)
        for i in range(start, len(texts)):
            if rx.search(texts[i]):
                return i + 1
        return None

    si = first_page(r'一、词条索引（按笔画序')
    ss = first_page(r'二、主题词索引（subject-index：')
    sb = first_page(r'0001\s+' + re.escape(heads.get('0001', '')), (ss or 1) - 1)
    for key, label, act in [('sec_index', '词条索引', si), ('sec_subject', '主题词索引', ss), ('sec_body', '正文', sb)]:
        claim = claims.get(key)
        ck(f'目录「{label}」页码正确', claim is not None and claim == act, f'标注P{claim} 实际P{act}')

    body_start = (sb or 1) - 1
    actual = {}
    for i, t in enumerate(texts[body_start:], start=body_start):
        for m in re.finditer(r'(?<!\d)(\d{4})[ \u3000]+([^\n]+)', t):
            no = m.group(1)
            if no in actual:
                continue
            seg = re.sub(r'［ICD-11[^］]*］', '', m.group(2))       # 去 ICD 标注
            cand = re.sub(r'[\s\u3000]', '', seg)                  # 去空白（拉丁/CJK 混排会插空格）
            exp = re.sub(r'[\s\u3000]', '', heads.get(no, ''))
            if exp and cand.startswith(exp):
                actual[no] = i + 1
    bad = [(no, claims.get('e' + no), actual.get(no)) for no in heads
           if claims.get('e' + no) != actual.get(no)]
    ck(f'词条索引页码全部正确({len(heads)}条)', len(bad) == 0 and len(actual) >= 1800,
       f'错 {len(bad)}: {bad[:5]} | 定位 {len(actual)}')

    nums = list(claims.values())
    ck('页码非原著(落在 1..总页内)', bool(nums) and all(1 <= x <= pages for x in nums),
       f'max={max(nums) if nums else "-"} 总页={pages}')

    json.dump(rep, open(os.path.join(DIST, 'docx_verify.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    for c in rep['checks']:
        print(('  PASS ' if c['pass'] else '  FAIL ') + c['name'] + (f"  [{c['detail']}]" if c['detail'] else ''))
    print('DOCX VERIFY OK' if rep['ok'] else 'DOCX VERIFY FAILED')
    return rep


if __name__ == '__main__':
    main()
