#!/usr/bin/env python3
"""Complete batch 006 (DSU-00076~00083) FAST using dict literals"""
import json, os
DIR = r'C:\Users\DELL\textbook-project\kg-schema\samples'
M = {"source_textbook":"D01-S01","source_chapter":"第7-11章","version":"1.0.0","status":"draft","created_at":"2026-07-23T00:00:00Z"}
def make_dsu(**kw):
    r = {"metadata": M}
    for k,v in kw.items(): r[k]=v
    return r

new = []

# DSU-00076 骨质疏松
new.append(make_dsu(
    id="DSU-00076",
    disease_side={"disease_name":"骨质疏松症","icd_code":"FB83","category":"内分泌代谢病",
        "molecular_targets":["RANKL/OPG骨保护素","PTH1R","VDR维生素D受体","组织蛋白酶K"],
        "gene_pathways":["RANK-RANKL-OPG骨吸收通路","Wnt/beta-catenin骨形成通路"],
        "biomarkers":["DXA T值<=-2.5","FRAX骨折风险评估","P1NP/CTX-1骨转换标志物"],
        "epidemiology":"60岁以上患病率约36%，绝经后女性约50%",
        "western_treatment":"钙剂+VD基础；双膦酸盐/地舒单抗抗骨吸收；特立帕肽促骨形成"},
    syndrome_side={"syndrome_name":"肾精亏虚、骨痿证","pattern_type":"肝肾阴虚证","zangfu":"肾·肝·骨","six_channels":"少阴病",
        "eight_principles":{"yin_yang":"阴证","exterior_interior":"里证","cold_heat":"寒证","deficiency_excess":"虚证"},
        "key_symptoms":["腰背疼痛酸软乏力","身高缩短驼背","轻微外力即骨折","活动能力下降"],
        "secondary_symptoms":["腰膝酸软","牙齿松动","耳鸣健忘","发脱齿摇"],
        "tongue":"舌淡暗苔薄白或少苔","pulse":"脉沉细弱或尺脉无力",
        "field_theory":"肾主骨生髓藏精。肾精亏虚则骨枯髓减、骨质疏松。肾为先天之本，年高则天癸竭精血衰，肾虚骨失所养发为骨痿。治以补肾填精壮骨。",
        "classical_basis":"《素问-痿论》：肾气热则腰脊不举骨枯而髓减发为骨痿。"},
    bridge={"mapping_type":"机制对应",
        "mapping_description":"骨痛骨折对应骨吸收>骨形成。肾精亏虚对应绝经后/衰老引起骨代谢负平衡。",
        "biological_basis":"雌激素下降→RANKL↑/OPG↓→破骨细胞活化+成骨细胞Wnt信号↓→骨形成↓→骨折风险↑",
        "evidence_level":"B级-单中心RCT","key_references":["《骨质疏松症诊疗指南》2023","《中医骨伤科学》十三五教材"]},
    clinical={"recommended_formula":"左归丸合六味地黄丸","formula_source":"《景岳全书》合《小儿药证直诀》",
        "modifications":[{"condition":"腰背痛甚","adjustment":"加杜仲、续断、骨碎补补肾壮骨"},{"condition":"兼阳虚畏寒","adjustment":"加鹿角胶、肉苁蓉温补肾阳"},{"condition":"骨折后","adjustment":"加丹参、血竭、自然铜接骨"}],
        "acupuncture_rx":["肾俞","脾俞","命门","腰阳关","关元","足三里","太溪","悬钟"],
        "dietary_therapy":"高钙食物奶制品豆制品；VD晒太阳每日15min；负重运动防跌倒",
        "prognosis":"药物可增骨密度5-10%/年；综合管理降低骨折风险50%",
        "caution":"双膦酸盐需防颌骨坏死和股骨非典型骨折"},
    teaching={"difficulty":4,"stage":"主治医",
        "sage_ref_zhang":"《金匮要略》肾气丸治疗肾虚腰痛——补肾壮骨的源头。",
        "sage_ref_sun":"《备急千金要方》孙思邈记载补肾强骨方剂。",
        "typical_case":"患者李某，女，68岁。腰背痛2年伴压缩性骨折。DXA T值-3.2。左归丸合六味地黄丸+钙剂VD+阿仑膦酸钠。6月后疼痛减轻，1年后DXA T值-2.6。未再发骨折。",
        "teaching_points":["从骨质疏松理解肾精的生物学本质","双膦酸盐与补肾中药的协同","左归丸与右归丸鉴别应用"],
        "exam_questions":["左归丸与右归丸治疗骨质疏松的鉴别？"]}
))

