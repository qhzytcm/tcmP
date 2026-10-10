# -*- coding: utf-8 -*-
"""《中医智能仪器与可穿戴设备》(D07-S11) 教材素材工作簿生成器
GitBook 书稿 → Excel（目录结构 + 正文 + 真实器械数据 + Holter 实测 + embedding-code）。
产出：桌面 中医智能仪器与可穿戴设备.xlsx
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))
from gitbook_to_excel import SW, parse_summary, sanitize, write_book  # noqa: E402

REPO = SCRIPTS.parent
BOOK = REPO / "kg" / "device" / "book"
CAT = REPO / "kg" / "device" / "tcm-device.json"
OUT = Path.home() / "Desktop" / "中医智能仪器与可穿戴设备.xlsx"

F_T = Font(name="微软雅黑", size=13, bold=True, color="1F3864")
F_H = Font(name="微软雅黑", size=10.5, bold=True, color="2E5C8A")
F_B = Font(name="微软雅黑", size=10)
F_C = Font(name="Consolas", size=9.5)
AL_L = Alignment(horizontal="left", vertical="top", wrap_text=True)
AL_C = Alignment(horizontal="center", vertical="center", wrap_text=True)


def add_data_sheets(wb, cat, used):
    def new(name, w):
        return SW(wb.create_sheet(sanitize(name, used)), w)

    sw = new("器械分类", [8, 18, 44, 16]); sw.title("六类器械（C1–C6）", 4)
    sw.row(["编号", "类别", "代表器械", "信号"], [None] * 4, [F_H] * 4, [AL_C] * 4, 20)
    for c in cat["classes"]:
        sw.row([c["id"], c["name"], c["examples"], c["signal"]], [None] * 4, [F_B] * 4, [AL_C, AL_L, AL_L, AL_C], 18)

    sw = new("可穿戴形态", [8, 16, 30, 30]); sw.title("六种可穿戴形态与中医对应", 4)
    sw.row(["编号", "形态", "传感器", "中医语义"], [None] * 4, [F_H] * 4, [AL_C] * 4, 20)
    for f in cat["forms"]:
        sw.row([f["id"], f["name"], "·".join(f["sensors"]), f["tcm"]], [None] * 4, [F_B] * 4, [AL_C, AL_L, AL_L, AL_L], 18)

    sw = new("信号通道", [8, 16, 14, 46]); sw.title("六条生理信号通道", 4)
    sw.row(["编号", "通道", "采样率", "可提取特征"], [None] * 4, [F_H] * 4, [AL_C] * 4, 20)
    for s in cat["signals"]:
        sw.row([s["id"], s["name"], s["fs"], s["feat"]], [None] * 4, [F_B] * 4, [AL_C, AL_C, AL_C, AL_L], 18)

    sw = new("数据标准", [22, 42, 12]); sw.title("数据标准与平台落地", 3)
    sw.row(["标准", "作用", "状态"], [None] * 3, [F_H] * 3, [AL_C] * 3, 20)
    for s in cat["standards"]:
        sw.row([s["code"], s["name"], s["verify"]], [None] * 3, [F_B] * 3, [AL_C, AL_L, AL_C], 18)

    sw = new("AI算子", [8, 16, 34, 40]); sw.title("六类器材信息学算子", 4)
    sw.row(["编号", "算子", "算法", "用途"], [None] * 4, [F_H] * 4, [AL_C] * 4, 20)
    for o in cat["operators"]:
        sw.row([o["id"], o["name"], o["algo"], o["use"]], [None] * 4, [F_B] * 4, [AL_C, AL_L, AL_L, AL_L], 18)

    sw = new("平台接入", [34, 40]); sw.title("械者 六端点（sage-api 已上线）", 2)
    sw.row(["接口", "用途"], [None] * 2, [F_H] * 2, [AL_C] * 2, 20)
    for p in cat["platform"]:
        sw.row([p["api"], p["use"]], [None] * 2, [F_B] * 2, [AL_L, AL_L], 18)

    sw = new("Holter实测", [14, 10, 10, 10, 10, 10, 34]); sw.title("Holter 心律检测 · 六场景实测（仿真 RR 序列）", 7)
    sw.row(["场景", "HR", "SDNN", "RMSSD", "pNN50", "CV", "判读 + 中医提示"], [None] * 7, [F_H] * 7, [AL_C] * 7, 20)
    for k, v in cat["holter"].items():
        m = v["metrics"]
        sw.row([k, m["hr"], m["sdnn"], m["rmssd"], m["pnn50"], m["cv"],
                ",".join(v["diagnoses"]) + " ｜ " + "；".join(v["tcm_hints"])],
               [None] * 7, [F_B] * 7, [AL_C, AL_C, AL_C, AL_C, AL_C, AL_C, AL_L], 18)


EMBED = [
 ("① 时域 HRV（kg/device/holter.py）",
  "# RR 间期序列(ms) → 指标\nrr = [float(x) for x in rr_ms if x and x > 0]\nmean = sum(rr)/len(rr);  hr = 60000.0/mean\nsdnn  = sqrt(sum((x-mean)**2 for x in rr)/(len(rr)-1))\nrmssd = sqrt(sum(d*d for d in diffs)/len(diffs))\npnn50 = 100.0*sum(1 for d in diffs if abs(d) > 50)/len(diffs)"),
 ("② 节律判读与危险度排序",
  "if hr > 100: flags.append(('SINUS_TACHYCARDIA','warning'))\nif any(x >= 2500 for x in rr): flags.append(('PAUSE','danger'))\nif rmssd > 120 and pnn50 > 45 and cv > 0.12:\n    flags.append(('AF_SUSPECT','warning'))\nflags.sort(key=lambda f: order[f[1]])   # danger 先出"),
 ("③ ICD-11 桥接（scripts/icd11_client.py）",
  "import sqlite3\ncon = sqlite3.connect('tcmP/data/icd11_mms.db')   # 31,838 实体\nrow = con.execute('SELECT id, code, title FROM entities WHERE id=?', (fid,)).fetchone()"),
 ("④ 检索 FTS5 + RRF（scripts/tcm_embed.py）",
  "CREATE VIRTUAL TABLE dsu_fts USING fts5(id UNINDEXED, text, tokenize='unicode61');\nSELECT id, bm25(dsu_fts) FROM dsu_fts WHERE dsu_fts MATCH '心悸' ORDER BY 2 LIMIT 5;\n# RRF：score = Σ 1/(k + rank), k=60"),
 ("⑤ 上下文工程装配（context engineering）",
  "def build_context(q, k=5):\n    hits = retrieve(q, k)          # 向量 ∪ FTS5 ∪ RRF\n    return '\\n'.join(f'[{h.id}] {h.disease} / {h.syndrome}（证据 {h.evidence}）' for h in hits)\n# Top-5 ≈ 1.5K token，较全库 ↓≈95%"),
 ("⑥ 中医药关联提示（仅提示，非诊断）",
  "TCM_RULES = [('hr>100 且 rmssd>60', '心火亢盛 / 阴虚火旺'),\n             ('sdnn<30',           '心气虚 / 心脉瘀阻'),\n             ('AF_SUSPECT',        '心悸、怔忡（脉结代/促/涩）')]\n# 输出必须携带边界声明：不构成医学诊断，不得据以调整用药"),
]


def add_embed_sheet(wb, used):
    sw = SW(wb.create_sheet(sanitize("embedding-code", used)), [30, 96])
    sw.title("embedding code：HRV · 节律判读 · ICD-11 · FTS5 · RRF · 上下文工程", 2)
    for t, code in EMBED:
        sw.row([t, ""], [None, None], [F_H, F_B], [AL_L, AL_L], 18)
        for ln in code.split("\n"):
            sw.row(["", ln], [None, None], [F_B, F_C], [AL_L, AL_L], 15 if ln.strip() else 12)


def add_ext_sheets(wb, cat, used):
    """扩展层数据页：可感测四元 / 六快 / 健康自动评价 / 光遗传学 / 参考实现。"""
    SW_ = lambda nm, w: SW(wb.create_sheet(sanitize(nm, used)), w)
    sen = cat.get("sensing", {})
    sw = SW_("可感测四元", [8, 18, 18, 26, 26, 40]); sw.title("可感测物理量四元：光子 · 电子电压 · 质量 · 运动", 6)
    sw.row(["元", "名称", "单位", "传感器", "可测量", "中医对应"], [None] * 6, [F_H] * 6, [AL_C] * 6, 20)
    for q in sen.get("quanta", []):
        sw.row([q["id"], q["name"], q["unit"], q["sensor"], q["meas"], q["tcm"]],
               [None] * 6, [F_B] * 6, [AL_C, AL_L, AL_C, AL_L, AL_L, AL_L], 18)

    sw = SW_("六快", [8, 14, 34, 40, 18]); sw.title("中医药通用六快：吃 / 喝 / 拉 / 撒 / 睡 / 警觉安全", 5)
    sw.row(["编号", "快", "可感测", "中医关联", "承载四元"], [None] * 5, [F_H] * 5, [AL_C] * 5, 20)
    sq = sen.get("six_quick_quanta", {})
    for q in sen.get("six_quick", []):
        sw.row([q["id"], q["name"], q["sense"], q["tcm"], "+".join(sq.get(q["id"], []))],
               [None] * 5, [F_B] * 5, [AL_C, AL_C, AL_L, AL_L, AL_C], 18)

    hb = sen.get("demo_health", {})
    sw = SW_("健康自动评价", [14, 12, 40, 44]); sw.title(
        "健康自动评价（six-quick scoring）· 总分 %s（%s）· 覆盖 %s" % (hb.get("total"), hb.get("grade"), hb.get("coverage")), 4)
    sw.row(["维度", "评分", "证据（record）", "中医药提示"], [None] * 4, [F_H] * 4, [AL_C] * 4, 20)
    for k, v in (hb.get("dimensions") or {}).items():
        sw.row([v.get("name"), v.get("score"), json.dumps(v.get("evidence"), ensure_ascii=False), v.get("tcm")],
               [None] * 4, [F_B] * 4, [AL_C, AL_C, AL_L, AL_L], 18)
    sw.row(["总分 / 分级", "%s / %s" % (hb.get("total"), hb.get("grade")), "薄弱维度：" + "、".join(hb.get("weak_dimensions") or []),
            hb.get("disclaimer")], [None] * 4, [F_H] * 4, [AL_C, AL_C, AL_L, AL_L], 30)

    op = cat.get("optogenetics", {})
    nb = op.get("nobel", {})
    sw = SW_("光遗传学", [26, 78]); sw.title("光遗传学与神经调控 · 2026 诺贝尔生理学或医学奖", 2)
    sw.row(["项", "内容"], [None, None], [F_H, F_H], [AL_C, AL_L], 20)
    sw.row(["奖项 / 日期 / 奖金", "%s · %s · %s SEK" % (nb.get("prize"), nb.get("date"), nb.get("amount_sek"))], [None, None], [F_B, F_B], [AL_C, AL_L], 18)
    sw.row(["获奖者", " · ".join(nb.get("laureates", []))], [None, None], [F_B, F_B], [AL_C, AL_L], 18)
    sw.row(["获奖理由", nb.get("motivation_en", "")], [None, None], [F_B, F_B], [AL_C, AL_L], 18)
    sw.row(["来源", nb.get("source", "")], [None, None], [F_B, F_B], [AL_C, AL_L], 18)
    sw.row(["【技术原理】", ""], [None, None], [F_H, F_B], [AL_L, AL_L], 18)
    for t in op.get("tech", []):
        sw.row([t["k"], t["v"]], [None, None], [F_B, F_B], [AL_C, AL_L], 18)
    sw.row(["【与中医对照】", ""], [None, None], [F_H, F_B], [AL_L, AL_L], 18)
    for t in op.get("tcm_contrast", []):
        sw.row([t["item"], "光遗传：%s ｜ 中医：%s ｜ %s" % (t["opto"], t["tcm"], t["note"])], [None, None], [F_B, F_B], [AL_C, AL_L], 18)
    sw.row(["【边界声明】", ""], [None, None], [F_H, F_B], [AL_L, AL_L], 18)
    for b in op.get("boundary", []):
        sw.row(["⚠", b], [None, None], [F_B, F_B], [AL_C, AL_L], 18)

    rf = cat.get("ref_impl", {})
    sw = SW_("参考实现", [26, 78]); sw.title("参考实现：%s（★%s）" % (rf.get("repo"), rf.get("stars")), 2)
    sw.row(["项", "内容"], [None, None], [F_H, F_H], [AL_C, AL_L], 20)
    sw.row(["说明", rf.get("desc", "")], [None, None], [F_B, F_B], [AL_C, AL_L], 18)
    sw.row(["管线", rf.get("pipeline", "")], [None, None], [F_B, F_B], [AL_C, AL_L], 18)
    sw.row(["粒度", json.dumps(rf.get("granularity", {}), ensure_ascii=False)], [None, None], [F_B, F_B], [AL_C, AL_L], 30)
    sw.row(["依赖", " · ".join(rf.get("deps", []))], [None, None], [F_B, F_B], [AL_C, AL_L], 18)
    cv = sen.get("conversions", {})
    sw.row(["复刻换算常量（本平台）", json.dumps(cv, ensure_ascii=False)], [None, None], [F_B, F_B], [AL_C, AL_L], 30)
    sw.row(["备注", rf.get("note", "")], [None, None], [F_B, F_B], [AL_C, AL_L], 18)

def add_itcm_sheet(wb, cat, used):
    """智能中医学对接页（对标《智能中医学概论》田贵华、商洪才 2021）。"""
    it = cat.get("intelligent_tcm", {})
    if not it:
        return
    sw = SW(wb.create_sheet(sanitize("智能中医学", used)), [26, 78])
    bk = it.get("book", {})
    sw.title("智能中医学对接 · 《%s》（%s · %s · ISBN %s）" % (bk.get("title"), bk.get("publisher"), bk.get("date"), bk.get("isbn")), 2)
    sw.row(["项", "内容"], [None, None], [F_H, F_H], [AL_C, AL_L], 20)
    sw.row(["作者", " · ".join(bk.get("authors", []))], [None, None], [F_B, F_B], [AL_C, AL_L], 18)
    sw.row(["学科定义", it.get("concept", "")], [None, None], [F_B, F_B], [AL_C, AL_L], 30)
    sw.row(["实现路径", it.get("path", "")], [None, None], [F_B, F_B], [AL_C, AL_L], 30)
    sw.row(["发展理念", it.get("motto", "")], [None, None], [F_B, F_B], [AL_C, AL_L], 18)
    sw.row(["辨证框架", it.get("framework", "")], [None, None], [F_B, F_B], [AL_C, AL_L], 18)
    sw.row(["方法学", it.get("method", "")], [None, None], [F_B, F_B], [AL_C, AL_L], 30)
    sw.row(["典型应用", it.get("case", "")], [None, None], [F_B, F_B], [AL_C, AL_L], 18)
    sw.row(["数据来源", bk.get("source", "")], [None, None], [F_B, F_B], [AL_C, AL_L], 18)
    sw.row(["【作者简介】", ""], [None, None], [F_H, F_B], [AL_L, AL_L], 18)
    for a in it.get("authors", []):
        sw.row([a["name"], "%s ｜ %s ｜ %s" % (a["role"], a["work"], a["honor"])], [None, None], [F_B, F_B], [AL_C, AL_L], 34)
    sw.row(["【全书目录（实测）】", ""], [None, None], [F_H, F_B], [AL_L, AL_L], 18)
    for t in it.get("toc", []):
        sw.row([t["ch"], " / ".join(t["secs"]) if t["secs"] else "—"], [None, None], [F_B, F_B], [AL_L, AL_L], 26)
    sw.row(["【与本课程对接点】", ""], [None, None], [F_H, F_B], [AL_L, AL_L], 18)
    sw.row(["原书位置", "本课程章节 ｜ 说明"], [None, None], [F_H, F_H], [AL_C, AL_L], 20)
    for b in it.get("bridge", []):
        sw.row([b["book"], "%s ｜ %s" % (b["here"], b["note"])], [None, None], [F_B, F_B], [AL_L, AL_L], 26)

def add_wise_tcm_sheet(wb, cat, used):
    """智慧中医学对接页 + 综合实训设备清单（对标《智慧中医学》高教社 2026）。"""
    wt = cat.get("wise_tcm", {})
    if not wt:
        return
    bk = wt.get("book", {})
    sw = SW(wb.create_sheet(sanitize("智慧中医学", used)), [26, 78])
    sw.title("智慧中医学对接 · 《%s》（%s · %s · ISBN %s）" % (bk.get("title"), bk.get("publisher"), bk.get("date"), bk.get("isbn")), 2)
    sw.row(["项", "内容"], [None, None], [F_H, F_H], [AL_C, AL_L], 20)
    sw.row(["系列 / 结构", "%s ｜ %s" % (bk.get("series"), bk.get("structure"))], [None, None], [F_B, F_B], [AL_C, AL_L], 30)
    sw.row(["适用对象", bk.get("audience", "")], [None, None], [F_B, F_B], [AL_C, AL_L], 30)
    sw.row(["数字资源", bk.get("digital", "")], [None, None], [F_B, F_B], [AL_C, AL_L], 18)
    sw.row(["数据来源", bk.get("source", "")], [None, None], [F_B, F_B], [AL_C, AL_L], 18)
    sw.row(["AI 三要素", " · ".join(wt.get("ai3", []))], [None, None], [F_B, F_B], [AL_C, AL_L], 18)
    sw.row(["技术清单", " · ".join(wt.get("tech", []))], [None, None], [F_B, F_B], [AL_C, AL_L], 18)
    sw.row(["生成式 AI", " · ".join(wt.get("genai", []))], [None, None], [F_B, F_B], [AL_C, AL_L], 18)
    sw.row(["【三篇七章目录（实测）】", ""], [None, None], [F_H, F_B], [AL_L, AL_L], 18)
    for p in wt.get("toc", []):
        sw.row([p["part"], ""], [None, None], [F_H, F_B], [AL_L, AL_L], 18)
        for c in p["chapters"]:
            sw.row([c["ch"], " / ".join(c["secs"])], [None, None], [F_B, F_B], [AL_L, AL_L], 30)
    sw.row(["【伦理要求】", ""], [None, None], [F_H, F_B], [AL_L, AL_L], 18)
    for e in wt.get("ethics", []):
        sw.row(["⚠", e], [None, None], [F_B, F_B], [AL_C, AL_L], 18)
    sw.row(["【基本条件】", ""], [None, None], [F_H, F_B], [AL_L, AL_L], 18)
    for e in wt.get("basic_conditions", []):
        sw.row(["·", e], [None, None], [F_B, F_B], [AL_C, AL_L], 18)
    sw.row(["【发展趋势六条】", ""], [None, None], [F_H, F_B], [AL_L, AL_L], 18)
    for i, t in enumerate(wt.get("trends", []), 1):
        sw.row([str(i), t], [None, None], [F_B, F_B], [AL_C, AL_L], 18)

    sw = SW(wb.create_sheet(sanitize("实训设备", used)), [8, 26, 16, 34, 40])
    sw.title("智慧中医综合实训设备清单（对标《智慧中医学》第六章）", 5)
    sw.row(["#", "设备", "归类", "本课程对应", "说明"], [None] * 5, [F_H] * 5, [AL_C] * 5, 20)
    for i, d in enumerate(wt.get("training_devices", []), 1):
        sw.row([str(i), d["name"], d["cat"], d["here"], d["note"]], [None] * 5, [F_B] * 5, [AL_C, AL_L, AL_C, AL_L, AL_L], 18)
    sw.row(["", "【问题导向改进对象】", "", "", ""], [None] * 5, [F_H] * 5, [AL_C] * 5, 18)
    for d in wt.get("improve", []):
        sw.row(["", d["name"], "改进", d["dir"], d["issue"]], [None] * 5, [F_B] * 5, [AL_C, AL_L, AL_C, AL_L, AL_L], 26)

def add_curriculum_sheet(wb, cat, used):
    """认知地图页：认知四阶 × 语义张量（v2.0 目录重构依据）。"""
    cu = cat.get("curriculum", {})
    if not cu:
        return
    sw = SW(wb.create_sheet(sanitize("认知地图", used)), [10, 14, 12, 12, 34, 20])
    sw.title("认知四阶 × 中医药领域语义张量（D07-S11 v2.0 目录重构）", 6)
    sw.row(["阶", "名称", "对应", "动词", "产出", "本课程篇"], [None] * 6, [F_H] * 6, [AL_C] * 6, 20)
    for l in cu.get("ladder", []):
        sw.row([l["id"], l["name"], l["tcm"], l["verb"], l["outcome"], "%s（%s）" % (l["part"], l["chapters"])],
               [None] * 6, [F_B] * 6, [AL_C, AL_C, AL_C, AL_C, AL_L, AL_L], 18)
    sw.row(["【语义张量三轴】", "", "", "", "", ""], [None] * 6, [F_H] * 6, [AL_L] * 6, 18)
    sw.row(["轴", "名称", "端点", "", "本课程落点", ""], [None] * 6, [F_H] * 6, [AL_C, AL_C, AL_C, AL_C, AL_L, AL_C], 20)
    for a in cu.get("axes", []):
        sw.row([a["axis"], a["name"], " / ".join(a["ends"]), "", a["here"], ""],
               [None] * 6, [F_B] * 6, [AL_C, AL_C, AL_C, AL_C, AL_L, AL_C], 18)
    sw.row(["【四阶 × 三轴 矩阵】", "", "", "", "", ""], [None] * 6, [F_H] * 6, [AL_L] * 6, 18)
    mx = {}
    for m in cu.get("matrix", []):
        mx[(m["level"], m["axis"])] = m["cell"]
    sw.row(["阶 \\ 轴", "X 阴阳", "Y 表里", "Z 精气神", "", ""], [None] * 6, [F_H] * 6, [AL_C] * 6, 30)
    for l in cu.get("ladder", []):
        sw.row([l["id"] + " " + l["name"], mx.get((l["id"], "X"), ""), mx.get((l["id"], "Y"), ""),
                mx.get((l["id"], "Z"), ""), "", ""], [None] * 6, [F_B] * 6, [AL_C, AL_L, AL_L, AL_L, AL_C, AL_C], 30)
    sw.row(["【四元 → 张量】", "", "", "", "", ""], [None] * 6, [F_H] * 6, [AL_L] * 6, 18)
    for k, v in (cu.get("quanta_to_tensor") or {}).items():
        sw.row([k, v["semantic"] + "（" + v["axis"] + "）", "", "", v["reason"], ""],
               [None] * 6, [F_B] * 6, [AL_C, AL_L, AL_C, AL_C, AL_L, AL_C], 18)
    dd = cu.get("discipline", {})
    sw.row(["【学科定位】", "", "", "", "", ""], [None] * 6, [F_H] * 6, [AL_L] * 6, 18)
    sw.row(["课程", dd.get("code"), "", "", dd.get("role"), ""], [None] * 6, [F_B] * 6, [AL_C, AL_C, AL_C, AL_C, AL_L, AL_C], 30)
    for d in dd.get("domains", []):
        sw.row([d["prefix"], d["domain"], str(d["count"]) + " 门", "", "", ""],
               [None] * 6, [F_B] * 6, [AL_C, AL_C, AL_C, AL_C, AL_C, AL_C], 16)
    an = dd.get("domain_anchor") or {}
    if an:
        sw.row(["D07 锚点", "x=%.2f y=%.2f z=%.2f" % (an["anchor"]["x"], an["anchor"]["y"], an["anchor"]["z"]),
                "r=%.2f" % an["r"], "θ=%.1f°" % an["theta"], "Z 轴「神」极 · 色 " + an["color"], ""],
               [None] * 6, [F_B] * 6, [AL_C, AL_C, AL_C, AL_C, AL_L, AL_C], 20)

def main():
    cat = json.loads(CAT.read_text(encoding="utf-8"))
    wb = Workbook(); wb.remove(wb.active); used = set()
    meta = dict(title="中医智能仪器与可穿戴设备", subtitle="TCM Smart Instruments & Wearables",
                author="六者·中医医院AI网络教育平台 · tcmP",
                note="D07-S11 教材素材 · 与 kg/device 单一构建点同步")
    write_book(wb, BOOK, meta, used)
    add_data_sheets(wb, cat, used)
    add_ext_sheets(wb, cat, used)
    add_itcm_sheet(wb, cat, used)
    add_wise_tcm_sheet(wb, cat, used)
    add_curriculum_sheet(wb, cat, used)
    add_embed_sheet(wb, used)
    wb.save(OUT)
    print("[产出] " + str(OUT))
    print("[sheet] %d 个：%s" % (len(wb.sheetnames), ", ".join(wb.sheetnames)))


if __name__ == "__main__":
    main()