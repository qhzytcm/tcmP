#!/bin/bash
# tcmP Sage API v2.2 部署：ICD-11 编码桥接上线（main.py + icd11_client + db）
set -e
BASE=/var/www/tcm-dashboard
cd $BASE

echo "═══ 1. 注入 DeepSeek Key（从 .bak.20260801 提取）═══"
python3 << 'PYEOF'
import re
p = "sage-api/main.py"
s = open(p, encoding="utf-8").read()
old = open("sage-api/main.py.bak.20260801", encoding="utf-8").read()
m = re.search(r'or "([^"]+)"', old)
k = m.group(1) if m else ""
s2 = re.sub(r'(or ")[^"]*(")', lambda mm: mm.group(1) + k + mm.group(2), s)
assert s2 != s, "key 注入失败"
open(p, "w", encoding="utf-8").write(s2)
print("key注入:", len(k), "字符")
PYEOF

echo "═══ 2. 编译检查 ═══"
python3 -m py_compile sage-api/main.py && echo COMPILE_OK
python3 -m py_compile scripts/icd11_client.py && echo CLIENT_OK

echo "═══ 3. db 完整性 ═══"
ls -la data/icd11_mms.db

echo "═══ 4. 重启 API ═══"
PID=$(ss -tlnp | grep 8300 | grep -oP 'pid=\K[0-9]+' | head -1)
[ -n "$PID" ] && kill -9 $PID && echo "killed $PID"
sleep 1
cd sage-api
nohup /root/.local/share/uv/tools/hermes-agent/bin/python3 main.py > api.log 2>&1 &
sleep 6
echo "--- 8300 监听 ---"
ss -tlnp | grep 8300
echo "--- 启动日志关键行 ---"
grep -E "ICD-11|人格加载|LLM|Uvicorn" api.log | head -12
echo "--- health ---"
curl -s http://127.0.0.1:8300/health