# DSU-00077 缺铁性贫血
new.append(make_dsu(
    id="DSU-00077",
    disease_side={"disease_name":"缺铁性贫血","icd_code":"3A02","category":"血液病",
        "molecular_targets":["DMT1二价金属转运蛋白1","TfR1转铁蛋白受体","铁调素hepcidin","铁蛋白"],
        "gene_pathways":["BMP-SMAD-hepcidin铁代谢调控通路","HIF-2alpha-DMT1肠铁吸收通路"],
        "biomarkers":["血清铁<8umol/L","铁蛋白<15ug/L","转铁蛋白饱和度<16%","Hb<120g/L(女)"],
        "epidemiology":"全球最常见贫血，中国患病率约15-20%，孕妇儿童高发",
        "western_treatment":"口服铁剂（硫酸亚铁/多糖铁）；静脉铁剂；病因治疗"},
    syndrome_side={"syndrome_name":"脾胃虚弱、气血两虚证","pattern_type":"脾肾阳虚证","zangfu":"脾·胃·心","six_channels":"太阴病",
        "eight_principles":{"yin_yang":"阴证","exterior_interior":"里证","cold_heat":"寒证","deficiency_excess":"虚证"},
        "key_symptoms":["面色萎黄或苍白无华","头晕眼花","心悸气短","疲乏无力"],
        "secondary_symptoms":["食欲不振","口唇指甲淡白","皮肤干燥","月经量少色淡"],
        "tongue":"舌淡红苔薄白","pulse":"脉细弱或芤脉",
        "field_theory":"脾为后天之本、气血生化之源。脾胃虚弱运化失职则水谷精微不能化生血液。血虚面色失荣则萎黄苍白，心血不足则心悸气短，清窍失养则头晕眼花。",
        "classical_basis":"《灵枢-决气》：中焦受气取汁变化而赤是谓血。"},
    bridge={"mapping_type":"直接对应",
        "mapping_description":"贫血对应铁缺乏导致血红素合成不足Hb下降组织缺氧。脾胃虚弱对应铁摄入/吸收不足。",
        "biological_basis":"铁摄入不足/丢失过多→铁储存耗尽→血清铁↓→骨髓有核红细胞铁缺乏→血红素合成↓→Hb减少+组织缺氧",
        "evidence_level":"B级-单中心RCT","key_references":["《缺铁性贫血诊治指南》2022","《中医内科学-虚劳》十三五教材"]},
    clinical={"recommended_formula":"归脾汤合八珍汤","formula_source":"《济生方》合《正体类要》",
        "modifications":[{"condition":"铁吸收障碍","adjustment":"加炒麦芽、砂仁醒脾开胃"},{"condition":"月经过多","adjustment":"加阿胶、艾叶止血"},{"condition":"严重贫血","adjustment":"结合静脉铁剂"}],
        "acupuncture_rx":["足三里","脾俞","心俞","气海","关元","三阴交","血海","膈俞"],
        "dietary_therapy":"高铁食物红肉动物肝脏；搭配维C促吸收；忌茶咖啡与铁同服",
        "prognosis":"铁剂4周Hb可上升>20g/L；补足储存铁需2-4月",
        "caution":"口服铁剂注意胃肠道反应；Hb正常后续补铁2-3月补足储存铁"},
    teaching={"difficulty":2,"stage":"住院医-1",
        "sage_ref_zhang":"《金匮要略》小建中汤治虚劳——补血先补脾的思想。",
        "sage_ref_sun":"《备急千金要方》卷三·妇人：孙思邈重视妇人血虚治疗。",
        "typical_case":"患者林某，女，28岁。头昏心悸半年Hb 78g/L铁蛋白6ug/L。归脾汤合八珍汤+硫酸亚铁。4周后Hb 102g/L，2月Hb正常。",
        "teaching_points":["中焦受气取汁变化而赤是谓血","铁剂与归脾汤的协同——补铁+健脾","补足储存铁的治疗原则"],
        "exam_questions":["归脾汤补血先补脾的组方原理？"]}
))

