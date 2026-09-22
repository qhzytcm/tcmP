# -*- coding: utf-8 -*-
"""
constitution.model —— 阴阳二十五人 参数化生成式模型（ConstitutionModel）
======================================================================
把《灵枢·阴阳二十五人》(LS64) + 《灵枢·五音五味》(LS65) + 《素问·上古天真论》(SW01)
形式化为一个**参数化生成式模型**：

  正向生成（generate）：体质型 → 表型参数向量（形/色/音/经/情态/血气/毛发/易感/调治）
  逆转推理（infer）   ：表型观测（形色音经毛发）→ 25 型归属排序
  性别参数（compare_gender）：男性分类参数 vs 女性分类参数 同异对照

参数空间（与 etiology 病因层同尺，5 区间 L1-L5 + 高斯归一化）：
  B = (xi 五形, yi 五音, se 五色, jing 经络, V_qi 气量, V_xue 血量, hai 须髯, neng 时令)

用法：
    from constitution.model import ConstitutionModel
    m = ConstitutionModel()
    p = m.generate('木', '上角', sex='male')       # 生成某型表型参数
    r = m.infer({'color': '青', 'yin': '角', 'shape': ['小头', '长面']})  # 逆转推理
    print(m.report_gender())                        # 男女参数同异对照
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, List, Optional

from constitution import framework as F

DATA_DIR = Path(os.path.dirname(__file__)) / 'data'

# 经络 → 三阴三阳（取六经气血常数用）
JING_SANYIN = {
    'LR': '厥阴', 'GB': '少阳', 'HT': '少阴', 'SI': '太阳',
    'SP': '太阴', 'ST': '阳明', 'LU': '太阴', 'LI': '阳明',
    'KI': '少阴', 'BL': '太阳',
}
# 经气血常数 → 数值偏移（多=+0.10 / 少=-0.10）
QW = {'多': +0.10, '少': -0.10}


class ConstitutionModel:
    """阴阳二十五人体质参数化生成式模型"""

    def __init__(self, data_dir: Optional[Path] = None):
        d = Path(data_dir) if data_dir else DATA_DIR
        self.kb = json.loads((d / 'wu_xing_25.json').read_text(encoding='utf-8'))
        self.xing = self.kb['xing']
        self.types = self.kb['types25']
        self.gender = self.kb['gender']

    # ── 0. 索引 ────────────────────────────────────────────────
    def all_types(self) -> List[Dict]:
        """展开 25 型为扁平列表"""
        out = []
        for xing in F.XING_ORDER:
            for t in self.types[xing]:
                out.append({'xing': xing, **t})
        return out

    def find(self, name: str) -> Optional[Dict]:
        for t in self.all_types():
            if t['name'] == name or t['name'].startswith(name):
                return t
        return None

    # ── 1. 正向生成：体质型 → 表型参数向量 ────────────────────
    def generate(self, xing: str, subtype: Optional[str] = None,
                 sex: str = 'male') -> Dict:
        """生成指定体质型（默认主型=该行第 1 型）的完整表型参数。"""
        types = self.types[xing]
        t = None
        if subtype:
            for cand in types:
                if cand['name'].startswith(subtype) or subtype in cand['name']:
                    t = cand
                    break
        if t is None:
            t = types[0]                                   # 主型
        x = self.xing[xing]
        base = F.GENDER_BASE.get(sex, F.GENDER_BASE['male'])

        # 血气：性别基线 ⊕ 该经气血常数偏移
        sy = JING_SANYIN.get(t['jing'], '太阴')
        const = F.QI_XUE_CONST.get(sy, {'qi': '多', 'xue': '多'})
        V_qi = round(min(1.0, max(0.0, base['V_qi'] + QW[const['qi']])), 2)
        V_xue = round(min(1.0, max(0.0, base['V_xue'] + QW[const['xue']])), 2)

        # 毛发：男六维（须髯标尺）；女无须
        if base['has_beard']:
            hair = {d: '随血气盛衰' for d in F.HAIR_DIMS}
            hair_note = '须髯俱备——血气外显标尺'
        else:
            hair = {d: ('0(无)' if d in ('髯', '须', '髭', '下毛', '腋毛') else '随血气盛衰')
                    for d in F.HAIR_DIMS}
            hair_note = '无须——冲任不荣口唇'

        # 易感：形色相得 / 年忌
        yi_suscept = self._susceptibility(xing)

        return {
            'code': f'{xing}形·{t["name"]}',
            'sex': sex,
            'xing': xing, 'xing_cn': x['xing_cn'], 'se': x['se'], 'yin': x['yin'],
            'zhu_jing': x['zhu_jing_cn'], 'sub_jing': t['pos'], 'jing_code': t['jing'],
            'tai': t['tai'], 'tai_cn': t['tai_cn'],
            'shape': x['shape'], 'xingqing': x['xingqing'], 'neng': x['neng'],
            'de': x['de'], 'chang': x['chang'],
            'params': {
                'V_qi': V_qi, 'V_qi_lv': F.level_cn(F.level_of(V_qi)),
                'V_xue': V_xue, 'V_xue_lv': F.level_cn(F.level_of(V_xue)),
                '六经气血常数': const, '三阴三阳': sy,
            },
            'hair': hair, 'hair_note': hair_note,
            'is_main_type': 'role' in t,
            'susceptibility': yi_suscept,
            'therapy': {
                '五音': f'{x["yin"]}音（{F.ZANG_CN[x["zang"]]}）',
                '食疗': F.WU_YIN_WU_WEI[x['yin']],
                '经络': f'{x["zhu_jing_cn"]} / {t["jing"]}',
            },
        }

    def _susceptibility(self, xing: str, color_se: Optional[str] = None) -> Dict:
        """形色关系（LS64）：形色相得者富贵大乐；形胜色/色胜形者逢年忌感邪则病。"""
        se_wx = {'青': '木', '赤': '火', '黄': '土', '白': '金', '黑': '水'}
        sheng = {'木': '火', '火': '土', '土': '金', '金': '水', '水': '木'}
        ke = {'木': '土', '土': '水', '水': '火', '火': '金', '金': '木'}
        co = color_se or self.xing[xing]['se']
        color_wx = se_wx.get(co, xing)
        if color_wx == xing:
            rel, verdict = '形色相得', '富贵大乐，形质气机调和'
        elif sheng.get(xing) == color_wx or sheng.get(color_wx) == xing:
            rel, verdict = '形色相生', '相得（一形一色相生），安'
        elif ke.get(xing) == color_wx:
            rel, verdict = '形胜色', '逢年忌感邪则病，失则忧'
        elif ke.get(color_wx) == xing:
            rel, verdict = '色胜形', '逢年忌感邪则病，失则忧'
        else:
            rel, verdict = '形色待辨', '需别五色而定'
        return {
            '形色关系': f'{rel}（形{xing}·色{co}）',
            '断语': verdict,
            '时令': self.xing[xing]['neng'],
            '年忌': F.NIAN_JI,
            '年忌语': '大忌常加七岁…当此之时，无为奸事，是谓年忌（LS64）',
        }

    # ── 2. 逆转推理：表型观测 → 25 型排序 ─────────────────────
    def infer(self, obs: Dict) -> Dict:
        """obs: {color, yin, jing, shape:[...], sex, beard}"""
        scored = []
        for t in self.all_types():
            x = self.xing[t['xing']]
            s, why = 0.0, []
            if obs.get('color') and obs['color'] == x['se']:
                s += 3.0; why.append(f'色{x["se"]}✔')
            if obs.get('yin') and obs['yin'] == x['yin']:
                s += 3.0; why.append(f'音{x["yin"]}✔')
            if obs.get('jing'):
                if obs['jing'] == t['jing'] and t['jing'] == x['zhu_jing']:
                    s += 3.0; why.append('主经✔(主型)')
                elif obs['jing'] == x['zhu_jing']:
                    s += 2.5; why.append('主经✔')
                elif obs['jing'] == t['jing']:
                    s += 2.0; why.append('亚型经✔')
            if obs.get('shape'):
                for kw in obs['shape']:
                    if kw and kw in x['shape']:
                        s += 1.0; why.append(f'形[{kw}]✔')
            # 位置精辨（左右上下部，LS64「比于左/右足少阳之上/下」）
            if obs.get('pos') and obs['pos'] in t['pos']:
                s += 1.5; why.append(f'位[{obs["pos"]}]✔')
            # 主型加成（形色音经皆合则禀该行最全，LS64「禀气最全」）
            if 'role' in t and s > 0:
                s += 0.5; why.append('主型加成')
            if s > 0:
                scored.append({'code': f'{t["xing"]}形·{t["name"]}',
                               'xing': t['xing'], 'score': s, 'why': why})
        scored.sort(key=lambda r: r['score'], reverse=True)
        top = scored[:5]
        return {
            'obs': obs,
            'ranked': top,
            'main': top[0] if top else None,
            'gender_note': ('观测含须髯→男' if obs.get('beard')
                            else '无须/未标须髯→疑女或须髯缺失'),
        }

    # ── 3. 性别参数对照（男女分类参数 同异）───────────────────
    def compare_gender(self) -> Dict:
        rows = self.gender['compare']
        same = [r for r in rows if r['same']]
        diff = [r for r in rows if not r['same']]
        return {'same': same, 'diff': diff, 'all': rows}

    # ── 4. 九类 Hermes 独到思考（模型理论骨架）───────────────
    def hermes9(self) -> List[Dict]:
        return self.kb['hermes9']

    # ── 5. 模型预测疾病易感性（五形 × 性别 × 形色 × 年忌）────
    def predict_susceptibility(self, xing: str, subtype: Optional[str] = None,
                               sex: str = 'male', color_se: Optional[str] = None) -> Dict:
        """按五形主脏+性别修饰+形色相得+年忌，输出疾病易感画像。"""
        s = self.kb['susceptibility'][xing]
        rel = self._susceptibility(xing, color_se)
        # 形色相克 → 易感整体上浮
        risk = '基线' if ('相得' in rel['形色关系'] or '相生' in rel['形色关系']) else '上浮(形色相克)'
        # 按性别取"性别修饰"分句（sex_mod 形如「女：…；男：…」）
        want = '女' if sex in ('female', '女', 'f') else '男'
        sex_specific = next((c.strip() for c in s['sex_mod'].split('；') if c.strip().startswith(want)),
                            s['sex_mod'])
        return {
            'code': f'{xing}形{("·" + subtype) if subtype else ""}',
            'sex': sex,
            'zang': s['zang'], 'jing': s['jing'], 'core_patho': s['core_patho'],
            'diseases': s['diseases'], 'modern': s['modern'],
            'sex_mod': s['sex_mod'], 'sex_specific': sex_specific, 'high_window': s['high_window'],
            'form_color': rel['形色关系'], 'risk_level': risk,
            'nian_ji': F.NIAN_JI,
        }

    def susceptibility_all(self) -> List[Dict]:
        """五形疾病易感全表（模型预测疾病易感性）"""
        out = []
        for x in F.XING_ORDER:
            s = self.kb['susceptibility'][x]
            out.append({'xing': x, 'zang': s['zang'], 'jing': s['jing'],
                        'core_patho': s['core_patho'], 'diseases': s['diseases'],
                        'modern': s['modern'], 'sex_mod': s['sex_mod'],
                        'high_window': s['high_window']})
        return out

    # ── 6. 落地路线图 ──────────────────────────────────────────
    def roadmap(self) -> List[Dict]:
        """模型落地路线图（阶段 → 交付 → 依赖）"""
        return [
            {'phase': 'P1 契约与数据', 'deliver': 'framework.py 符号体系 + wu_xing_25.json(25型/男女/易感)',
             'dep': '桌面四文件素材', 'status': '已完成'},
            {'phase': 'P2 生成式引擎', 'deliver': 'ConstitutionModel：generate()正向 / infer()逆转',
             'dep': 'P1', 'status': '已完成'},
            {'phase': 'P3 性别参数层', 'deliver': '男女血气/须髯/节律参数化 + report_gender()',
             'dep': 'P1 LS65/LS64/SW01', 'status': '已完成'},
            {'phase': 'P4 疾病易感层', 'deliver': 'predict_susceptibility()：五形×性别×形色×年忌',
             'dep': 'Hermes第3/4/6条理解', 'status': '已完成'},
            {'phase': 'P5 与病因层耦合', 'deliver': 'Φ_total = Φ_病因[E,P,Z]·B_体质 增益因子',
             'dep': 'etiology/ 模块', 'status': '待接线'},
            {'phase': 'P6 数字人接入', 'deliver': 'sage-api /constitution 端点 + 25型问诊对话流',
             'dep': 'P4/P5 + sage-api', 'status': '待开发'},
            {'phase': 'P7 表型组学数据化', 'deliver': '毛发六维/面色/体型 → 可测量标尺(体表生物标志物)',
             'dep': 'Hermes第5/7条理解', 'status': '规划中'},
            {'phase': 'P8 临床验证', 'deliver': 'A型(火形)-心血管回顾性队列验证',
             'dep': 'Hermes第6条 + 医院数据', 'status': '规划中'},
        ]

    # ══════════════════════════════════════════════════════════
    # V2 术数层：双层进制 · 60甲子 · 男8女7 · 左右镜像 · 两预测目标
    # ══════════════════════════════════════════════════════════

    # ── 7. 阴阳五行双层进制 ────────────────────────────────────
    def dual_radix(self) -> Dict:
        """阴阳(2进制) ⊗ 五行(5进制) = 10 → 天干；天干(10) × 地支(12) → 60甲子。"""
        return {
            'radix_low': {'base': 2, 'bits': F.YINYANG, 'name': '阴阳'},
            'radix_high': {'base': 5, 'bits': F.WUXING, 'name': '五行'},
            'composite': '阴阳(2) × 五行(5) = 10 = 天干',
            'tiangan': F.TIANGAN,
            'dizhi': F.DIZHI,
            'jiazi_cycle': '天干(10) × 地支(12) 的最小公倍数 = 60 = 一甲子',
        }

    def jiazi(self, index: int) -> Dict:
        """按序号取 60 甲子之一（0=甲子 … 59=癸亥）"""
        return F.JIAZI60[index % 60]

    def jiazi_by_year(self, year: int) -> Dict:
        """按公历年取干支（甲子参考年 1984）。"""
        return F.JIAZI60[(year - 1984) % 60]

    def jiazi_lifetime(self, index: int, xing: Optional[str] = None) -> Dict:
        """60甲子 · 个体终身模式：以本命天干五行为『命局主行』，
        与先天禀赋五形比对生克，得终身气运基调。"""
        j = self.jiazi(index)
        ming = j['tg_wx']                      # 命局主行（本命天干五行）
        rel = F.wuxing_relation(ming, xing) if xing else None
        tone = {'同': '本命与禀赋同气，禀性纯粹、易过刚',
                '生': '命生禀赋(泄)，才思外发、易耗散',
                '被生': '禀赋生命局(得助)，根基厚、得扶持',
                '克': '命克禀赋，压力内蕴、易郁',
                '被克': '禀赋克命局，主控力强、易劳心'}.get(rel, '—')
        return {'idx': j['idx'], 'gz': j['gz'], 'shengxiao': j['shengxiao'],
                'tg': j['tg'], 'tg_yy': j['tg_yy'], 'ming_wuxing': ming,
                'dz': j['dz'], 'dz_wx': j['dz_wx'], 'dz_yy': j['dz_yy'],
                'xing_relation': rel, 'lifetime_tone': tone}

    # ── 8. 男8女7 发育阶段性模式 ──────────────────────────────
    def development(self, sex: str, age: int) -> Dict:
        """按性别节律(女7男8)定位发育阶段及所处节点。"""
        stages = F.DEV_STAGES.get(sex, F.DEV_STAGES['male'])
        base = F.LIFE_RHYTHM[sex]['base']
        cur = stages[0]
        for s in stages:
            if age >= s['age']:
                cur = s
        nxt = next((s for s in stages if s['age'] > age), None)
        return {'sex': sex, 'age': age, 'base': base,
                'node_index': (age // base), 'stage': cur['stage'],
                'stage_text': cur['text'], 'stage_age': cur['age'],
                'next_age': (nxt['age'] if nxt else None),
                'tiangui': ('已竭' if age >= F.LIFE_RHYTHM[sex]['tiangui_jie']
                            else ('已至' if age >= F.LIFE_RHYTHM[sex]['tiangui_zhi'] else '未至'))}

    # ── 9. 左右镜像 ────────────────────────────────────────────
    def mirror(self, sex: str) -> Dict:
        return F.MIRROR.get(sex, F.MIRROR['male'])

    def subtype_side_sex(self, subtype: str, sex: str) -> str:
        """亚型解剖方位(左/右) → 该性别下的阴阳归属（男女镜像）。"""
        import re
        mm = re.search(r'[左右]', subtype)
        side = mm.group(0) if mm else '—'
        return F.side_yinyang(side, sex) if side != '—' else '—'

    # ── 10. 目标1：个体健康状态 ────────────────────────────────
    def health_state(self, xing: str, sex: str = 'male',
                     jiazi_index: Optional[int] = None, age: int = 30) -> Dict:
        """综合 禀赋(五形) + 命局(甲子) + 发育期(男8女7) + 形色 得 0–1 健康评分。"""
        score = 0.70
        rel = self._susceptibility(xing)
        fc = rel['形色关系']
        score += 0.10 if '相得' in fc else (0.05 if '相生' in fc else -0.12)
        ming = None
        if jiazi_index is not None:
            lt = self.jiazi_lifetime(jiazi_index, xing)
            ming = lt['ming_wuxing']
            score += {'同': 0.05, '生': -0.02, '被生': 0.05, '克': -0.08, '被克': -0.03}.get(lt['xing_relation'], 0)
        dev = self.development(sex, age)
        score += {'童': 0.02, '天癸至': 0.03, '壮盛': 0.05, '巅峰': 0.08,
                  '始衰': -0.05, '阳衰': -0.08, '天癸竭': -0.10, '衰极': -0.12}.get(dev['stage'], 0)
        score = round(max(0.0, min(1.0, score)), 3)
        state, meaning = next((s, m) for thr, s, m in F.HEALTH_STATES if score >= thr)
        return {'code': f'{xing}形·{sex}', 'health_score': score, 'state': state,
                'meaning': meaning, 'form_color': fc, 'ming_wuxing': ming,
                'dev_stage': dev['stage'], 'tiangui': dev['tiangui'],
                'mirror': self.mirror(sex)['first'] + '为阳'}

    # ── 11. 目标2：疾病证候易感性 ──────────────────────────────
    def syndrome_susceptibility(self, xing: str, sex: str = 'male',
                                jiazi_index: Optional[int] = None, age: int = 30) -> Dict:
        """五形主证候 × 命局五行 × 发育期 × 性别 → 证候易感度排序。"""
        zh = F.ZHENGHOU[xing]
        scores = dict(zh['scores'])
        reasons = {}
        # 命局五行加持：命局五行对应脏之证候 +0.10
        if jiazi_index is not None:
            ming = self.jiazi_lifetime(jiazi_index, xing)['ming_wuxing']
            for xz, z in F.ZHENGHOU.items():
                if xz == ming:
                    for k in z['scores']:
                        scores[k] = scores.get(k, 0) + 0.10
                    reasons[z['main']] = f'命局{ming}气旺'
        # 发育期：天癸竭/阳衰/衰极 → 肾虚类 +0.10
        dev = self.development(sex, age)
        if dev['stage'] in ('天癸竭', '阳衰', '衰极'):
            for k in scores:
                if '肾' in k:
                    scores[k] = scores.get(k, 0) + 0.10
            reasons[F.ZHENGHOU['水']['main']] = f'发育期「{dev["stage"]}」天癸衰减'
        # 性别：女偏血证/经断，男偏精/劳
        if sex == 'female':
            scores['肝血虚证'] = max(scores.get('肝血虚证', 0.50), 0.50) + 0.08
            reasons['肝血虚证'] = '女以血为用(数脱血)'
        ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
        out = [{'zheng': k, 'susceptibility': round(min(1.0, v), 2),
                'level': F.level_cn(F.level_of(min(1.0, v))),
                'reason': reasons.get(k, '禀赋基线')} for k, v in ranked]
        return {'code': f'{xing}形·{sex}', 'main_zheng': out[0]['zheng'],
                'bing_xing': zh['bing_xing'], 'ranked': out,
                'ming_wuxing': (self.jiazi(jiazi_index)['tg_wx'] if jiazi_index is not None else None),
                'dev_stage': dev['stage'], 'side_rule': self.mirror(sex)['first'] + '为阳'}

    def report_gender(self, fmt: str = 'text') -> str:
        """渲染男女参数同异对照表（markdown 表格）"""
        g = self.compare_gender()
        L = []
        L.append('## 一、相同点（男性分类参数 = 女性分类参数）')
        L.append('| 维度 | 参数 | 男 | 女 | 依据 |')
        L.append('|---|---|---|---|---|')
        for r in g['same']:
            L.append(f'| {r["dim"]} | {r["param"]} | {r["male"]} | {r["female"]} | {r["src"]} |')
        L.append('')
        L.append('## 二、不同点（男性分类参数 ≠ 女性分类参数）')
        L.append('| 维度 | 参数 | 男 | 女 | 依据 |')
        L.append('|---|---|---|---|---|')
        for r in g['diff']:
            L.append(f'| {r["dim"]} | {r["param"]} | {r["male"]} | {r["female"]} | {r["src"]} |')
        return '\n'.join(L)


if __name__ == '__main__':
    m = ConstitutionModel()
    print('25 型载入:', len(m.all_types()))
    print('--- 示例：木形·上角（男）---')
    import json as _j
    print(_j.dumps(m.generate('木', '上角', 'male'), ensure_ascii=False, indent=2))
    print('--- 示例：木形·上角（女）---')
    print(_j.dumps(m.generate('木', '上角', 'female'), ensure_ascii=False, indent=2))
