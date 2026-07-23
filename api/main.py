"""
医圣人格API服务器 v2.0 — Sage Persona API Server
- 张仲景/孙思邈人格 consult/teach/analyze_case (DeepSeek驱动)
- 病证知识图谱查询 (KG)
- 患者Agent症状自查/导诊/用药说明
- 药者Agent处方审核/药物相互作用/替代建议/库存管理/饮片溯源
"""
from __future__ import annotations
import os, json, re, urllib.request, urllib.error
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ── 配置 ──
SAGE_DIR = Path(__file__).parent.parent / "sages"
KG_DIR = Path(__file__).parent.parent / "kg-schema"
DEEPSEEK_API = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_KEY = os.environ.get("DEEPSEEK_API_KEY", "") or "«sk-placeholder»"
# 检查密钥是否有效（sk-开头+至少20字符）
LLM_AVAILABLE = bool(DEEPSEEK_KEY.startswith("sk-") and len(DEEPSEEK_KEY) > 20)
MODEL = "deepseek-chat"

app = FastAPI(title="医圣人格API v2", version="2.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ── 数据结构 ──
class ConsultRequest(BaseModel):
    user_role: str = "healer"; sage_id: str = "sage-zhang-zhongjing"
    user_level: str = "住院医-1"; chief_complaint: str
    key_symptoms: list[str] = []; tongue: Optional[str] = None
    pulse: Optional[str] = None; context: Optional[str] = None

class TeachRequest(BaseModel):
    sage_id: str = "sage-zhang-zhongjing"; topic: str
    student_level: str = "住院医-1"; duration_minutes: int = 30
    focus: Optional[str] = None

class AnalyzeCaseRequest(BaseModel):
    sage_id: str = "sage-zhang-zhongjing"; chief_complaint: str
    history: str; four_exams: dict = {}
    treatment_so_far: Optional[str] = None; focus: str = "六经辨证"

class SymptomCheckRequest(BaseModel):
    symptoms: list[str]; duration_days: int = 1
    age: Optional[int] = None; gender: Optional[str] = None

class TriageRequest(BaseModel):
    symptoms: list[str]; age: int = 30; preexisting: list[str] = []

class MedicationRequest(BaseModel):
    drug_name: str; form: str = "中成药"

# ── 药者数据结构 ──
class PrescriptionReviewRequest(BaseModel):
    herbs: list[str]
    patient: dict = {}
    review_type: str = "full"  # full | quick | pregnancy

class InteractionRequest(BaseModel):
    drug_a: str; drug_b: str
    category_a: str = "中药"; category_b: str = "中药"

class SubstitutionRequest(BaseModel):
    herb: str; reason: str = "缺货"

class InventoryRequest(BaseModel):
    herb: str

class TraceRequest(BaseModel):
    herb: str; batch: str = ""

# ── 械者数据结构 ──
class DeviceMaintenanceRequest(BaseModel):
    device_id: str; metric: str = "status"; days: int = 7

class ImagingRequest(BaseModel):
    modality: str = ""; findings: str = ""; clinical_context: str = ""

class ProcurementRequest(BaseModel):
    device_type: str = ""; budget: float = 100; department: str = ""

class EmergencyRequest(BaseModel):
    device_type: str = ""; fault_scenario: str = ""

# 十八反十九畏知识库
INCOMPATIBILITY_RULES = {
    "十八反": [
        {"group": "乌头类", "herbs": ["川乌","草乌","附子"], "antagonizes": ["半夏","瓜蒌","瓜蒌皮","瓜蒌仁","天花粉","川贝母","浙贝母","白蔹","白及"]},
        {"group": "甘草", "herbs": ["甘草"], "antagonizes": ["海藻","大戟","甘遂","芫花"]},
        {"group": "藜芦", "herbs": ["藜芦"], "antagonizes": ["人参","沙参","丹参","玄参","细辛","白芍","赤芍"]},
    ],
    "十九畏": [
        {"pair": ["硫黄","朴硝"]}, {"pair": ["水银","砒霜"]}, {"pair": ["狼毒","密陀僧"]},
        {"pair": ["巴豆","牵牛"]}, {"pair": ["丁香","郁金"]}, {"pair": ["川乌","犀角"]},
        {"pair": ["草乌","犀角"]}, {"pair": ["牙硝","三棱"]}, {"pair": ["官桂","石脂"]},
        {"pair": ["人参","五灵脂"]},
    ],
    "妊娠禁忌": [
        {"level": "禁用", "herbs": ["水蛭","虻虫","三棱","莪术","巴豆","牵牛","大戟","芫花","甘遂","麝香","蟾酥","雄黄","斑蝥"]},
        {"level": "慎用", "herbs": ["附子","乌头","桃仁","红花","大黄","枳实","芒硝","牛膝","丹皮","肉桂","半夏","冬葵子"]},
    ]
}
DOSE_LIMITS = {
    "附子(制)": {"min":3,"max":9,"note":"先煎30-60分钟"},
    "细辛": {"min":1,"max":3,"note":"散剂不超过6g"},
    "马钱子": {"min":0.3,"max":0.6,"note":"炮制后入丸散"},
    "川乌": {"min":1.5,"max":3,"note":"先煎1小时以上"},
    "草乌": {"min":1.5,"max":3,"note":"先煎1小时以上"},
    "大黄(生)": {"min":3,"max":15,"note":"后下"},
    "麻黄": {"min":2,"max":9,"note":"高血压/心衰慎用"},
    "蟾酥": {"min":0.015,"max":0.03,"note":"入丸散，不入煎剂"},
}

# ── LLM调用 ──
def call_llm(system_prompt: str, user_prompt: str, max_tokens: int = 1024) -> str:
    """调用DeepSeek LLM（密钥有效时）或返回prompt（无密钥时演示）"""
    if not LLM_AVAILABLE:
        return f"[演示模式] 请配置有效DEEPSEEK_API_KEY以启用AI推理。\n\n=== 将发送给LLM的System Prompt ===\n{system_prompt[:500]}\n\n=== User Prompt ===\n{user_prompt[:500]}"
    payload = json.dumps({
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "max_tokens": max_tokens,
        "temperature": 0.7
    }).encode()
    req = urllib.request.Request(DEEPSEEK_API, data=payload,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {DEEPSEEK_KEY}"})
    try:
        resp = urllib.request.urlopen(req, timeout=60)
        data = json.loads(resp.read())
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        return f"[LLM调用失败: {e}]"

# ── 医圣引擎 ──
class SageEngine:
    def __init__(self):
        self.sages = {}; self._load_sages()
    def _load_sages(self):
        for sage_dir in SAGE_DIR.iterdir():
            soul_file = sage_dir / "SOUL.md"
            if soul_file.exists():
                c = soul_file.read_text(encoding="utf-8")
                sid = re.search(r'name:\s*(\S+)', c)
                dn = re.search(r'display_name:\s*(\S+)', c)
                rid = sid.group(1) if sid else sage_dir.name
                self.sages[rid] = {"id": rid, "name": dn.group(1) if dn else rid, "soul": c}
                print(f"  ✅ {rid}")
    def get_soul(self, sage_id: str) -> str:
        s = self.sages.get(sage_id)
        if not s: raise HTTPException(404, f"医圣 '{sage_id}' 未找到")
        return s["soul"]

engine = SageEngine()

# ── 医圣API ──
@app.get("/health")
def health():
    return {"status": "ok", "sages_loaded": len(engine.sages), "version": "2.0.0"}

@app.get("/sages")
def list_sages():
    return [{"id": s["id"], "name": s["name"],
             "available_apis": ["consult","teach","analyze_case"]}
            for s in engine.sages.values()]

@app.post("/consult/{sage_id}")
def consult(sage_id: str, req: ConsultRequest):
    """临床咨询——调用DeepSeek以医圣人格回答"""
    soul = engine.get_soul(sage_id)
    prompt = f"""你是一位中医临床导师。以下用户向你就诊：
- 医师阶段：{req.user_level}
- 主诉：{req.chief_complaint}
- 症状：{', '.join(req.key_symptoms)}
- 舌象：{req.tongue or '未提供'}
- 脉象：{req.pulse or '未提供'}
- 背景：{req.context or '无'}

请：
1. 先辨证（六经定位+八纲属性）
2. 后论治（推荐方药思路，不含具体克数）
3. 引用至少一条经典原文
4. 给出教学思考题
5. 末尾附免责声明"""
    reply = call_llm(soul, prompt)
    return {"sage_id": sage_id, "mode": "consult", "reply": reply}

@app.post("/teach/{sage_id}")
def teach(sage_id: str, req: TeachRequest):
    """师带徒教学——DeepSeek驱动的教学输出"""
    soul = engine.get_soul(sage_id)
    prompt = f"""你正在带教一名{req.student_level}阶段的青年医师。
教学主题：{req.topic}，课时{req.duration_minutes}分钟。

要求：
1. 师带徒对话风格，先提问引导
2. 每项论点引用经典原文
3. 穿插临床案例
4. 难度匹配{req.student_level}阶段
5. 结尾布置3个思考题"""
    reply = call_llm(soul, prompt)
    return {"sage_id": sage_id, "mode": "teach", "reply": reply}

@app.post("/analyze-case/{sage_id}")
def analyze_case(sage_id: str, req: AnalyzeCaseRequest):
    """医案分析——DeepSeek驱动"""
    soul = engine.get_soul(sage_id)
    exams = "\n".join([f"  {k}: {v}" for k, v in req.four_exams.items()])
    prompt = f"""请以{req.focus}为框架分析以下医案：

主诉：{req.chief_complaint}
现病史：{req.history}
四诊：{exams}
已施治：{req.treatment_so_far or '尚未治疗'}

要求：
1. 定位当前证候（六经/八纲/脏腑）
2. 辨病机
3. 推荐方药思路（不含剂量）
4. 预测传变趋势
5. 附经典原文引用"""
    reply = call_llm(soul, prompt)
    return {"sage_id": sage_id, "mode": "analyze_case", "reply": reply}

# ── 知识图谱API ──
def load_all_dsus():
    units = []
    samples_dir = KG_DIR / "samples"
    if samples_dir.exists():
        for f in sorted(samples_dir.glob("dsu-samples-*.json")):
            try: units.extend(json.loads(f.read_text(encoding="utf-8")))
            except: pass
    return units

@app.get("/kg/query")
def kg_query(disease: str = "", syndrome: str = "", keyword: str = "", limit: int = 20):
    all_dsu = load_all_dsus()
    results = []
    for u in all_dsu:
        if disease and disease not in u["disease_side"]["disease_name"]: continue
        if syndrome and syndrome not in u["syndrome_side"]["syndrome_name"]: continue
        if keyword:
            haystack = (u["disease_side"]["disease_name"] + u["syndrome_side"]["syndrome_name"]
                       + u["clinical"]["recommended_formula"] + json.dumps(u["disease_side"]["molecular_targets"]))
            if keyword not in haystack: continue
        results.append({
            "id": u["id"], "disease": u["disease_side"]["disease_name"],
            "syndrome": u["syndrome_side"]["syndrome_name"],
            "formula": u["clinical"]["recommended_formula"],
            "difficulty": u["teaching"]["difficulty"],
            "icd": u["disease_side"].get("icd_code",""),
            "zangfu": u["syndrome_side"].get("zangfu",""),
            "six_channels": u["syndrome_side"].get("six_channels",""),
        })
        if len(results) >= limit: break
    return {"total": len(all_dsu), "matched": len(results), "results": results}

@app.get("/kg/detail/{dsu_id}")
def kg_detail(dsu_id: str):
    for u in load_all_dsus():
        if u["id"] == dsu_id: return u
    raise HTTPException(404, f"DSU {dsu_id} 未找到")

@app.get("/kg/stats")
def kg_stats():
    all_dsu = load_all_dsus()
    return {"total": len(all_dsu), "files": len(list(KG_DIR.glob("samples/dsu-samples-*.json")))}

# ── 患者Agent API ──
@app.post("/patients/symptom-check")
def symptom_check(req: SymptomCheckRequest):
    """症状自查——患者Agent核心功能"""
    symptoms_str = "、".join(req.symptoms)
    prompt = f"""你是一位耐心的健康导诊助手。用户描述了以下症状：
【症状】{symptoms_str}
【持续时间】{req.duration_days}天
{'【年龄】' + str(req.age) if req.age else ''}
{'【性别】' + req.gender if req.gender else ''}

请用通俗语言回答（不用中医术语解释中医术语）：
1. 可能的疾病方向（2-3个，用"可能"语气）
2. 建议就诊科室
3. 紧急程度评估（急诊/门诊/居家观察）
4. 就医前可以做的自我管理建议
5. 什么情况下需要立即就医

末尾附免责声明：以上分析仅供参考，请以实际就诊医师诊断为准。"""
    # 使用通用系统提示
    system = "你是一位专业、耐心、亲切的健康导诊助手。你的使命是帮助患者理解自己的症状，给出安全的就诊建议。你永远不做出明确诊断，永远不推荐具体药物。安全第一。"
    reply = call_llm(system, prompt, max_tokens=800)
    return {"mode": "symptom_check", "symptoms": req.symptoms, "reply": reply}

@app.post("/patients/triage")
def triage(req: TriageRequest):
    """导诊建议"""
    s = "、".join(req.symptoms)
    p = "、".join(req.preexisting) if req.preexisting else "无"
    prompt = f"""用户症状：{s}，年龄{req.age}岁，既往病史：{p}
请推荐就诊科室和紧急程度（急诊/门诊/居家观察），并给出就诊前准备建议。"""
    reply = call_llm("你是一位分诊护士助手，专业推荐就诊科室。", prompt, max_tokens=500)
    return {"mode": "triage", "reply": reply}

@app.post("/patients/medication")
def medication(req: MedicationRequest):
    """用药说明"""
    prompt = f"""用户询问{req.form}「{req.drug_name}」的用法。
请用通俗语言说明：用法用量、注意事项、禁忌、常见副作用（如有）。
如是中药，可简要介绍其方剂来源和功效。末尾附免责声明。"""
    reply = call_llm("你是一位药学知识科普助手。", prompt, max_tokens=600)
    return {"mode": "medication", "drug": req.drug_name, "form": req.form, "reply": reply}

# ── 药者Agent API ──
def _match_herb(name: str, candidates: list[str]) -> list[str]:
    """中药名模糊匹配"""
    return [h for h in candidates if name in h or h in name]

@app.post("/pharmacists/review")
def prescription_review(req: PrescriptionReviewRequest):
    """处方审核—十八反十九畏剂量妊娠禁忌全检"""
    violations = []; warnings = []
    herb_names = []
    for h in req.herbs:
        h2 = re.sub(r'\(.*?\)|（.*?）|[0-9.]+g|[0-9.]+克','',h).strip()
        if h2: herb_names.append(h2)

    # 十八反检查
    for rule in INCOMPATIBILITY_RULES["十八反"]:
        present = [h for h in herb_names if h in rule["herbs"]]
        if present:
            antagonized = [h for h in herb_names if h in rule["antagonizes"]]
            if antagonized:
                violations.append({
                    "rule": "十八反", "group": rule["group"],
                    "herbs_found": present, "antagonizes_found": antagonized
                })

    # 十九畏检查
    for pair in INCOMPATIBILITY_RULES["十九畏"]:
        a, b = pair["pair"]
        if a in herb_names and b in herb_names:
            violations.append({"rule": "十九畏", "pair": [a, b]})

    # 妊娠禁忌
    if req.patient.get("pregnant"):
        for level_grp in INCOMPATIBILITY_RULES["妊娠禁忌"]:
            found = [h for h in herb_names if h in level_grp["herbs"]]
            if found:
                violations.append({"rule": f"妊娠{level_grp['level']}", "herbs": found})

    # 剂量检查
    for h in req.herbs:
        for limit_name, limit in DOSE_LIMITS.items():
            if limit_name.split("(")[0] in h or limit_name in h:
                doses = re.findall(r'(\d+\.?\d*)\s*g', h)
                if doses:
                    d = float(doses[0])
                    if d > limit["max"]:
                        warnings.append({"herb": h, "issue": f"超量: {d}g > 上限{limit['max']}g", "note": limit["note"]})

    status = "reject" if violations else ("warn" if warnings else "pass")
    return {
        "mode": "prescription_review", "status": status,
        "violations": violations, "warnings": warnings,
        "herbs_count": len(req.herbs)
    }

@app.post("/pharmacists/interaction")
def drug_interaction(req: InteractionRequest):
    """药物相互作用查询"""
    # 检查十八反十九畏
    violations = []
    for rule in INCOMPATIBILITY_RULES["十八反"]:
        if req.drug_a in rule["herbs"] and req.drug_b in rule["antagonizes"]:
            violations.append({"rule": "十八反", "detail": f"{req.drug_a}与{req.drug_b}相反"})
        if req.drug_b in rule["herbs"] and req.drug_a in rule["antagonizes"]:
            violations.append({"rule": "十八反", "detail": f"{req.drug_b}与{req.drug_a}相反"})
    for pair in INCOMPATIBILITY_RULES["十九畏"]:
        if set([req.drug_a, req.drug_b]) == set(pair["pair"]):
            violations.append({"rule": "十九畏", "detail": f"{req.drug_a}与{req.drug_b}相畏"})
    level = "禁忌" if violations else "安全"
    return {"drug_a": req.drug_a, "drug_b": req.drug_b, "level": level, "violations": violations}

@app.post("/pharmacists/substitute")
def substitute(req: SubstitutionRequest):
    """替代药品建议（调用LLM）"""
    prompt = f"""用户查询中药「{req.herb}」的替代方案，原因：{req.reason}。
请给出2-3个替代方案（按优先级排列），每个方案需说明：
1. 替代药物名
2. 替代原理（药性功效相似度）
3. 注意事项
末尾附免责声明：替代方案需经医师确认。"""
    system = f"你是一位资深中药学专家，熟悉《中药学》《本草纲目》等典籍。注意不可编造替代关系。"
    reply = call_llm(system, prompt, max_tokens=600)
    return {"mode": "substitute", "herb": req.herb, "reason": req.reason, "advice": reply}

@app.get("/pharmacists/inventory")
def inventory_check(herb: str):
    """库存查询 + 补货建议"""
    # 模拟库存数据（实际应从数据库读取）
    mock_inventory = {
        "麻黄": {"stock": 15, "unit": "kg", "reorder": 20, "monthly_usage": 12},
        "桂枝": {"stock": 28, "unit": "kg", "reorder": 15, "monthly_usage": 18},
        "甘草": {"stock": 45, "unit": "kg", "reorder": 30, "monthly_usage": 22},
        "柴胡": {"stock": 8, "unit": "kg", "reorder": 15, "monthly_usage": 10},
        "当归": {"stock": 5, "unit": "kg", "reorder": 20, "monthly_usage": 15},
        "黄芪": {"stock": 30, "unit": "kg", "reorder": 25, "monthly_usage": 20},
        "党参": {"stock": 22, "unit": "kg", "reorder": 20, "monthly_usage": 10},
        "大黄": {"stock": 12, "unit": "kg", "reorder": 10, "monthly_usage": 8},
    }
    match = _match_herb(herb, list(mock_inventory.keys()))
    if not match:
        return {"herb": herb, "found": False, "message": f"未找到「{herb}」的库存记录"}
    data = mock_inventory[match[0]]
    suggestion = "建议补货" if data["stock"] <= data["reorder"] else "库存充足"
    return {"herb": match[0], "stock": data["stock"], "unit": data["unit"],
            "reorder_point": data["reorder"], "monthly_usage": data["monthly_usage"],
            "suggestion": suggestion, "found": True}

@app.get("/pharmacists/trace")
def herb_trace(herb: str, batch: str = ""):
    """饮片溯源查询"""
    mock_traces = {
        "黄芪": {"origin": "甘肃定西", "processor": "甘肃天士力中药饮片有限公司",
                 "qc_date": "2026-06-15", "standard": "《中国药典》2025版",
                 "distributor": "九州通医药集团"},
        "当归": {"origin": "甘肃岷县", "processor": "岷县当归加工厂",
                 "qc_date": "2026-06-10", "standard": "《中国药典》2025版",
                 "distributor": "华润医药"},
        "三七": {"origin": "云南文山", "processor": "文山三七产业股份有限公司",
                 "qc_date": "2026-05-20", "standard": "《中国药典》2025版",
                 "distributor": "国药控股"},
        "枸杞": {"origin": "宁夏中宁", "processor": "宁夏枸杞产业发展有限公司",
                 "qc_date": "2026-07-01", "standard": "《中国药典》2025版",
                 "distributor": "上海医药"},
        "人参": {"origin": "吉林抚松", "processor": "吉林长白山人参有限公司",
                 "qc_date": "2026-04-10", "standard": "《中国药典》2025版",
                 "distributor": "广州医药"},
    }
    match = _match_herb(herb, list(mock_traces.keys()))
    if not match:
        return {"herb": herb, "found": False, "message": f"未找到「{herb}」的溯源信息"}
    data = mock_traces[match[0]]
    return {"herb": match[0], "batch": batch or "默认批次", "trace": data, "found": True}

# ── 械者Agent API ──
# 设备知识库
DEVICE_DB = {
    "CT-001": {"name":"西门子SOMATOM Definition Flash","type":"CT","dept":"影像科","status":"运行"},
    "CT-002": {"name":"GE Revolution CT","type":"CT","dept":"影像科","status":"运行"},
    "MRI-001":{"name":"西门子MAGNETOM Vida 3T","type":"MRI","dept":"影像科","status":"运行"},
    "US-001": {"name":"Philips EPIQ 7C","type":"超声","dept":"心血管科","status":"运行"},
    "DR-001": {"name":"飞利浦DigitalDiagnost C90","type":"DR","dept":"影像科","status":"运行"},
}
QC_CYCLES = {"CT":"年度","MRI":"年度","超声":"年度","DR":"年度","生化分析仪":"半年","呼吸机":"季度"}
DEVICE_VENDORS = {
    "CT":[{"name":"西门子SOMATOM Drive","price":680,"score":4.8},
          {"name":"GE Revolution CT","price":620,"score":4.7},
          {"name":"联影uCT 960+","price":480,"score":4.5}],
    "超声":[{"name":"Philips EPIQ 7C","price":148,"score":4.9},
           {"name":"GE Vivid E95","price":145,"score":4.8},
           {"name":"Siemens Acuson SC2000","price":138,"score":4.3}],
    "MRI":[{"name":"西门子MAGNETOM Vida 3T","price":1200,"score":4.9},
           {"name":"GE SIGNA Architect 3T","price":1150,"score":4.8},
           {"name":"联影uMR 790","price":880,"score":4.4}],
}

@app.post("/devices/maintenance")
def device_maintenance(req: DeviceMaintenanceRequest):
    """设备维护预警"""
    if req.device_id not in DEVICE_DB:
        return {"found": False, "message": f"设备 {req.device_id} 未在册"}
    dev = DEVICE_DB[req.device_id]
    # 模拟预警逻辑
    return {
        "found": True, "device": dev,
        "status": "正常", "errors": [],
        "maintenance_suggestions": "建议按时执行季度保养",
        "last_maintenance": "2026-06-15",
        "next_maintenance": "2026-09-15",
        "qc_cycle": QC_CYCLES.get(dev["type"],"年度"),
        "alternative": [d for i,d in DEVICE_DB.items() if d["type"]==dev["type"] and i!=req.device_id]
    }

@app.post("/devices/imaging")
def imaging_assist(req: ImagingRequest):
    """影像AI预分析"""
    prompt = f"""影像模态：{req.modality}
影像所见：{req.findings}
临床背景：{req.clinical_context}

请以影像科辅助分析的角色回答：
1. 影像特征的鉴别诊断方向（2-3个可能）
2. 建议补充的影像序列或检查
3. 临床建议
末尾附免责声明。"""
    reply = call_llm("你是一位影像诊断学助手，擅长CT/MRI/超声图像分析。注意：不可出具正式诊断报告。", prompt, max_tokens=600)
    return {"modality": req.modality, "findings": req.findings, "pre_analysis": reply}

@app.post("/devices/procurement")
def procurement_eval(req: ProcurementRequest):
    """采购论证对比"""
    vendors = DEVICE_VENDORS.get(req.device_type, [])
    if not vendors:
        return {"found": False, "message": f"暂未收录{req.device_type}类设备数据"}
    in_budget = [v for v in vendors if v["price"] <= req.budget]
    return {
        "device_type": req.device_type, "budget": f"{req.budget}万", "department": req.department,
        "candidates": in_budget or vendors,
        "recommendation": in_budget[0]["name"] if in_budget else vendors[0]["name"],
        "note": "以上为参考对比，最终采购需结合临床实际需求进行论证"
    }

@app.get("/devices/qc")
def qc_calibration(device_type: str = "", department: str = ""):
    """质控校准管理"""
    cycle = QC_CYCLES.get(device_type, "未设定")
    return {
        "device_type": device_type, "department": department or "全院",
        "calibration_cycle": cycle, "last_calibration": "2026-01-15",
        "next_calibration": "2027-01-15", "status": "正常",
        "alerts": [], "history": [
            {"date":"2026-01-15","result":"合格","operator":"王工"},
            {"date":"2025-07-15","result":"合格","operator":"李工"}
        ]
    }

@app.get("/devices/trace")
def device_trace(device_type: str = "", batch: str = ""):
    """器械批次溯源"""
    mock = {
        "针灸针": {"manufacturer":"苏州医疗用品厂","brand":"华佗牌",
                   "sterilization":"环氧乙烷","expiry":"2028-06",
                   "distributor":"国药器械","hospital_dept":"针灸科"},
        "无菌包": {"manufacturer":"山东威高","brand":"威高",
                   "sterilization":"压力蒸汽","expiry":"2027-12",
                   "distributor":"华润医药","hospital_dept":"手术室"},
        "电针仪": {"manufacturer":"苏州天协","brand":"天协",
                   "sterilization":"非灭菌","expiry":"2030-01",
                   "distributor":"九州通","hospital_dept":"针灸科"},
    }
    data = mock.get(device_type)
    if not data:
        return {"found": False, "message": f"暂未收录{device_type}的溯源信息"}
    return {"device_type": device_type, "batch": batch or "默认批次",
            "trace": data, "found": True}

@app.post("/devices/emergency")
def emergency_plan(req: EmergencyRequest):
    """应急预案生成"""
    plans = {
        "CT": {"球管损坏":{"impact":"CT检查中断","downtime":"3-5天",
                        "alternatives":["启用备用CT","外送第三方影像中心"],
                        "immediate":["通知设备科紧急报修","调整患者检查安排","启动备用设备"]},
               "软件系统崩溃":{"impact":"重建/后处理中断","downtime":"4-8小时",
                           "alternatives":["重启系统","联系厂家远程支持"],
                           "immediate":["保存现有数据","重启DICOM服务","通知影像科主任"]}},
        "MRI": {"失超":{"impact":"MRI完全停机","downtime":"7-14天",
                       "alternatives":["转CT增强检查","外送MRI检查"],
                       "immediate":["疏散人员","通知厂家紧急处理","启动失超应急预案"]}},
    }
    device_plans = plans.get(req.device_type, {})
    plan = device_plans.get(req.fault_scenario, {})
    if not plan:
        return {"found": False, "message": f"暂未收录「{req.device_type}·{req.fault_scenario}」应急预案"}
    return {"device_type": req.device_type, "scenario": req.fault_scenario,
            "plan": plan, "found": True}

# ── 规者Agent API ──
# 医疗质量模拟数据
QUALITY_MOCK = {
    "内科": {"beds": 60, "indicators": {
        "2026Q2": {"bed_turnover":88,"avg_stay":8.2,"diag_accuracy":96,"cure_rate":92.5,
                   "drug_ratio":31,"infection_rate":2.1,"readmission_rate":4.5},
        "2026Q1": {"bed_turnover":85,"avg_stay":8.5,"diag_accuracy":95,"cure_rate":91.8,
                   "drug_ratio":33,"infection_rate":1.8,"readmission_rate":4.2},
    }},
    "针灸科": {"beds": 30, "indicators": {
        "2026Q2": {"bed_turnover":92,"avg_stay":6.5,"diag_accuracy":97,"cure_rate":94.0,
                   "drug_ratio":18,"infection_rate":0.5,"readmission_rate":2.1},
        "2026Q1": {"bed_turnover":90,"avg_stay":6.8,"diag_accuracy":96,"cure_rate":93.2,
                   "drug_ratio":20,"infection_rate":0.6,"readmission_rate":2.3},
    }},
}
TARGETS = {"bed_turnover":85,"avg_stay":9,"diag_accuracy":95,"cure_rate":90,
           "drug_ratio":30,"infection_rate":2,"readmission_rate":4}

@app.post("/regulators/quality")
def quality_control(department: str = "", period: str = "2026Q2"):
    """医疗质量分析"""
    dept_data = QUALITY_MOCK.get(department, QUALITY_MOCK.get("内科"))
    period_data = dept_data["indicators"].get(period, dept_data["indicators"]["2026Q2"])
    alerts = []; indicators = []
    for k, v in period_data.items():
        target = TARGETS.get(k)
        if target is not None:
            label = {"bed_turnover":"床位周转率%","avg_stay":"平均住院日(天)","diag_accuracy":"入出院诊断符合率%",
                     "cure_rate":"治愈好转率%","drug_ratio":"药占比%","infection_rate":"院内感染率%",
                     "readmission_rate":"非计划再入院率%"}.get(k, k)
            # 判断红黄绿灯: 高优指标(越高越好)或低优指标(越低越好)
            high_better = k in ("bed_turnover","diag_accuracy","cure_rate")
            status = "green"
            if high_better and v < target: status = "red" if v < target*0.95 else "yellow"
            if not high_better and v > target: status = "red" if v > target*1.05 else "yellow"
            if status != "green":
                alerts.append({"indicator":label,"value":v,"target":target,"status":status})
            indicators.append({"name":label,"value":v,"target":target,"status":status})
    return {"department":department,"period":period,"indicators":indicators,
            "alerts":alerts,"bed_count":dept_data["beds"],
            "summary":f"{'共'+str(len(alerts))+'项预警' if alerts else '全部指标正常'}"}

@app.post("/regulators/scheduling")
def scheduling(department: str = "", staff_list: list = [], days: int = 5):
    """智能排班建议"""
    if not staff_list:
        staff_list = [{"name":"主任医师","title":"主任","level":3},
                      {"name":"主治医师A","title":"主治","level":2},
                      {"name":"主治医师B","title":"主治","level":2},
                      {"name":"住院医师A","title":"住院","level":1},
                      {"name":"住院医师B","title":"住院","level":1}]
    # 按级别分配班次
    daily_workload = [35, 38, 42, 45, 48]  # 周一到周五预估值
    schedule = []
    for d in range(min(days, 5)):
        day_name = ["周一","周二","周三","周四","周五"][d]
        # 主任半天门诊，主治全天，住院医全天+夜班
        day_sched = {"date":day_name,"workload_est":daily_workload[d],
                     "morning":[s["name"] for s in staff_list if s["level"]>=2][:2],
                     "afternoon":[s["name"] for s in staff_list if s["level"]>=1][:3],
                     "night":[s["name"] for s in staff_list if s["level"]==1]}
        schedule.append(day_sched)
    return {"department":department,"schedule":schedule,
            "staff_count":len(staff_list),"notes":["周末值班另行安排","夜班由住院医师轮值"]}

@app.get("/regulators/utilization")
def utilization(department: str = ""):
    """资源利用率"""
    mock = {
        "影像科": {"bed_utilization":85,"equipment_utilization":78,"staff_utilization":92,
                  "avg_wait_time":45,"suggestions":["CT设备利用率偏低→增开夜间门诊"]},
        "针灸科": {"bed_utilization":92,"equipment_utilization":90,"staff_utilization":88,
                  "avg_wait_time":25,"suggestions":["床位利用率高→建议适当扩容"]},
    }
    data = mock.get(department, mock.get("针灸科"))
    return {"department":department or "全院","metrics":data,"suggestions":data.get("suggestions",[])}

@app.post("/regulators/dispatch")
def emergency_dispatch(scenario: str = "", resource_type: str = "人员"):
    """应急调度"""
    plans = {
        "突发公共卫生事件": {"人员":{"team":"应急医疗队(10人)","leader":"医务科主任",
                               "timeline":"2h内集结","dept":"急诊科+内科+感控科"},
                          "物资":{"supplies":"防护服200套/口罩500个/消毒液50L",
                                 "pharmacy":"抗病毒药/中药防疫方","logistics":"后勤保障组"}},
        "大规模外伤": {"人员":{"team":"创伤救治组(8人)","leader":"骨科主任",
                           "timeline":"1h内集结","dept":"骨科+普外+麻醉+ICU"},
                      "物资":{"supplies":"手术包/止血材料/血浆",
                             "pharmacy":"抗感染药/止痛药","logistics":"血库+手术室"}},
    }
    plan = plans.get(scenario, {}).get(resource_type, {})
    if not plan:
        return {"found":False,"message":f"暂未收录「{scenario}·{resource_type}」预案"}
    return {"scenario":scenario,"resource_type":resource_type,
            "dispatch_plan":plan,"found":True}

@app.get("/regulators/dashboard")
def dashboard(department: str = "全院"):
    """运营看板"""
    return {"department":department,"date":"2026-07-23",
            "bed_occupancy":"91%","avg_stay":"7.8天",
            "outpatient_daily":2850,"inpatient":420,
            "surgery_daily":15,"emergency_daily":180,
            "alerts":["药占比31%超目标建议关注"],
            "trends":["门诊量环比+5%","住院量环比+2%"]}

# ── 法者Agent API ──
RISK_LEVELS = {"高":75,"中":50,"低":25}
LAW_DB = {
    "医疗纠纷预防": {"law":"《医疗纠纷预防和处理条例》","articles":"第1-15条","summary":"医疗机构应当建立健全医疗纠纷预防和处理制度"},
    "知情同意": {"law":"《民法典》第1219条","articles":"第1219-1220条","summary":"医务人员应当向患者说明病情和医疗措施"},
    "医疗损害": {"law":"《民法典》侵权责任编","articles":"第1218-1228条","summary":"患者在诊疗活动中受到损害，医疗机构有过错的应赔偿"},
    "病历": {"law":"《病历书写基本规范》","articles":"全文","summary":"病历应当客观、真实、准确、及时、完整、规范"},
    "医师执业": {"law":"《医师法》","articles":"第23-30条","summary":"医师应当履行告知义务，保护患者隐私"},
}

@app.post("/legals/risk")
def risk_assessment(case_description: str = "", department: str = ""):
    """纠纷风险评估"""
    import random
    score = random.randint(25, 85)
    level = "高" if score >= 70 else ("中" if score >= 45 else "低")
    return {
        "risk_level": level, "score": score, "department": department,
        "risk_factors": [
            {"factor":"知情同意书签署情况","status":"✅ 已签署" if score < 60 else "⚠️ 需核实"},
            {"factor":"病历记录完整性","status":"✅ 完整" if score < 50 else "⚠️ 建议复核"},
            {"factor":"家属沟通记录","status":"⚠️ 需要完善" if score > 40 else "✅ 完整"},
        ],
        "immediate_actions": ["完善沟通记录","核对知情同意书完整性","启动院内调解程序"],
        "relevant_laws": [LAW_DB["医疗纠纷预防"], LAW_DB["医疗损害"]],
    }

@app.post("/legals/consent")
def consent_form(procedure: str = "", patient_condition: str = "", template_type: str = "手术"):
    """知情同意书生成"""
    return {
        "procedure": procedure, "template_type": template_type,
        "consent_draft": f"【{procedure}知情同意书·草稿】\n"
            f"患者诊断：{patient_condition or '请填写'}\n"
            f"手术目的：{procedure}  替代方案：保守治疗/其他术式\n"
            f"风险告知：出血/感染/麻醉意外/邻近器官损伤/效果未达预期\n"
            f"注意事项：术后遵医嘱复查\n\n⚠️ AI辅助生成草稿，请医师修改确认",
        "required_items": ["患者身份核对","诊断确认","手术方案说明","风险告知","替代方案说明","患者/家属签字"],
        "disclaimer": "本同意书为AI辅助生成草稿，不替代正式医疗文书"
    }

@app.get("/legals/regulation")
def regulation_query(keyword: str = ""):
    """法规查询"""
    if not keyword:
        return {"results": [{"law":k,**v} for k,v in LAW_DB.items()]}
    results = [{"law":k,**v} for k,v in LAW_DB.items() if keyword in k or keyword in v["summary"]]
    return {"keyword": keyword, "results": results or [LAW_DB.get("医疗纠纷预防")]}

@app.post("/legals/cases")
def case_matching(keywords: str = "", limit: int = 5):
    """历史案例匹配"""
    mock_cases = [
        {"title":"某患者术后感染纠纷案","court":"某市中级人民法院","focus":"术后感染·告知义务","result":"调解结案","year":2025},
        {"title":"某患者诊疗延误纠纷案","court":"某区人民法院","focus":"延误诊断·过错认定","result":"医院承担次要责任","year":2025},
        {"title":"某患者知情同意纠纷案","court":"某市中级人民法院","focus":"知情同意·告知不充分","result":"医院承担主要责任","year":2024},
    ]
    return {"matched": len(mock_cases), "cases": mock_cases[:limit]}

@app.post("/legals/prevention")
def prevention_advice(department: str = "", historical_issues: list = []):
    """纠纷预防建议"""
    suggestions = {
        "普外科":["术前讨论记录规范化","并发症告知清单标准化","术后24h内沟通记录"],
        "骨科":["手术效果预期管理","内固定材料选择告知","康复计划沟通"],
        "产科":["产程记录数字化","分娩方式选择告知","新生儿筛查告知"],
    }
    return {
        "department": department or "全院",
        "suggestions": suggestions.get(department,["完善知情同意流程","加强医患沟通培训","规范病历书写"]),
        "training_topics":["医疗纠纷预防与处理条例解读","知情同意规范操作","医患沟通技巧"],
        "checklist":["知情同意书签署","病历24h内完成","手术安全核对","出院指导记录"],
    }

# ── 启动 ──
if __name__ == "__main__":
    import uvicorn
    print(f"🧬 医圣人格API v2 启动中...")
    print(f"📚 医圣: {list(engine.sages.keys())}")
    print(f"🔬 KG: {KG_DIR / 'samples'}")
    print(f"🤖 LLM: {MODEL} {'✅ 已配置' if LLM_AVAILABLE else '⚠️ 需配置DEEPSEEK_API_KEY'}")
    uvicorn.run(app, host="0.0.0.0", port=8300)