# DSU-00078 再生障碍性贫血
new.append(make_dsu(
    id="DSU-00078",
    disease_side={"disease_name":"再生障碍性贫血","icd_code":"3A70","category":"血液病",
        "molecular_targets":["CD34+造血干细胞","IFN-gamma/TNF-alpha造血抑制因子","Fas/FasL凋亡通路","端粒酶"],
        "gene_pathways":["造血干细胞自我更新Wnt/Notch通路","Th1介导造血抑制通路","Fas-caspase凋亡通路"],
        "biomarkers":["全血细胞减少(三系下降)","骨髓增生低下","CD34+细胞明显减少","PNH克隆检测"],
        "epidemiology":"发病率约4-8/百万，好发15-25岁和60岁以上",
        "western_treatment":"免疫抑制治疗（ATG+环孢素）；促造血（TPO-RA）；造血干细胞移植"},
    syndrome_side={"syndrome_name":"肾精亏虚、髓枯血虚证","pattern_type":"脾肾阳虚证","zangfu":"肾·脾·髓","six_channels":"少阴病",
        "eight_principles":{"yin_yang":"阴证","exterior_interior":"里证","cold_heat":"寒热错杂","deficiency_excess":"虚证"},
        "key_symptoms":["进行性面色苍白","反复感染发热","皮肤黏膜出血（瘀斑鼻衄）","高度疲乏"],
        "secondary_symptoms":["头晕眼花","低热骨痛","口舌生疮","腰膝酸软"],
        "tongue":"舌淡胖有齿痕苔白","pulse":"脉沉细数或虚大无力",
        "field_theory":"肾藏精主骨生髓，髓生血。肾精亏虚则髓海枯竭、无血化生。再障之根在肾虚髓枯，标在血虚发热出血。脾为后天之本，肾虚日久必累及脾。",
        "classical_basis":"《灵枢-经脉》论肾足少阴之脉。"},
    bridge={"mapping_type":"机制对应",
        "mapping_description":"全血细胞减少对应造血干细胞免疫损伤导致骨髓脂肪化、造血衰竭。肾精亏虚对应造血干细胞池耗竭。",
        "biological_basis":"自身反应性T细胞→IFN-gamma/TNF-alpha↑→CD34+干细胞Fas凋亡+抑制造血→骨髓脂肪化→三系减少",
        "evidence_level":"C级-队列研究","key_references":["《再障诊治指南》2022","《中医内科学-虚劳》十三五教材"]},
    clinical={"recommended_formula":"左归丸合十四味建中汤","formula_source":"《景岳全书》合《局方》",
        "modifications":[{"condition":"感染发热","adjustment":"加金银花、连翘、板蓝根清热解毒"},{"condition":"出血明显","adjustment":"加仙鹤草、白茅根、三七凉血止血"},{"condition":"阳虚畏寒","adjustment":"加鹿角胶、补骨脂、淫羊藿温阳"}],
        "acupuncture_rx":["肾俞","脾俞","命门","关元","足三里","三阴交","血海","膈俞"],
        "dietary_therapy":"高蛋白高维生素易消化饮食；注意食品卫生防感染",
        "prognosis":"慢性再障免疫抑制治疗有效率约60-70%",
        "caution":"ATG过敏风险；环孢素需监测血药浓度"},
    teaching={"difficulty":5,"stage":"主任医",
        "sage_ref_zhang":"《金匮要略》薯蓣丸治虚劳诸不足——扶正抵御外邪。",
        "sage_ref_sun":"《备急千金要方》卷十九·肾脏：孙思邈论肾虚实辨证。",
        "typical_case":"患者周某，男，22岁。Hb 46g/L, WBC 1.2x10^9/L, PLT 15x10^9/L，骨髓增生低下。予左归丸合十四味建中汤+ATG+环孢素+艾曲波帕。4周脱离输血。6月三系恢复。",
        "teaching_points":["再障肾虚髓枯与造血干细胞衰竭对应","ATG+环孢素+补肾填精中西医结合"],
        "exam_questions":["再障中医辨证分型与西医严重程度对应？"]}
))

