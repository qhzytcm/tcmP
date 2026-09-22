# -*- coding: utf-8 -*-
"""
S51 依【】标记切分病名单元 + 重建「病源/病状/治法」三段结构
容错：】 可能缺失（实测 【2153 / 】1317）→ 名称取「】前」或「至多 8 字且止于标点/数字」
输出 data/pdf3_units.json + dist/pdf3_units_report.json
"""
import os, re, json
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, 'dist')
S = json.load(open(os.path.join(DIST, 'pdf3_stream.json'), encoding='utf-8'))['full']
print('流字数:', len(S))

RX_S = re.compile(r'病源')
RX_Z = re.compile(r'病状')
RX_F = re.compile(r'治法')
BAD = re.compile(r'[0-9０-９一二三四五六七八九十百]+$')      # 名称尾部若为数字→可疑


def parse_name(seg):
    """从【 之后取病名"""
    j = seg.find('】')
    if 0 <= j <= 10:
        return seg[:j], seg[j + 1:]
    # 无】 → 取前若干字，止于非病名用字
    m = re.match(r'([\u4e00-\u9fff]{1,8}?)(?=[，,。；;：:（(0-9０-９（]|病源|病状|治法)', seg)
    if m:
        return m.group(1), seg[m.end():]
    return seg[:5], seg[5:]


def split_sections(body):
    """按 病源/病状/治法 切段（首现位置）"""
    pos = {}
    for k, rx in (('病源', RX_S), ('病状', RX_Z), ('治法', RX_F)):
        m = rx.search(body)
        if m:
            pos[k] = m.start()
    if not pos:
        return {'全': body}
    order = sorted(pos.items(), key=lambda kv: kv[1])
    out = {}
    for i, (k, p) in enumerate(order):
        e = order[i + 1][1] if i + 1 < len(order) else len(body)
        seg = body[p:e]
        if seg.startswith(k):                    # 剥掉标记本身，避免「病源：病源…」
            seg = seg[len(k):]
        out[k] = seg
    # 首段之前的内容归入首段
    if order[0][1] > 0:
        out[order[0][0]] = body[:order[0][1]] + out[order[0][0]]
    return out


def main():
    idx = [m.start() for m in re.finditer('【', S)]
    units = []
    for i, p in enumerate(idx):
        end = idx[i + 1] if i + 1 < len(idx) else len(S)
        seg = S[p + 1:end]
        name, body = parse_name(seg)
        name = name.strip()
        if not name or len(name) > 12:
            continue
        sec = split_sections(body)
        units.append({'name': name, 'body': body, 'sections': sec,
                      'has': {k: (k in sec) for k in ('病源', '病状', '治法')}})
    from collections import Counter
    st = Counter()
    for u in units:
        for k in ('病源', '病状', '治法'):
            if u['has'][k]:
                st[k] += 1
        st['三段齐备'] += all(u['has'].values())
    json.dump(units, open(os.path.join(ROOT, 'data', 'pdf3_units.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=0)
    rep = {'units': len(units), 'sections': dict(st),
           'sample': [{'name': u['name'], 'len': len(u['body']),
                       'has': u['has'], 'head': u['body'][:70]} for u in units[:12]]}
    json.dump(rep, open(os.path.join(DIST, 'pdf3_units_report.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    print('病名单元:', len(units))
    print('分段统计:', dict(st))
    for x in rep['sample']:
        print(f"  【{x['name']}】{x['len']}字 {x['has']} | {x['head']}")


if __name__ == '__main__':
    main()
