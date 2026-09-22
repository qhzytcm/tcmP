# -*- coding: utf-8 -*-
"""阴阳二十五人 参数化生成式模型 演示 / 自检"""
import sys, json
sys.path.insert(0, r'C:\Users\DELL\tcmP')
from constitution import framework as F
from constitution.model import ConstitutionModel

m = ConstitutionModel()

print('=' * 72)
print('【0】25 型载入清单（五形 × 五亚型）')
print('=' * 72)
for xing in F.XING_ORDER:
    names = [t['name'] for t in m.types[xing]]
    print(f'  {xing}形({m.xing[xing]["yin"]}音/{m.xing[xing]["zhu_jing_cn"]}): ' + '  '.join(names))
print(f'  合计: {len(m.all_types())} 型')

print('\n' + '=' * 72)
print('【1】正向生成：木形·上角 男 vs 女（核心差异=血气/须髯）')
print('=' * 72)
for sex in ('male', 'female'):
    p = m.generate('木', '上角', sex)
    tag = '男' if sex == 'male' else '女'
    print(f'  [{tag}] {p["code"]} | 色{p["se"]}/音{p["yin"]}/{p["sub_jing"]} 情态{p["tai"]}')
    print(f'        V_气={p["params"]["V_qi"]}({p["params"]["V_qi_lv"]})  '
          f'V_血={p["params"]["V_xue"]}({p["params"]["V_xue_lv"]})  '
          f'六经常数={p["params"]["六经气血常数"]}')
    print(f'        毛发: {p["hair_note"]}')

print('\n' + '=' * 72)
print('【2】25 型全表性别参数扫描（V_气 / V_血 / 须髯）')
print('=' * 72)
print(f'  {"型":<16}{"经":<8}{"男V气":>7}{"男V血":>7}{"女V气":>7}{"女V血":>7}  须髯')
for t in m.all_types():
    pm = m.generate(t['xing'], t['name'], 'male')['params']
    pf = m.generate(t['xing'], t['name'], 'female')['params']
    print(f'  {t["xing"]}·{t["name"]:<13}{t["jing"]:<8}'
          f'{pm["V_qi"]:>7}{pm["V_xue"]:>7}{pf["V_qi"]:>7}{pf["V_xue"]:>7}  男有/女无')

print('\n' + '=' * 72)
print('【3】逆转推理：由表型观测反推体质型')
print('=' * 72)
demos = [
    {'color': '青', 'yin': '角', 'jing': 'LR', 'shape': ['小头', '长面', '大肩背'], 'beard': True},
    {'color': '赤', 'yin': '徵', 'shape': ['小头', '行摇肩', '背肉满']},
    {'color': '黑', 'yin': '羽', 'jing': 'BL', 'shape': ['大头', '大腹']},
]
for d in demos:
    r = m.infer(d)
    top = r['main']
    print(f'  观测 {d}')
    print(f'    → 主判: {top["code"]} (score {top["score"]:g}; {", ".join(top["why"])})')
    for c in r['ranked'][1:3]:
        print(f'      次选: {c["code"]} (score {c["score"]:g})')

print('\n' + '=' * 72)
print('【4】形色相得 / 相克（LS64 五行生克：形胜色/色胜形者逢年忌感邪则病）')
print('=' * 72)
for _, color in [('木', '青'), ('木', '白'), ('木', '黄'), ('火', '黑')]:
    s = m._susceptibility(_, color)
    print(f'  形{_}·色{color} → {s["形色关系"]} | {s["断语"]}')

print('\n' + '=' * 72)
print('【5】男女分类参数 同异对照')
print('=' * 72)
print(m.report_gender())

print('\n' + '=' * 72)
print('【6】并列第二轴：阴阳之人（灵枢·通天，不在 25 型内）')
print('=' * 72)
print('  ' + '  '.join(F.YIN_YANG_5))