# DSU-00079 白血病
new.append(make_dsu(
    id="DSU-00079",
    disease_side={"disease_name":"急性髓系白血病","icd_code":"2A60","category":"血液病",
        "molecular_targets":["FLT3-ITD/TKD突变","NPM1突变","IDH1/2突变","DNMT3A突变"],
        "gene_pathways":["JAK-STAT信号通路(FLT3激活)","PI3K/Akt/mTOR增殖通路","BCL2抗凋亡通路"],
        "biomarkers":["骨髓原始细胞>=20%","流式免疫分型(MPO/CD34/CD117)","NPM1/FLT3-ITD预后分层"],
        "epidemiology":"中国发病率约3-4/10万，AML中位发病年龄65-70岁",
        "western_treatment":"诱导化疗(7+3方案)；靶向药(FLT3/IDH/BCL2抑制剂)；造血干细胞移植"},
    syndrome_side={"syndrome_name":"热毒炽盛、气阴两虚证(急劳/热劳)","pattern_type":"肝火上炎证","zangfu":"肾·髓·心·肝","six_channels":"厥阴病",
        "eight_principles":{"yin_yang":"阳证","exterior_interior":"里证","cold_heat":"热证","deficiency_excess":"虚实夹杂"},
        "key_symptoms":["持续高热不退","出血(瘀斑鼻衄牙龈)","面色苍白乏力","骨痛"],
        "secondary_symptoms":["咽喉肿痛糜烂","淋巴结肿大","肝脾肿大","盗汗消瘦"],
        "tongue":"舌红绛苔黄燥或少苔","pulse":"脉弦滑数或细数",
        "field_theory":"白血病属中医急劳热劳范畴。热毒直入骨髓耗灼精血、扰乱营血。邪热炽盛则高热；热入营血迫血妄行则出血；热毒煎熬骨髓则骨痛。",
        "classical_basis":"《素问-评热病论》：邪之所凑其气必虚。"},
    bridge={"mapping_type":"机制对应",
        "mapping_description":"高热出血贫血对应白血病细胞克隆性增殖导致正常造血受抑。热毒对应异常克隆增殖，髓枯血虚对应正常造血受抑。",
        "biological_basis":"造血干细胞基因突变→BCL2↑→异常克隆增殖+正常造血受抑→贫血/PLT下降+白血病细胞浸润→骨痛+细胞因子→发热消耗",
        "evidence_level":"B级-单中心RCT","key_references":["《急性髓系白血病诊治指南》2023","《中医内科学-血证/急劳》十三五教材"]},
    clinical={"recommended_formula":"清营汤合犀角地黄汤","formula_source":"《温病条辨》合《千金要方》",
        "modifications":[{"condition":"高热神昏","adjustment":"加安宫牛黄丸清热解毒开窍"},{"condition":"出血严重","adjustment":"加茜草、仙鹤草、三七凉血止血"},{"condition":"化疗后呕吐","adjustment":"加法半夏、陈皮和胃降逆"}],
        "acupuncture_rx":["大椎","曲池","合谷","血海","膈俞","足三里","三阴交","肾俞"],
        "dietary_therapy":"无菌饮食(化疗期)；高蛋白高热量高维生素",
        "prognosis":"AML诱导缓解率约60-80%；5年生存率约30-40%",
        "caution":"强化疗有骨髓抑制和感染风险；HSCT是唯一根治手段"},
    teaching={"difficulty":5,"stage":"主任医",
        "sage_ref_zhang":"《金匮要略》虚劳辨证系统为白血病正虚邪实认识奠基。",
        "sage_ref_sun":"《备急千金要方》犀角地黄汤为清热解毒凉血散瘀代表方。",
        "typical_case":"患者王某，男，48岁。高热2周Hb 68g/L, WBC 56x10^9/L(原始72%), PLT 18x10^9/L。骨髓原始84%, FLT3-ITD(+)。清营汤合犀角地黄汤+7+3化疗+米哚妥林。1疗程CR，续以移植巩固。随访2年无复发生存。",
        "teaching_points":["AML热毒壅盛气阴两虚","清营汤透热转气理论","FLT3抑制剂与中医辨证结合"],
        "exam_questions":["从热入营血分析AML的出血和高热？"]}
))

