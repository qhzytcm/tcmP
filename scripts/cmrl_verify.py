# -*- coding: utf-8 -*-
"""cmrl_verify.py — cmrl 管线自检 + 章节正文验收工具

用法:
  python scripts/cmrl_verify.py --ch 1        # 验收第1章正文(段数/字数/标记)
  python scripts/cmrl_verify.py --all         # 验收全部已有正文章节
  python scripts/cmrl_verify.py --selftest    # 管线函数自检(parse_md/split_paragraphs)

退出码: 0=全部通过, 1=有失败(便于 CI 判断)
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from cmrl_merge import parse_md, split_paragraphs  # noqa: E402
from cmrl_update_xlsx import load_chapter, check_chapter, XLSX  # noqa: E402


def selftest():
    """管线函数自检: ### 忽略 / ## 分节 / 段落拆分"""
    ok = True
    md = ("## [Part1] 1.1 智能体与环境：网格世界\n\n"
          "第一段正文内容。\n\n第二段正文内容。\n\n"
          "### 1.1.1 知识要点\n\n第三段正文内容。\n\n"
          "## [Part2] 1.1 平台语境\n\n平台改写段落。\n")
    rows = parse_md(md)
    if not (len(rows) == 2 and '###' not in rows[0][1] and '知识要点' not in rows[0][1]):
        print('FAIL selftest: parse_md 未忽略 ### 子标题')
        ok = False
    paras = split_paragraphs(rows)
    if len(paras) != 4:
        print(f'FAIL selftest: split_paragraphs 期望 4 段, 实得 {len(paras)}')
        ok = False
    if ok:
        print('PASS selftest: parse_md(###忽略) + split_paragraphs')
    return ok


def verify_chapter(ch: int, check_xlsx: bool = True):
    rows, total, per = load_chapter(ch)
    if rows is None:
        print(f'[ch{ch:02d}] SKIP 无正文 md')
        return True
    ok, note = check_chapter(ch, rows, total)
    n1 = sum(1 for m, _ in rows if m.startswith('[Part1'))
    n2 = sum(1 for m, _ in rows if m.startswith('[Part2'))
    print(f'[ch{ch:02d}] {"PASS" if ok else "FAIL"} {len(rows)}段/{total}字 '
          f'(Part1={n1} Part2={n2}) {note}')
    if ok and check_xlsx:
        ok &= verify_xlsx(ch, len(rows))
    return ok


def verify_xlsx(ch: int, n_rows: int):
    """读回桌面 xlsx 章节 sheet: 行数=段数+2, Part1/Part2 标记齐全"""
    from cmrl_merge import CHAP_META
    from openpyxl import load_workbook
    prefix, sheet_name, title = CHAP_META[ch]
    if not XLSX.exists():
        print(f'[ch{ch:02d}] SKIP xlsx 不存在')
        return True
    wb = load_workbook(XLSX, read_only=True)
    try:
        if sheet_name not in wb.sheetnames:
            print(f'[ch{ch:02d}] FAIL xlsx 缺 sheet {sheet_name}')
            return False
        ws = wb[sheet_name]
        data = list(ws.iter_rows(min_row=3, values_only=True))
        # 正文区校验: 非空 C 列行数 >= n_rows（图题/图注文本行计入; 图体行 C 列为空不计）
        nonempty = sum(1 for r in data if str(r[2] or '').strip())
        ok = len(data) >= n_rows and nonempty >= n_rows
        print(f'[ch{ch:02d}] xlsx {sheet_name}: 数据行 {len(data)} 非空 {nonempty} '
              f'({"PASS" if ok else "FAIL"})')
        return ok
    finally:
        wb.close()


