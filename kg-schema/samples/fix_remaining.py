#!/usr/bin/env python3
"""Fix remaining validation issues in batch 006"""
import json, os
DIR = r'C:\Users\DELL\textbook-project\kg-schema\samples'
p = os.path.join(DIR, 'dsu-samples-006.json')
with open(p, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Fix DSU-00078 再障
for u in data:
    if u['id'] == 'DSU-00078':
        u['teaching']['teaching_points'] = [
            '再障肾虚髓枯与造血干细胞衰竭对应', 
            'ATG+环孢素+补肾填精中西医结合',
            '再生障碍性贫血的分型与预后评估'
        ]
        u['teaching']['exam_questions'] = [
            '再障中医辨证分型与西医严重程度对应？', 
            'ATG/环孢素免疫抑制的祛邪效应与补肾中药扶正的结合？'
        ]
    if u['id'] == 'DSU-00079':
        u['teaching']['exam_questions'] = [
            '从热入营血分析AML的出血和高热？',
            '中医药在白血病化疗中减轻毒副反应的策略？'
        ]
    if u['id'] == 'DSU-00080':
        u['teaching']['exam_questions'] = [
            '从痰瘀互结分析淋巴瘤的证候特点？',
            '消瘰丸治疗淋巴瘤组方依据——浙贝母玄参牡蛎的配伍？'
        ]
    if u['id'] == 'DSU-00081':
        u['teaching']['teaching_points'] = [
            'GBS湿热浸淫筋脉失养', 
            'IVIG+中药祛湿通络',
            '格林-巴利综合征的临床分型与预后'
        ]
        u['teaching']['exam_questions'] = [
            '从湿热不攘大筋软短小筋弛长分析GBS经典？',
            'IVIG治疗GBS的免疫调节机制与中医扶正祛邪的对应？'
        ]
    if u['id'] == 'DSU-00082':
        u['teaching']['exam_questions'] = [
            'MG与Lambert-Eaton综合征鉴别？',
            '补中益气汤益气升阳与溴吡斯的明改善传导——中西医结合？'
        ]
    if u['id'] == 'DSU-00083':
        u['teaching']['exam_questions'] = [
            '从髓海不足分析AD？',
            '从痰瘀清窍与Abeta沉积和tau缠结的对应关系？'
        ]

with open(p, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print('Fixed all remaining validation issues')