# DSU-00080 淋巴瘤
new.append(make_dsu(
    id="DSU-00080",
    disease_side={"disease_name":"弥漫大B细胞淋巴瘤","icd_code":"2B33","category":"血液病",
        "molecular_targets":["CD20(利妥昔单抗靶点)","BCL2/BCL6抗凋亡蛋白","MYC增殖转录因子","PD-L1免疫逃逸"],
        "gene_pathways":["BCR-BTK-NF-kappaB信号通路","BCL2抗凋亡通路","PI3K/Akt/mTOR增殖通路"],
        "biomarkers":["淋巴结活检(金标准)","PET-CT分期Deauville评分","LDH升高","beta2-微球蛋白"],
        "epidemiology":"年发病率约6-10/10万，DLBCL占NHL的30-40%",
        "western_treatment":"R-CHOP方案一线标准；CAR-T治疗复发难治"},
    syndrome_side={"syndrome_name":"痰瘀互结、气阴两虚证(石疽/恶核)","pattern_type":"气滞血瘀证","zangfu":"肝·脾·经络","six_channels":"少阳病",
        "eight_principles":{"yin_yang":"阳证","exterior_interior":"半表半里证","cold_heat":"热证","deficiency_excess":"虚实夹杂"},
        "key_symptoms":["进行性无痛性淋巴结肿大","发热盗汗体重减轻(B症状)","乏力","肿块推之可动或固定"],
        "secondary_symptoms":["局部压迫症状","皮肤瘙痒","肝脾肿大","纳呆消瘦"],
        "tongue":"舌暗紫或有瘀点苔白腻或黄腻","pulse":"脉弦滑或滑数",
        "field_theory":"淋巴瘤属中医石疽恶核范畴。痰浊瘀血互结于经络凝集成块则淋巴结肿大。痰瘀日久化热则发热盗汗。气阴为痰热所伤则消瘦乏力。",
        "classical_basis":"《灵枢-寒热》：寒热瘰疬在于颈腋者此皆鼠瘘寒热之毒气也。"},
    bridge={"mapping_type":"机制对应",
        "mapping_description":"淋巴结进行性肿大有B症状对应恶性B细胞增殖导致淋巴结构破坏。痰瘀互结对应异常淋巴细胞增殖的肿块。",
        "biological_basis":"B细胞BCL6/BCL2/MYC基因重排→NF-kappaB持续激活→单克隆增殖→肿块形成+PI3K/Akt→LDH↑→B症状+PD-L1→免疫逃逸",
        "evidence_level":"B级-单中心RCT","key_references":["《中国淋巴瘤诊治指南》2023","《中医外科学-石疽》十三五教材"]},
    clinical={"recommended_formula":"消瘰丸合柴胡疏肝散","formula_source":"《医学心悟》合《景岳全书》",
        "modifications":[{"condition":"B症状发热盗汗","adjustment":"加青蒿、鳖甲、丹皮滋阴清热"},{"condition":"化疗后骨髓抑制","adjustment":"加黄芪、当归益气养血"},{"condition":"局部肿块大","adjustment":"加夏枯草、浙贝母软坚散结"}],
        "acupuncture_rx":["天鼎","扶突","肩井","曲池","足三里","丰隆","太冲","血海"],
        "dietary_therapy":"高蛋白高能量易消化饮食；忌烟酒辛辣",
        "prognosis":"DLBCL R-CHOP治愈率约60-70%",
        "caution":"CAR-T后CRS和ICANS需密切监护"},
    teaching={"difficulty":5,"stage":"副主任医",
        "sage_ref_zhang":"张仲景小柴胡汤为和解少阳治疗淋巴结肿大的思路。",
        "sage_ref_sun":"《备急千金要方》孙思邈记载治恶核肿痛方。",
        "typical_case":"患者刘某，女，38岁。右颈部淋巴结肿大3月伴B症状。PET-CT Deauville 5分，活检DLBCL(GCB型)。R-CHOPx6周期+消瘰丸合柴胡疏肝散。2周期后PET-CT CR。续中药巩固。随访3年无复发。",
        "teaching_points":["石疽与淋巴瘤对应","R-CHOP+中药减毒增效","CAR-T与中医扶正祛邪"],
        "exam_questions":["从痰瘀互结分析淋巴瘤的证候特点？"]}
))

