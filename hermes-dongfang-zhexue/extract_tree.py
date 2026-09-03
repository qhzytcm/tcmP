# -*- coding: utf-8 -*-
"""Extract chapter body into a TREE structure: chapter -> section(2.1) -> subsection(2.1.1) -> item(2.1.1.1) -> paragraphs."""
import openpyxl, json, re

SRC = r'C:\Users\DELL\Desktop\东方哲学概论.xlsx'
OUT = r'C:\Users\DELL\tcmP\_dump\chapters_tree.json'

CHAPTERS = [
    ('1感知', 1, '感知在地', 115),
    ('2行规', 2, '仿行立规', 112),
    ('3数理', 3, '抽象建模', 112),
    ('4传承', 4, '传承延绵', 112),
    ('5逻辑', 5, '逻辑升维', 118),
    ('6生态', 6, '寰宇共生', 113),
]

HEAD_RE = re.compile(r'^(\d+)\.(\d+)(?:\.(\d+))?(?:\.(\d+))?\s+(.+)$')
CHAP_RE = re.compile(r'^第[一二三四五六]章\s*(.*)$|^第[一二三四五六]节\s*(.*)$')

wb = openpyxl.load_workbook(SRC, data_only=True)

def get_c(row):
    """Return body text: prefer C-column (index 2), fallback D-column (index 3)."""
    v = row[2] if len(row) > 2 else None
    if v is None or str(v).strip() == '':
        v = row[3] if len(row) > 3 else None
    return '' if v is None else str(v).strip()

tree = {}
for sheet, num, title, start in CHAPTERS:
    ws = wb[sheet]
    ch = {'num': num, 'title': title, 'intro': [], 'sections': []}
    cur_sec = None
    cur_sub = None
    cur_item = None
    pending_intro = None  # intro paragraph awaiting a heading
    for row in ws.iter_rows(min_row=start, values_only=True):
        text = get_c(row)
        if not text:
            continue
        m = HEAD_RE.match(text)
        if m:
            a, b, c, d, name = m.group(1), m.group(2), m.group(3), m.group(4), m.group(5)
            if c is None:
                # section 2.1
                cur_sec = {'code': '%s.%s' % (a, b), 'title': name, 'intro': [], 'subsections': []}
                ch['sections'].append(cur_sec)
                cur_sub = None
                cur_item = None
            elif d is None:
                # subsection 2.1.1
                cur_sub = {'code': '%s.%s.%s' % (a, b, c), 'title': name, 'intro': [], 'items': []}
                if cur_sec is not None:
                    cur_sec['subsections'].append(cur_sub)
                cur_item = None
            else:
                # item 2.1.1.1
                cur_item = {'code': '%s.%s.%s.%s' % (a, b, c, d), 'title': name, 'paras': []}
                if cur_sub is not None:
                    cur_sub['items'].append(cur_item)
        else:
            m2 = CHAP_RE.match(text)
            if m2:
                nm = m2.group(1) or m2.group(2) or ''
                ch['title'] = nm
                continue
            # paragraph text -> attach to deepest current node
            if cur_item is not None:
                cur_item['paras'].append(text)
            elif cur_sub is not None:
                cur_sub['intro'].append(text)
            elif cur_sec is not None:
                cur_sec['intro'].append(text)
            else:
                ch['intro'].append(text)
    tree[sheet] = ch
    print('%s: %d sections, %d subsections, %d items' % (
        sheet, len(ch['sections']),
        sum(len(s['subsections']) for s in ch['sections']),
        sum(len(sb['items']) for s in ch['sections'] for sb in s['subsections'])))

with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(tree, f, ensure_ascii=False, indent=1)
print('saved', OUT)
