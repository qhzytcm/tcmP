# -*- coding: utf-8 -*-
"""
etiology_api_demo.py —— 病因辨证引擎 FastAPI 接入示例
================================================
演示如何将三因辨证引擎挂入 tcmP 平台（与 sage-api 的 /diag /bianzheng
检索端点并列）。运行:

    cd C:\\Users\\DELL\\tcmP
    python -X utf8 scripts\\etiology_api_demo.py          # uvicorn :8411

端点:
    POST /etiology/dialect      # 自由文本辨证
    POST /etiology/dialect/structured  # 结构化症状+诱因
    GET  /etiology/health
    GET  /etiology/framework    # 符号体系说明
"""
from __future__ import annotations

import sys
from pathlib import Path

# 保证 etiology 包可导入（tcmP 根目录）
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pydantic import BaseModel, Field  # noqa: E402
from typing import List, Optional  # noqa: E402

from etiology.engine import EtiologyEngine  # noqa: E402
from etiology import framework  # noqa: E402

try:
    from fastapi import FastAPI, HTTPException
except ImportError:
    print('FastAPI 未安装: pip install fastapi uvicorn')
    sys.exit(1)

app = FastAPI(title='tcmP 三因辨证引擎', version='0.1.0',
              description='内因七情 / 外因六淫 / 不内外因7板块 — 病因辨证（依据醒了么·framework_spec 契约）')
eng = EtiologyEngine()


class DialectIn(BaseModel):
    text: Optional[str] = Field(None, description='自由文本主诉（含症状与诱因）')
    symptoms: Optional[List[str]] = Field(None, description='结构化症状词表')
    trigger: Optional[str] = Field(None, description='诱因/触发事件（生气/受凉/暴食…）')


@app.post('/etiology/dialect')
def dialect(body: DialectIn):
    if not body.text and not body.symptoms:
        raise HTTPException(400, '需提供 text 或 symptoms')
    result = eng.dialect(text=body.text, symptoms=body.symptoms, trigger=body.trigger)
    return {'report': eng.report(result), **result}


@app.get('/etiology/health')
def health():
    return {'status': 'ok', 'engine': 'etiology', 'version': '0.1.0',
            'kb': {k: len(v) for k, v in {
                'nei': eng.kb['nei']['emotions'],
                'wai': eng.kb['wai']['liuyin'],
                'bunei': eng.kb['bunei']['boards']}.items()}}


@app.get('/etiology/framework')
def framework_info():
    return {
        'zang': framework.ZANG,
        'fu': framework.FU,
        'levels': [f'{c} {n} [{lo},{hi})' for c, n, lo, hi in framework.LEVELS],
        'nei_stages': framework.NEI_STAGES,
        'wai_stages': framework.WAI_STAGES,
        'bunei_stages': framework.BUNEI_STAGES,
        'wai_signature': {k: {kk: vv for kk, vv in v.items() if kk in ('code', 'lam', 'alpha', 's')}
                          for k, v in framework.WAI_SIGNATURE.items()},
        'bunei_boards': {k: v['name'] for k, v in framework.BUNEI_BOARDS.items()},
    }


if __name__ == '__main__':
    import uvicorn
    print('启动三因辨证引擎 API: http://127.0.0.1:8411/etiology/health')
    uvicorn.run(app, host='127.0.0.1', port=8411)