# DSU-00081 格林-巴利综合征
new.append(make_dsu(
    id="DSU-00081",
    disease_side={"disease_name":"格林-巴利综合征(多发性神经炎)","icd_code":"8C01","category":"神经系统疾病",
        "molecular_targets":["神经节苷脂GM1/GD1a","TLR4/NF-kappaB自身免疫炎症","电压门控钠通道","补体C5b-9"],
        "gene_pathways":["cAMP-PKA神经修复通路","TLR4-MyD88-NF-kappaB周围神经免疫通路","MAPK轴突再生通路"],
        "biomarkers":["脑脊液蛋白-细胞分离","NCV减慢F波消失","抗GM1/GD1a抗体"],
        "epidemiology":"年发病率约1-2/10万，空肠弯曲菌是最常见前驱",
        "western_treatment":"IVIG 0.4g/kg/日x5日；血浆置换；呼吸支持"},
    syndrome_side={"syndrome_name":"湿热浸淫、筋脉失养证(痿证)","pattern_type":"脾胃湿热证","zangfu":"脾·胃·经络","six_channels":"太阴病",
        "eight_principles":{"yin_yang":"阳证","exterior_interior":"里证","cold_heat":"热证","deficiency_excess":"虚实夹杂"},
        "key_symptoms":["急性四肢对称性弛缓性瘫痪","远端感觉异常(麻木刺痛)","腱反射减弱或消失","从下肢向上发展"],
        "secondary_symptoms":["前驱感染史(腹泻/上感后1-4周)","肌肉酸痛","自主神经紊乱","呼吸肌无力"],
        "tongue":"舌红苔黄腻或薄黄","pulse":"脉濡数或滑数",
        "field_theory":"本病属痿证范畴。湿热毒邪浸淫筋脉，气血阻滞、筋脉弛缓不收则为痿软。湿热不攘，大筋软短、小筋弛长——湿热为痿证重要病机。",
        "classical_basis":"《素问-痿论》：五脏因肺热叶焦发为痿躄。《素问-生气通天论》：湿热不攘弛长为痿。"},
    bridge={"mapping_type":"间接对应",
        "mapping_description":"四肢弛缓性瘫痪对应自身免疫性脱髓鞘导致神经传导阻滞。湿热对应自身免疫炎症。",
        "biological_basis":"前驱感染→分子模拟→抗GM1抗体→抗体结合郎飞结→补体MAC形成→钠通道簇破坏+巨噬细胞脱髓鞘→传导阻滞→瘫痪",
        "evidence_level":"D级-病例对照","key_references":["《GBS诊治指南》2023","《中医内科学-痿证》十三五教材"]},
    clinical={"recommended_formula":"加味二妙散合四妙勇安汤","formula_source":"《丹溪心法》合《验方新编》",
        "modifications":[{"condition":"呼吸困难","adjustment":"配合机械通气"},{"condition":"自主神经紊乱","adjustment":"加生脉散益气复脉"},{"condition":"恢复期气虚","adjustment":"合补中益气汤"}],
        "acupuncture_rx":["肩髃","曲池","合谷","环跳","阳陵泉","足三里","华佗夹脊穴"],
        "dietary_therapy":"高蛋白高维生素饮食；吞咽障碍者鼻饲；康复期功能锻炼",
        "prognosis":"约80%可基本恢复；约5-15%残留永久后遗症",
        "caution":"监测呼吸功能和自主神经；VTE预防"},
    teaching={"difficulty":4,"stage":"主治医",
        "sage_ref_zhang":"《金匮要略》论但手臂不遂者此为痹——肢体瘫痪的鉴别。",
        "sage_ref_sun":"《备急千金要方》孙思邈论风痹治疗。",
        "typical_case":"患者徐某，男，36岁。腹泻后1周双下肢进行性无力3天累及双上肢。CSF蛋白1.8g/L。加味二妙散合四妙勇安汤+IVIG。2周后病情停止，1月可坐，3月扶行，6月基本自理。",
        "teaching_points":["GBS湿热浸淫筋脉失养","IVIG+中药祛湿通络"],
        "exam_questions":["从湿热不攘大筋软短小筋弛长分析GBS经典？"]}
))

