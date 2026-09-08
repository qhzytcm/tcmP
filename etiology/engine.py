# -*- coding: utf-8 -*-
"""
etiology.engine —— 三因辨证引擎（核心）
================================================
内因辨证（七情）· 外因辨证（六淫）· 不内外因辨证（7板块）

输入：症状/诱因描述文本（或结构化 symptoms 列表 + 可选项 trigger）
流程：
  1) 文本切词 → 与三因知识库症状词做包含匹配，得各候选病因命中
  2) 三因门类评分（命中数×权重 + 门类特异关键词加成）
  3) 输出：三因分类置信 → 每因 Top 病因辨证卡（病机/治则/方/穴/经脉）
  4) 四层定位映射（病因层 → 脏腑层 → 经络层）与五阶段对齐

用法：
    from etiology.engine import EtiologyEngine
    eng = EtiologyEngine()                       # 载入三因 JSON 知识库
    r = eng.dialect('恶寒发热无汗，身痛，脉浮紧')   # 文本入口
    r = eng.dialect(['恶寒', '无汗', '身痛'], trigger='着凉')  # 结构化入口
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, List, Optional

from etiology import framework as F

DATA_DIR = Path(os.path.dirname(__file__)) / 'data'


class EtiologyEngine:
    """三因辨证引擎：载入知识库 + 分类评分 + 辨证输出"""

    def __init__(self, data_dir: Optional[Path] = None):
        d = Path(data_dir) if data_dir else DATA_DIR
        self.kb = {}
        for key, fn in [('nei', 'nei_yin.json'),
                        ('wai', 'wai_yin.json'),
                        ('bunei', 'bu_nei_wai.json')]:
            self.kb[key] = json.loads((d / fn).read_text(encoding='utf-8'))
        # 门类特异触发词（诱因/主诉中一票加成）
        self.trigger_words = {
            'nei': ['生气', '发怒', '愤怒', '受惊', '惊吓', '焦虑', '思虑', '悲伤', '难过',
                    '伤心', '恐惧', '害怕', '担忧', '忧愁', '情绪', '心情', '压力', '大喜'],
            'wai': ['受凉', '着凉', '感冒', '吹风', '受风', '淋雨', '暑天', '中暑', '天热',
                    '潮湿', '久居湿地', '秋燥', '天气', '换季', '受寒', '外感'],
            'bunei': ['吃多', '暴饮暴食', '吃坏', '喝多', '累', '劳累', '熬夜', '加班',
                      '受伤', '摔伤', '跌打', '手术', '咬伤', '过敏', '遗传', '先天', '久坐',
                      '房事', '饮食不洁'],
        }
        # 常见伴随症/体质词（降低误命中）
        self.noise = ['三天', '两天', '一周', '今天', '昨天', '反复', '多年', '小时', '左右']

    # ── 1. 文本清洗与切分 ──────────────────────────────────────
    def _clean(self, text: str) -> List[str]:
        """粗切：按标点/空格切短句，再截取含关键词窗口；返回候选症状词"""
        import re
        parts = re.split(r'[，。；、,.!?！？\s/]+', text)
        out = []
        for p in parts:
            p = p.strip()
            if len(p) < 2:
                continue
            # 去掉纯时序/量词噪声片段
            if p in self.noise:
                continue
            out.append(p)
        return out

    # ── 2. 单候选项评分 ────────────────────────────────────────
    def _score_candidate(self, cand_name: str, symptoms: Dict[str, int],
                         symptom_list: List[str]) -> float:
        """候选病因命中评分：症状词包含匹配加权"""
        entry = symptoms[cand_name]
        hit = 0.0
        detail = []
        for sym in entry.get('symptom_keywords', entry.get('symptoms', [])):
            for s in symptom_list:
                if sym in s or s in sym:
                    hit += 1.0
                    detail.append(sym)
                    break
        return hit, detail

    # ── 3. 主入口：三因辨证 ────────────────────────────────────
    def dialect(self, text: Optional[str] = None, symptoms: Optional[List[str]] = None,
                trigger: Optional[str] = None) -> Dict:
        """辨证主入口。text 自由文本 或 symptoms 结构化列表，可带 trigger 诱因。"""
        sym_list = []
        if text:
            sym_list += self._clean(text)
        if symptoms:
            sym_list += list(symptoms)
        # 去重保序（py3.9 兼容：避免推导式引用外部变量）
        sym_list = list(dict.fromkeys(sym_list))

        # 门类分数 = 触发词命中 + 知识库症状命中（归一）
        scores = {'nei': 0.0, 'wai': 0.0, 'bunei': 0.0}
        trigger_hits = {'nei': [], 'wai': [], 'bunei': []}
        all_input = ' '.join(sym_list) + (' ' + trigger if trigger else '')
        for cls in scores:
            for tw in self.trigger_words[cls]:
                if tw in all_input:
                    scores[cls] += 2.0
                    trigger_hits[cls].append(tw)

        # 各门类内部候选评分
        cls_candidates = {}
        cls_hits = {}
        # 内因：七情（emotions）
        nei_cands = {}
        for emo, entry in self.kb['nei']['emotions'].items():
            h, det = self._score_candidate(emo, {emo: entry}, sym_list)
            if h > 0 or (trigger and any(t in trigger for t in ['生气', '发怒', '受惊', '悲伤', '害怕', '焦虑', '思虑'])):
                # trigger 归属加成：匹配情志语义的诱因词
                trg_map = {'怒': ['生气', '发怒', '愤怒', '被气'], '惊': ['受惊', '惊吓', '吓'],
                           '恐': ['害怕', '恐惧', '吓'], '悲': ['悲伤', '难过', '伤心', '哭'],
                           '忧': ['担忧', '忧愁', '焦虑'], '思': ['思虑', '想太多', '焦虑'],
                           '喜': ['大喜', '高兴']}
                for k, ws in trg_map.items():
                    if emo == k and trigger and any(w in trigger for w in ws):
                        h += 1.5
                        det.append(f'诱因[{k}]')
                if h > 0:
                    nei_cands[emo] = {'hit': h, 'detail': det}
                    scores['nei'] += h
        # 外因：六淫
        wai_cands = {}
        for yin, entry in self.kb['wai']['liuyin'].items():
            h, det = self._score_candidate(yin, {yin: entry}, sym_list)
            if h > 0:
                # 六淫天气诱因加成
                trg_map = {'风': ['受风', '吹风'], '寒': ['受寒', '着凉', '受凉', '冷'],
                           '暑': ['中暑', '暑天', '天热', '夏天'], '湿': ['潮湿', '淋雨', '久居湿地'],
                           '燥': ['秋燥', '干燥', '秋天'], '热': ['上火', '天热', '热']}
                for k, ws in trg_map.items():
                    if yin == k and trigger and any(w in trigger for w in ws):
                        h += 1.5
                        det.append(f'诱因[{k}]')
                if h > 0:
                    wai_cands[yin] = {'hit': h, 'detail': det}
                    scores['wai'] += h
        # 不内外因：7 板块
        bunei_cands = {}
        for bid, entry in self.kb['bunei']['boards'].items():
            h, det = self._score_candidate(bid, {bid: entry}, sym_list)
            if h > 0:
                trg_map = {'I1': ['吃多', '暴饮暴食', '吃坏', '喝多', '饮食'],
                           'I2': ['劳累', '累', '熬夜', '加班', '久坐', '房事', '过劳'],
                           'I3': ['受伤', '摔伤', '跌打', '手术', '外伤', '撞'],
                           'I4': ['咬伤', '虫', '狗', '蛇'], 'I5': ['中毒', '误服', '药物'],
                           'I6': ['误诊', '误治', '吃错药'], 'I7': ['先天', '遗传', '从小就', '发育']}
                for k, ws in trg_map.items():
                    if bid == k and trigger and any(w in trigger for w in ws):
                        h += 1.5
                        det.append(f'诱因[{entry["name"]}]')
                if h > 0:
                    bunei_cands[bid] = {'hit': h, 'detail': det}
                    scores['bunei'] += h

        # 归一为置信（0-1）
        total = sum(scores.values())
        conf = {k: (v / total if total > 0 else 0.0) for k, v in scores.items()}
        # 主分类
        main_cls = max(conf, key=conf.get) if total > 0 else None
        top_names = {'nei': '内因（七情）', 'wai': '外因（六淫）', 'bunei': '不内外因'}

        result = {
            'input': {'text': text, 'symptoms': sym_list, 'trigger': trigger},
            'classification': {
                'main': {'cls': main_cls, 'name': top_names[main_cls] if main_cls else None,
                         'conf': conf[main_cls] if main_cls else 0.0},
                'scores': scores, 'conf': conf,
                'trigger_hits': {k: v for k, v in trigger_hits.items() if v},
            },
            'categories': {
                'nei': self._build_nei(nei_cands, sym_list),
                'wai': self._build_wai(wai_cands, sym_list),
                'bunei': self._build_bunei(bunei_cands, sym_list),
            },
        }
        return result

    # ── 4. 各门类辨证卡构建 ────────────────────────────────────
    def _build_nei(self, cands, sym_list):
        if not cands:
            return {'hits': [], 'note': '未检测到明显七情内伤特征'}
        ranked = sorted(cands.items(), key=lambda kv: kv[1]['hit'], reverse=True)[:3]
        out = []
        for emo, info in ranked:
            e = self.kb['nei']['emotions'][emo]
            zang_cn = F.ZANG[e['zang']]
            out.append({
                'cause': f'{emo}({e["physiology"]})',
                'hit': round(info['hit'], 2), 'matched': info['detail'],
                'zang': {'code': e['zang'], 'cn': zang_cn},
                'stage_seq': e['progression'],
                'treatment': e['treatment'],
                'formula': e['formula'],
                'acupoints': e['acupoints'],
                'meridians': [F.MAI_CN[m] for m in e['meridians']],
                'verse': e['verse'],
            })
        return {'hits': out, 'note': '七情内伤——五脏主情：肝怒/心喜/肺悲/脾思/肾恐'}

    def _build_wai(self, cands, sym_list):
        if not cands:
            return {'hits': [], 'note': '未检测到明显六淫外感特征'}
        ranked = sorted(cands.items(), key=lambda kv: kv[1]['hit'], reverse=True)[:3]
        out = []
        for yin, info in ranked:
            e = self.kb['wai']['liuyin'][yin]
            sig_desc = e.get('desc') or e.get('nature', '')
            out.append({
                'cause': f'{yin}邪',
                'signature': {'code': e['code'], 'lam': e['lam'], 'lam_lv': e['lam_lv'],
                              'alpha': e['alpha'], 'alpha_main': e['alpha_main'],
                              's': e['s'], 's_lv': e['s_lv'], 'desc': sig_desc},
                'hit': round(info['hit'], 2), 'matched': info['detail'],
                'stage_seq': e['stages'],
                'tongue': e['tongue'], 'pulse': e['pulse'],
                'treatment': e['treatment'],
                'formula': e['formula'],
                'acupoints': e['acupoints'],
                'meridians': [F.MAI_CN[m] for m in e['meridians']],
                'verse': e['verse'],
            })
        return {'hits': out, 'note': '六淫外感——五阶段 S1感→S2侵→S3传→S4化→S5损'}

    def _build_bunei(self, cands, sym_list):
        if not cands:
            return {'hits': [], 'note': '未检测到明显不内外因特征'}
        ranked = sorted(cands.items(), key=lambda kv: kv[1]['hit'], reverse=True)[:3]
        out = []
        for bid, info in ranked:
            e = self.kb['bunei']['boards'][bid]
            aff = {F.ZANG_FU[k]: v for k, v in e.get('affinity', {}).items() if k in F.ZANG_FU}
            out.append({
                'cause': f'{e["name"]}({bid})',
                'affinity': aff,
                'hit': round(info['hit'], 2), 'matched': info['detail'],
                'stage_seq': e['progression'],
                'treatment': e['treatment'],
                'formula': e['formula'],
                'acupoints': e['acupoints'],
                'meridians': [F.MAI_CN[m] for m in e['meridians']],
                'verse': e['verse'],
            })
        return {'hits': out, 'note': '不内外因——7板块×68细目（陈言《三因极一病证方论》）：饮食/劳逸/外伤/虫兽/中毒/医过/先天'}

    # ── 5. 简明文本报告（面向终端/LLM 注入）───────────────────
    def report(self, result: Dict) -> str:
        lines = []
        mc = result['classification']['main']
        c = result['classification']
        confs = ' '.join(f'{name}{c["conf"][k]:.0%}' for k, name in
                         [('nei', '内因'), ('wai', '外因'), ('bunei', '不内外因')])
        lines.append(f'【三因分类】主判：{mc["name"] if mc["name"] else "未明"} '
                     f'(置信 {mc["conf"]:.0%}) | 各门类 {confs}')
        for cls_key, cls_cn, head in [('nei', '内因·七情', '情志病机'),
                                      ('wai', '外因·六淫', '六淫病机'),
                                      ('bunei', '不内外因', '板块病机')]:
            cat = result['categories'][cls_key]
            if not cat['hits']:
                continue
            lines.append(f'\n◆ {cls_cn}（{head}）')
            for h in cat['hits']:
                lines.append(f'  · {h["cause"]} 命中{h["hit"]:g} {h["matched"]}')
                lines.append(f'    定位: {h.get("zang", {}).get("cn", "")} '
                             f'{h.get("meridians", [])}')
                lines.append(f'    治法: {h["treatment"]}')
                if h.get('formula'):
                    lines.append(f'    方: {"/".join(h["formula"][:3])}')
                if h.get('acupoints'):
                    lines.append(f'    穴: {"/".join(h["acupoints"][:5])}')
        return '\n'.join(lines)


if __name__ == '__main__':
    eng = EtiologyEngine()
    demos = [
        '恶寒发热无汗，身痛骨节痛，脉浮紧，受凉两天',
        '急躁易怒，胁肋胀痛，面红目赤，昨天跟人生气后加重',
        '脘腹胀满，嗳腐吞酸，昨晚暴饮暴食后',
        '口干咽燥，干咳无痰，皮肤干燥，秋天换季',
        '头重如裹，身重困倦，脘闷纳呆，久居湿地',
    ]
    for d in demos:
        print('═' * 60)
        print('输入:', d)
        r = eng.dialect(d)
        print(eng.report(r))
