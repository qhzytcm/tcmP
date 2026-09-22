#!/usr/bin/env python3
# Append DSU-00076~00083 to batch 006, then create batch 007
import json, os
DIR = r'C:\Users\DELL\textbook-project\kg-schema\samples'
M = {"source_textbook":"D01-S01","source_chapter":"第7-11章","version":"1.0.0","status":"draft","created_at":"2026-07-23T00:00:00Z"}

def d(id, dn, icd, cat, mt, pw, bm, epi, wt,
      sn, pt, zf, sc, yy, ei, ch, dx, ks, ss, tn, pu,
      ft, cb, bt, bd, bb, ev, refs,
      fm, fs, mods, acu, diet, prog, caut,
      diff, stage, zr, sr, case, tps, exqs):
    return {"id":id,"disease_side":{"disease_name":dn,"icd_code":icd,"category":cat,"molecular_targets":mt,"gene_pathways":pw,"biomarkers":bm,"epidemiology":epi,"western_treatment":wt},"syndrome_side":{"syndrome_name":sn,"pattern_type":pt,"zangfu":zf,"six_channels":sc,"eight_principles":{"yin_yang":yy,"exterior_interior":ei,"cold_heat":ch,"deficiency_excess":dx},"key_symptoms":ks,"secondary_symptoms":ss,"tongue":tn,"pulse":pu,"field_theory":ft,"classical_basis":cb},"bridge":{"mapping_type":bt,"mapping_description":bd,"biological_basis":bb,"evidence_level":ev,"key_references":refs},"clinical":{"recommended_formula":fm,"formula_source":fs,"modifications":mods,"acupuncture_rx":acu,"dietary_therapy":diet,"prognosis":prog,"caution":caut},"teaching":{"difficulty":diff,"stage":stage,"sage_ref_zhang":zr,"sage_ref_sun":sr,"typical_case":case,"teaching_points":tps,"exam_questions":exqs},"metadata":M}

b6_extra = []

# DSU-00076 骨质疏松
b6_extra.append(d("DSU-00076","骨质疏松症","FB83","内分泌代谢病",
["RANKL/OPG骨保护素","PTH1R","VDR维生素D受体","组织蛋白酶K"],
["RANK-RANKL-OPG骨吸收通路","Wnt/beta-catenin骨形成通路"],
["DXA T值<=-2.5","FRAX骨折风险评估","P1NP/CTX-1骨转换标志物"],
"60岁以上患病率约36%，绝经后女性约50%",
"钙剂+VD基础；双膦酸盐/地舒单抗抗骨吸收；特立帕肽促骨形成",
"肾精亏虚、骨痿证","肝肾阴虚证","肾·肝·骨","少阴病",
"阴证","里证","寒证","虚证",
["腰背疼痛酸软乏力","身高缩短驼背","轻微外力即骨折","活动能力下降"],
["腰膝酸软","牙齿松动","耳鸣健忘","发脱齿摇"],
"舌淡暗苔薄白或少苔","脉沉细弱或尺脉无力",
"肾主骨生髓藏精。肾精亏虚则骨枯髓减、骨质疏松。肾为先天之本，年高则天癸竭精血衰，肾虚骨失所养发为骨痿。治以补肾填精壮骨。",
"《素问-痿论》：肾气热则腰脊不举骨枯而髓减发为骨痿。",
"机制对应","骨痛骨折对应骨吸收>骨形成。肾精亏虚对应绝经后/衰老引起骨代谢负平衡。",
"雌激素下降→RANKL↑/OPG↓→破骨细胞活化+成骨细胞Wnt信号↓→骨形成↓→骨折风险↑",
"B级-单中心RCT",["《骨质疏松症诊疗指南》2023","《中医骨伤科学-骨痿》十三五教材"],
"左归丸合六味地黄丸","《景岳全书》合《小儿药证直诀》",
[{"condition":"腰背痛甚","adjustment":"加杜仲、续断、骨碎补补肾壮骨"},{"condition":"兼阳虚畏寒","adjustment":"加鹿角胶、肉苁蓉温补肾阳"},{"condition":"骨折后","adjustment":"加丹参、血竭、自然铜接骨"}],
["肾俞","脾俞","命门","腰阳关","关元","足三里","太溪","悬钟"],
"高钙食物奶制品豆制品；VD晒太阳每日15min；负重运动防跌倒",
"药物可增骨密度5-10%/年；综合管理降低骨折风险50%",
"双膦酸盐需防颌骨坏死和股骨非典型骨折",
4,"主治医",
"《金匮要略》肾气丸治疗肾虚腰痛——补肾壮骨的源头。",
"《备急千金要方》卷十九·肾脏：孙思邈记载补肾强骨方剂。",
"患者李某，女，68岁。腰背痛2年伴压缩性骨折。DXA T值-3.2。左归丸合六味地黄丸+钙剂VD+阿仑膦酸钠。6月后疼痛减轻，1年后DXA T值-2.6。未再发骨折。",
["从骨质疏松理解肾精的生物学本质","双膦酸盐与补肾中药的协同","左归丸与右归丸鉴别应用"],
["左归丸与右归丸治疗骨质疏松的鉴别？"]
))