# DSU-00082 重症肌无力
new.append(make_dsu(
    id="DSU-00082",
    disease_side={"disease_name":"重症肌无力","icd_code":"8C60","category":"神经系统疾病",
        "molecular_targets":["AChR乙酰胆碱受体","MuSK肌肉特异性酪氨酸激酶","补体C5b-9","RyR兰尼碱受体"],
        "gene_pathways":["AChR聚集-突触后膜信号通路","补体经典活化通路","NF-kappaB自身免疫通路"],
        "biomarkers":["新斯的明试验阳性","AChR抗体阳性(约85%)","MuSK抗体阳性","重复神经电刺激递减"],
        "epidemiology":"患病率约15-25/10万，好发20-40岁女性(男女比约1:2)",
        "western_treatment":"溴吡斯的明(对症)；免疫抑制(激素/MMF)；胸腺切除；C5抑制剂/FcRn拮抗剂"},
    syndrome_side={"syndrome_name":"脾胃虚弱、中气下陷证(痿证/睑废)","pattern_type":"脾肾阳虚证","zangfu":"脾·肾·筋脉","six_channels":"太阴病",
        "eight_principles":{"yin_yang":"阴证","exterior_interior":"里证","cold_heat":"寒证","deficiency_excess":"虚证"},
        "key_symptoms":["晨轻暮重波动性肌无力","上睑下垂/复视","吞咽困难声音嘶哑","四肢近端无力"],
        "secondary_symptoms":["咀嚼疲劳","颈肌无力头前倾","呼吸困难(危象)","苦笑面容"],
        "tongue":"舌淡苔薄白","pulse":"脉沉细弱或虚大无力",
        "field_theory":"脾主四肢肌肉。脾胃虚弱则气血不足、肌肉失养。中气不足升举无力则上睑下垂。脾阳不升则吞咽困难。治痿独取阳明——补益脾胃贯穿全程。",
        "classical_basis":"《素问-太阴阳明论》：脾病不能为胃行其津液故四肢不用焉。"},
    bridge={"mapping_type":"机制对应",
        "mapping_description":"波动性肌无力对应AChR抗体导致突触后膜AChR破坏、信号传递障碍。中气下陷对应AChR破坏导致的肌力不足。",
        "biological_basis":"胸腺异常→AChR抗体产生+补体C5b-9→突触后膜AChR减少/破坏→终极电位振幅↓→不足以触发动作电位→肌无力",
        "evidence_level":"C级-队列研究","key_references":["《MG诊治指南》2023","《中医内科学-痿证》十三五教材"]},
    clinical={"recommended_formula":"补中益气汤合黄芪桂枝五物汤","formula_source":"《脾胃论》合《金匮要略》",
        "modifications":[{"condition":"复视明显","adjustment":"加枸杞、菊花养肝明目"},{"condition":"吞咽困难","adjustment":"加桔梗、枳壳、威灵仙利咽"},{"condition":"呼吸困难","adjustment":"加山萸肉、五味子纳气"},{"condition":"激素后阴虚","adjustment":"加知母、黄柏、生地滋阴"}],
        "acupuncture_rx":["攒竹","丝竹空","阳白","足三里","脾俞","肾俞","百会","气海"],
        "dietary_therapy":"高蛋白易消化饮食；避免劳累感染情绪波动",
        "prognosis":"免疫治疗有效率80-90%",
        "caution":"危象需紧急呼吸支持；溴吡斯的明需长期维持"},
    teaching={"difficulty":4,"stage":"主治医",
        "sage_ref_zhang":"《金匮要略》论极虚——气血虚弱的理论。",
        "sage_ref_sun":"《备急千金要方》孙思邈论肺气虚。",
        "typical_case":"患者杨某，女，32岁。上睑下垂晨轻暮重2月伴复视。新斯的明(+)AChR抗体(+)8.5nmol/L。补中益气汤合黄芪桂枝五物汤+溴吡斯的明60mg tid+泼尼松30mg/日。4周后OSCAR从32降至12，8周明显好转。",
        "teaching_points":["脾主肌肉——MG的中医核心病机","治痿独取阳明——补脾胃","益气升阳与溴吡斯的明改善传导"],
        "exam_questions":["MG与Lambert-Eaton综合征鉴别？"]}
))

