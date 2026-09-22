#!/usr/bin/env python3
"""Fix minor validation issues"""
import json, os

DIR = r'C:\Users\DELL\textbook-project\kg-schema\samples'

fixes = {}

fixes['DSU-00066'] = {
    'typical_case': '患者周某，女，58岁。右面颊阵发性电击样剧痛2月，说话刷牙即触发V2/3支，每日发作10余次，烦躁易怒口干苦。MRI排除继发性。卡马西平200mg tid控制不佳。舌红苔黄，脉弦数。予龙胆泻肝汤合川芎茶调散加减+全蝎6g蜈蚣2条。3剂后发作减至3-4次/日，疼痛强度减轻。7剂后偶发。续服2周基本控制。',
    'exam_questions': ['三叉神经痛原发性和继发性的鉴别要点？', '从风火相煽角度分析三叉神经痛的病机特点？']
}
fixes['DSU-00068'] = {
    'typical_case': '患者吴某，女，36岁。反复发作性左侧偏头痛8年，每月发作3-4次，呈搏动性剧痛伴恶心呕吐、畏光畏声，每次持续8-24小时，月经期加重，有先兆（闪光暗点）。舌红苔薄黄，脉弦数。予天麻钩藤饮加减+舒马曲普坦鼻喷雾剂急性期治疗。2个月后发作频率减至每月1次。加用普萘洛尔预防，中药续服3个月，6个月随访偶有轻度发作。',
    'exam_questions': ['天麻钩藤饮中牛膝的配伍意义——引血下行的靶向作用？', '偏头痛先兆的中医病机解释——风阳扰动与CSD的对应？']
}
fixes['DSU-00069'] = {
    'typical_case': '患者黄某，男，16岁。反复发作性抽搐2年，每月发作1-2次。发作时突然倒地、四肢强直抽搐、口吐白沫、意识丧失约3分钟，发作后昏睡。EEG示广泛性痫样放电。舌红苔黄腻，脉弦滑。予定痫丸加减配合丙戊酸500mg/日。3个月后发作减至每2月1次。加用左乙拉西坦后完全控制9个月。中药以健脾化痰息风定痫调理，随访1年无发作。',
    'exam_questions': ['定痫丸中天麻全蝎僵蚕的配伍含义？为何用虫类药物？', '全面性强直-阵挛发作与癫痫持续状态的中西医处理？']
}
fixes['DSU-00070'] = {
    'typical_case': '患者王某，男，68岁。右手静止性震颤2年，动作迟缓、小写征、面具脸、便秘。UPDRS-III 32分。舌暗红少苔，脉弦细。予大定风珠合地黄饮子加减+美多巴125mg tid。3月后震颤减轻动作改善UPDRS-III 20分。1年后症状稳定运动波动少，生活质量明显改善。',
    'exam_questions': ['诸风掉眩皆属于肝——帕金森病震颤的中医解释？', '从肝肾阴虚角度分析左旋多巴远期并发症？']
}
fixes['DSU-00076'] = {
    'exam_questions': ['左归丸与右归丸治疗骨质疏松的鉴别应用？', '从RANKL/OPG通路分析肾精对骨代谢的调控？']
}
fixes['DSU-00077'] = {
    'typical_case': '患者林某，女，28岁。头昏心悸疲乏半年，面色苍白，月经量多。Hb 78g/L，MCV 68fL，铁蛋白6ug/L。舌淡苔薄白，脉细弱。予归脾汤合八珍汤+硫酸亚铁缓释片。4周后Hb升至102g/L。2月后Hb正常。续服归脾丸2月巩固。嘱多食红肉肝类。',
    'exam_questions': ['归脾汤补血先补脾的组方原理？', '缺铁性贫血与中医血虚证的对应关系？']
}

for fn in ['dsu-samples-005.json', 'dsu-samples-006.json', 'dsu-samples-007.json']:
    path = os.path.join(DIR, fn)
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    changed = False
    for u in data:
        eid = u['id']
        if eid in fixes:
            fdata = fixes[eid]
            if 'typical_case' in fdata:
                u['teaching']['typical_case'] = fdata['typical_case']
            if 'exam_questions' in fdata:
                u['teaching']['exam_questions'] = fdata['exam_questions']
            changed = True
            print(f'Fixed {eid}')
    if changed:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f'Saved {fn}')

print('All fixes applied')