# DSU-00077 缺铁性贫血
b6_extra.append(d("DSU-00077","缺铁性贫血","3A02","血液病",
["DMT1二价金属转运蛋白1","TfR1转铁蛋白受体","铁调素hepcidin","铁蛋白"],
["BMP-SMAD-hepcidin铁代谢调控通路","HIF-2alpha-DMT1肠铁吸收通路"],
["血清铁<8umol/L","铁蛋白<15ug/L","转铁蛋白饱和度<16%","Hb<120g/L(女)"],
"全球最常见贫血，中国患病率约15-20%，孕妇儿童高发",
"口服铁剂（硫酸亚铁/多糖铁）；静脉铁剂；病因治疗",
"脾胃虚弱、气血两虚证","脾肾阳虚证","脾·胃·心","太阴病",
"阴证","里证","寒证","虚证",
["面色萎黄或苍白无华","头晕眼花","心悸气短","疲乏无力"],
["食欲不振","口唇指甲淡白","皮肤干燥","月经量少色淡"],
"舌淡红苔薄白","脉细弱或芤脉",
"脾为后天之本、气血生化之源。脾胃虚弱运化失职则水谷精微不能化生血液。血虚面色失荣则萎黄苍白，心血不足则心悸气短，清窍失养则头晕眼花。",
"《灵枢-决气》：中焦受气取汁变化而赤是谓血。",
"直接对应","贫血对应铁缺乏导致血红素合成不足Hb下降组织缺氧。脾胃虚弱对应铁摄入/吸收不足。",
"铁摄入不足/丢失过多→铁储存耗尽→血清铁下降→骨髓有核红细胞铁缺乏→血红素合成↓→Hb减少+组织缺氧",
"B级-单中心RCT",["《缺铁性贫血诊治指南》2022","《中医内科学-虚劳》十三五教材"],
"归脾汤合八珍汤","《济生方》合《正体类要》",
[{"condition":"铁吸收障碍","adjustment":"加炒麦芽、砂仁醒脾开胃"},{"condition":"月经过多","adjustment":"加阿胶、艾叶止血"},{"condition":"严重贫血","adjustment":"结合静脉铁剂"}],
["足三里","脾俞","心俞","气海","关元","三阴交","血海","膈俞"],
"高铁食物红肉动物肝脏；搭配维C促吸收；忌茶咖啡与铁同服",
"铁剂4周Hb可上升>20g/L；补足储存铁需2-4月",
"口服铁剂注意胃肠道反应；Hb正常后续补铁2-3月补足储存铁",
2,"住院医-1",
"《金匮要略》小建中汤治虚劳——补血先补脾的思想。",
"《备急千金要方》卷三·妇人：孙思邈重视妇人血虚治疗。",
"患者林某，女，28岁。头昏心悸半年Hb 78g/L铁蛋白6ug/L。归脾汤合八珍汤+硫酸亚铁。4周后Hb 102g/L，2月Hb正常。",
["中焦受气取汁变化而赤是谓血","铁剂与归脾汤的协同——补铁+健脾","补足储存铁的治疗原则"],
["归脾汤补血先补脾的组方原理？"]
))

print(f"Added {len(b6_extra)} DSUs to batch 006")

# Merge with existing batch 006
p006 = os.path.join(DIR, "dsu-samples-006.json")
with open(p006, 'r', encoding='utf-8') as f:
    existing_006 = json.load(f)
print(f"Existing: {len(existing_006)} DSUs")
assert len(existing_006) == 12
assert len(b6_extra) == 2  # Just first 2 for now
all_006 = existing_006 + b6_extra
print(f"Merged: {len(all_006)} DSUs")
with open(p006, 'w', encoding='utf-8') as f:
    json.dump(all_006, f, ensure_ascii=False, indent=2)
print("Partial batch 006 save done")