# DSU-00083 阿尔茨海默病
new.append(make_dsu(
    id="DSU-00083",
    disease_side={"disease_name":"阿尔茨海默病","icd_code":"8A20","category":"神经系统疾病",
        "molecular_targets":["beta-淀粉样蛋白Abeta","tau蛋白(NFT核心)","乙酰胆碱酯酶AChE","BACE1 beta-分泌酶"],
        "gene_pathways":["APP/PS1/PS2-gamma分泌酶淀粉样级联通路","tau过磷酸化GSK-3beta/CDK5通路","胆碱能突触通路","小胶质细胞TREM2神经炎症通路"],
        "biomarkers":["MRI内侧颞叶萎缩MTA评分","PET-Abeta/Tau显像","CSF Abeta42下降/p-tau181升高","MoCA/MMSE评分"],
        "epidemiology":"65岁以上患病率约5-8%，85岁以上约30-50%，中国约1000万患者",
        "western_treatment":"多奈哌齐/卡巴拉汀(胆碱酯酶抑制剂)；美金刚(NMDA拮抗剂)；Abeta单抗(仑卡奈单抗/多奈单抗)"},
    syndrome_side={"syndrome_name":"髓海不足、肾虚痰瘀证(痴呆)","pattern_type":"脾肾阳虚证","zangfu":"肾·心·脾","six_channels":"少阴病",
        "eight_principles":{"yin_yang":"阴证","exterior_interior":"里证","cold_heat":"寒热错杂","deficiency_excess":"虚证"},
        "key_symptoms":["进行性近记忆力下降(首发症状)","失语找词困难","失用操作不能","失认不认识亲人"],
        "secondary_symptoms":["性格改变淡漠易激惹","空间定向障碍迷路","执行功能下降","行为异常游走重复"],
        "tongue":"舌淡暗或有瘀点苔薄白或白腻","pulse":"脉沉细涩或弦细",
        "field_theory":"肾藏精生髓充脑。肾精亏虚髓海不足则脑失濡养、神明失聪。脾虚不运则痰浊内生。气滞血瘀则瘀阻脑络。痰瘀虚三者互结。",
        "classical_basis":"《灵枢-海论》：髓海不足则脑转耳鸣胫酸眩冒目无所见懈怠安卧。"},
    bridge={"mapping_type":"机制对应",
        "mapping_description":"记忆力下降认知障碍对应Abeta沉积导致tau过磷酸化NFT神经元死亡脑萎缩。髓海不足对应脑萎缩，痰瘀对应Abeta沉积和tau缠结。",
        "biological_basis":"APP突变/APOEe4→Abeta42沉积老年斑→微胶质TREM2→神经炎症→tau过磷酸化→NFT→神经元丢失→脑萎缩→ACh下降→认知下降",
        "evidence_level":"C级-队列研究","key_references":["《阿尔茨海默病诊治指南》2023","《中医内科学-健忘/痴呆》十三五教材"]},
    clinical={"recommended_formula":"七福饮合当归芍药散","formula_source":"《景岳全书》合《金匮要略》",
        "modifications":[{"condition":"痰浊重言语不清","adjustment":"加石菖蒲、远志、胆南星化痰开窍"},{"condition":"血瘀明显","adjustment":"加川芎、丹参、水蛭化瘀通络"},{"condition":"精神行为症状","adjustment":"加龙骨、牡蛎、酸枣仁安神"}],
        "acupuncture_rx":["百会","神庭","本神","风池","四神聪","足三里","丰隆","太溪","三阴交"],
        "dietary_therapy":"地中海饮食、Omega-3(深海鱼)、保持社交和认知训练",
        "prognosis":"进行性不可逆病程；药物可延缓认知下降6-12月",
        "caution":"Abeta单抗需MRI监测ARIA；关注照顾者负担"},
    teaching={"difficulty":5,"stage":"主任医",
        "sage_ref_zhang":"《金匮要略》薯蓣丸治虚劳诸不足——为AD扶正治疗提供思路。",
        "sage_ref_sun":"《备急千金要方》定志丸(人参远志茯苓菖蒲)治疗健忘。",
        "typical_case":"患者张某，男，75岁。记忆下降3年MMSE 18/30。MRI双侧海马萎缩MTA 3级。七福饮合当归芍药散+多奈哌齐。6月后MMSE 20/30。1年MMSE 19/30(缓慢下降)。",
        "teaching_points":["AD肾虚髓空与脑萎缩对应","孙思邈定志丸治疗健忘","Abeta单抗与中医药协同"],
        "exam_questions":["从髓海不足分析AD？"]}
))

assert len(new) == 8
# Merge with existing
p = os.path.join(DIR, "dsu-samples-006.json")
with open(p, 'r', encoding='utf-8') as f:
    ex = json.load(f)
assert len(ex) == 12
all_dsu = ex + new
assert len(all_dsu) == 20
for i,u in enumerate(all_dsu):
    eid = f"DSU-{64+i:05d}"
    assert u["id"] == eid, f"Pos {i}: {u['id']} != {eid}"
with open(p, 'w', encoding='utf-8') as f:
    json.dump(all_dsu, f, ensure_ascii=False, indent=2)
print(f"✅ Batch 006 complete: 20 DSUs (DSU-00064 to DSU-00083)")
