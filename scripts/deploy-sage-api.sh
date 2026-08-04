#!/bin/bash
# tcmP Sage API v2.1 部署：六者SOUL人格加载上线
set -e
cd /var/www/tcm-dashboard/sage-api
cp main.py main.py.bak.20260801
python3 << 'PYEOF'
import re
p = "main.py"
s = open(p, encoding="utf-8").read()
old = open(p + ".bak.20260801", encoding="utf-8").read()
m = re.search(r'os.environ.get\("DEEPSEEK_API_KEY", ""\) or "([^"]*)"', old)
if not m:
    print("!! 旧文件未找到硬编码Key，跳过注入（使用环境变量）")
else:
    k = m.group(1)
    s2 = re.sub(r'(os.environ.get\("DEEPSEEK_API_KEY", ""\) or ")[^"]*(")',
                lambda mm: mm.group(1) + k + mm.group(2), s)
    open(p, "w", encoding="utf-8").write(s2)
    print("key注入:", len(k), "字符")
PYEOF
python3 -m py_compile main.py && echo "COMPILE_OK"