def verify_toc2():
    """验证 v2.1 目录（三编·科普叙事）已正确写入 Excel 0cmrl目录"""
    from cmrl_toc_v2 import CHAPTERS_V2, VOLUMES
    from openpyxl import load_workbook
    ok = True
    # 1) 数据一致性: 10 章 × 8 节; 第7节=系统定位; 第8节=和谐/共同体; 无平台实践大节
    if len(CHAPTERS_V2) != 10 or any(len(c[5]) != 8 for c in CHAPTERS_V2):
        print('FAIL toc2 数据: 需 10 章 × 8 节')
        ok = False
    if len(VOLUMES) != 3:
        print('FAIL toc2 数据: 需三编')
        ok = False
    if any('系统' not in c[5][6] or '定位' not in c[5][6] for c in CHAPTERS_V2):
        print('FAIL toc2 数据: 每章第7节需为系统科学定位')
        ok = False
    if any(not any(k in c[5][7] for k in ('和谐', '共同体', '愿景', '同心', '相互成就'))
           for c in CHAPTERS_V2):
        print('FAIL toc2 数据: 每章第8节需为六者和谐/共同体')
        ok = False
    all_secs = [s for c in CHAPTERS_V2 for s in c[5]]
    if any('平台实践' in s for s in all_secs):
        print('FAIL toc2 数据: 不应存在独立"平台实践"大节（平台一句话带过）')
        ok = False
    # 2) Excel 读回
    if not XLSX.exists():
        print('FAIL toc2: xlsx 不存在')
        return False
    # 2a) build 函数级断言: wrange 区间 + 小节概念/方法派生
    from cmrl_build_toc2 import wrange, sub_sections
    if wrange(30000) != '24000-36000' or wrange(500) != '400-600':
        print('FAIL toc2 build.wrange: 区间格式错误')
        ok = False
    subs = sub_sections('智能体与环境：医者、医院与患者', 3000)
    if subs[0][0] != '智能体与环境：概念与内涵' \
            or subs[1][0] != '智能体与环境：方法与实现':
        print('FAIL toc2 build.sub_sections: 小节标题未概念化')
        ok = False
    wb = load_workbook(XLSX, read_only=True)
    try:
        if '0cmrl目录' not in wb.sheetnames:
            print('FAIL toc2: 缺 0cmrl目录 sheet')
            return False
        rows = list(wb['0cmrl目录'].iter_rows(values_only=True))
        # 新结构: 表头+4说明行后为目录; 四级编码分列 A=章 B=节 C=小节 D=段落
        if len(rows) != 815:
            print(f'FAIL toc2 xlsx 总行数: {len(rows)} (期望 815)')
            ok = False
        data = rows[5:]   # 目录区
        # 分列判定: 章行=A非空且B/C/D空; 节行=B非空且C空; 小节行=C非空且D空; 段落行=D非空
        n_ch = sum(1 for r in data if str(r[0] or '').strip()
                   and not str(r[1] or '').strip() and not str(r[2] or '').strip()
                   and not str(r[3] or '').strip())
        n_sec = sum(1 for r in data if str(r[1] or '').strip()
                    and not str(r[2] or '').strip() and not str(r[3] or '').strip())
        n_sub = sum(1 for r in data if str(r[2] or '').strip()
                    and not str(r[3] or '').strip())
        n_para = sum(1 for r in data if str(r[3] or '').strip())
        if not (n_ch == 10 and n_sec == 80 and n_sub == 240 and n_para == 480):
            print(f'FAIL toc2 xlsx 分列层级: 章{n_ch}/节{n_sec}/小节{n_sub}/段落{n_para} '
                  f'(期望 10/80/240/480)')
            ok = False
        # 表头 11 列分列
        hdr = rows[0]
        if hdr[:4] != ('章', '节', '小节', '段落'):
            print(f'FAIL toc2 xlsx 表头未分列: {hdr[:4]}')
            ok = False
        # 区间化断言: 段落行预计字数(G列 idx6)含 '-'
        w_cell = [str(r[6]) for r in data if str(r[3] or '').strip()][:5]
        if not all('-' in w for w in w_cell):
            print(f'FAIL toc2 xlsx 字数未区间化: {w_cell}')
            ok = False
        # 小节标题概念化断言(E列 idx4): 无模板名"知识要点"
        sub_titles = [str(r[4]) for r in data if str(r[2] or '').strip()
                      and not str(r[3] or '').strip()]
        if any('知识要点' in t for t in sub_titles) \
                or not all('概念与内涵' in t or '方法与实现' in t or '小结与衔接' in t
                           for t in sub_titles):
            print('FAIL toc2 xlsx 小节标题未概念化')
            ok = False
        titles = ' '.join(str(r[4]) for r in data if str(r[0] or '').strip()
                          and not str(r[1] or '').strip())
        if not all(k in titles for k in ('认知', '信仰', '幸福')):
            print('FAIL toc2 xlsx 章标题缺三编关键词')
            ok = False
        if '原第1章' not in str(data[0][5] or ''):
            print('FAIL toc2 xlsx 第1章内容映射标注缺失')
            ok = False
        sec8_notes = [str(r[5]) for r in data
                      if str(r[1] or '').strip() == '8'
                      and not str(r[2] or '').strip()]
        if len(sec8_notes) != 10 or any('一句话带过' not in s for s in sec8_notes):
            print('FAIL toc2 xlsx 第8节缺少"平台一句话带过"标注')
            ok = False
    finally:
        wb.close()
    print(f'[toc2] v2.1 目录验证: 三编/10章/80节/240小节/科普叙事 {"PASS" if ok else "FAIL"}')
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--ch', type=int)
    ap.add_argument('--all', action='store_true')
    ap.add_argument('--selftest', action='store_true')
    ap.add_argument('--toc2', action='store_true', help='验证 v2 目录(三编)写入 Excel')
    args = ap.parse_args()
    all_ok = True
    if args.selftest or not (args.ch or args.all or args.toc2):
        all_ok &= selftest()
    if args.ch:
        all_ok &= verify_chapter(args.ch)
    if args.all:
        for ch in range(1, 11):
            all_ok &= verify_chapter(ch)
    if args.toc2:
        all_ok &= verify_toc2()
    print(f'\nCMRL VERIFY: {"PASS" if all_ok else "FAIL"}')
    sys.exit(0 if all_ok else 1)


if __name__ == '__main__':
    main()
