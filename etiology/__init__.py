# -*- coding: utf-8 -*-
"""
etiology —— 三因辨证引擎（tcmP 病因辨证模块）
================================================
依据桌面「醒了么(张仲景)」四文件（framework_spec 契约）实现的
中医病因辨证程序模块，覆盖三大门类：

  ├── nei   (data/nei_yin.json)    内因辨证   —— 七情：怒喜悲思恐忧惊
  ├── wai   (data/wai_yin.json)    外因辨证   —— 六淫：风寒暑湿燥热
  └── bunei (data/bu_nei_wai.json) 不内外因辨证 —— 7板块：饮食/劳逸/外伤/
                                             虫兽/中毒/医过/先天（68细目）

统一符号体系（etiology.framework）：
  5区间强度 L1-L5（0-0.2-0.4-0.6-0.8-1.0）、五阶段（p1损→p5败 /
  S1感→S5损 / 七情五段）、四层拓扑（因→脏腑→经络→穴位）、
  脏腑符号 H肝 X心 P肺 S脾 R肾 + 六腑、12正经+任督 14经脉。

快速开始：
    from etiology.engine import EtiologyEngine
    eng = EtiologyEngine()
    r = eng.dialect('恶寒发热无汗，身痛，脉浮紧，受凉两天')
    print(eng.report(r))
    r2 = eng.dialect(['急躁易怒', '胁胀'], trigger='生气')   # 结构化入口

集成为 API（FastAPI 示例见 scripts/etiology_api_demo.py）：
    POST /etiology/dialect   {"text": "…"} 或 {"symptoms": [...], "trigger": "…"}
    → 三因分类置信 + 每因辨证卡（病机/治则/方/穴/经脉/经文）
"""
from etiology.engine import EtiologyEngine  # noqa: F401
from etiology import framework  # noqa: F401

__version__ = '0.1.0'
