#!/bin/bash
# tcmP Sage API v3.0 部署：病证单元 Embedding 引擎（诊断/辨证/RAG）
set -e
BASE=/var/www/tcm-dashboard
cd $BASE

echo "═══ 1. 注入 DeepSeek Key ═══"
python3 << 'PYEOF'
import re
p = "sage-api/main.py"
s = open(p, encoding="utf-8").read()
KEY = "sk-bdc4ccda903249f5b79fe2e5568eb4ac"
s2 = re.sub(r'(os.environ.get\("DEEPSEEK_API_KEY", ""\) or ")[^"]*(")',
            lambda m: m.group(1) + KEY + m.group(2), s)
if s2 != s:
    open(p, "w", encoding="utf-8").write(s2)
    print("key 已更新:", len(KEY), "字符")
else:
    print("key 已是最新（35字符）")
PYEOF

echo "═══ 2. 编译检查 ═══"
python3 -m py_compile sage-api/main.py && echo MAIN_OK
python3 -m py_compile scripts/tcm_embed.py && echo EMBED_OK

echo "═══ 3. 引擎自检（加载 DSU + FTS5）═══"
python3 -c "
import sys; sys.path.insert(0, 'scripts')
from tcm_embed import TCMSearchEngine
eng = TCMSearchEngine()
print('DSU:', len(eng.docs), '| FTS5:', eng.fts.n)
r = eng.diagnose(['恶寒','发热','无汗'])
print('诊断:', r['results'][0]['disease'], r['results'][0]['icd11_code'])
"

echo "═══ 4. 重启 API ═══"
PID=$(ss -tlnp | grep 8300 | grep -oP 'pid=\K[0-9]+' | head -1)
[ -n "$PID" ] && kill -9 $PID
sleep 1
cd sage-api
nohup /root/.local/share/uv/tools/hermes-agent/bin/python3 main.py > api.log 2>&1 &
sleep 7
ss -tlnp | grep 8300
grep -E "引擎|ICD-11|LLM|Uvicorn" api.log | head -8
curl -s http://127.0.0.1:8300/health
