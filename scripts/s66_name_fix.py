# -*- coding: utf-8 -*-
"""
S66 词目名定向校正 + 续文合并（用户逐条校验）
  · MERGE_TAIL: 把被误拆的「续文单元」并入其宿主条目（idx8 → idx7 七恶）
  · NAME_FIX  : 用户裁定的正名（索引按**合并后**的单元序列）
数据源：data/pdf3_units_v2.json；由 s54 调用（亦可独立运行做后处理）
"""
import json, os, sys

# 续文合并：{被并入的单元 idx: 宿主 idx}
MERGE_TAIL = {8: 7}

# 用户逐条校验的正名：{合并后 idx: 正名}
NAME_FIX = {
    6: '七恶',        # 0007
    7: '七恶',        # 0008（并入原 idx8 续文）
    9: '七窍出血',    # 0009（OCR「七出血」，补「窍」）
    10: '九子疡',     # 0010（OCR「九子瘦二七九」）
    11: '九死',       # 0011（OCR「九痕」）
}


def apply(units):
    """返回 (新单元表, 合并数, 改名数)；索引重映射表 remap: 旧idx → 新idx（-1 表示已并入）"""
    remap = {}
    out = []
    for i, u in enumerate(units):
        if i in MERGE_TAIL:
            host = MERGE_TAIL[i]
            assert 0 <= host < len(out), f'宿主 {host} 不存在或已被合并'
            out[host]['body'] = (out[host]['body'] or '') + (u['body'] or '')
            # 合并段标记
            for k, v in (u.get('has') or {}).items():
                if v:
                    out[host].setdefault('has', {})[k] = True
            for k in ('病源', '病状', '治法'):
                if k in (u.get('sections') or {}) and k not in (out[host].get('sections') or {}):
                    out[host].setdefault('sections', {})[k] = u['sections'][k]
            remap[i] = -1
            continue
        remap[i] = len(out)
        out.append(dict(u))
    nfix = 0
    for idx, nm in NAME_FIX.items():
        ni = remap.get(idx, -1)
        if ni >= 0 and out[ni].get('name') != nm:
            out[ni]['name'] = nm
            nfix += 1
    return out, len(MERGE_TAIL), nfix, remap


if __name__ == '__main__':
    ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    fp = os.path.join(ROOT, 'data', 'pdf3_units_v2.json')
    U = json.load(open(fp, encoding='utf-8'))
    n0 = len(U)
    U2, nm, nf, remap = apply(U)
    json.dump(U2, open(fp, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f'单元 {n0} → {len(U2)} | 合并 {nm} | 改名 {nf}')
    for i, u in enumerate(U2[:12]):
        print(f'  {i+1:04d} 【{u["name"]}】{len(u["body"])}字')
