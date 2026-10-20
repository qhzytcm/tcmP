#!/bin/bash
set -o pipefail
TS=$(date +%Y%m%d_%H%M%S)
H=/root/.hermes
cp -a $H/config.yaml $H/config.yaml.bak.$TS 2>/dev/null
cp -a $H/.env $H/.env.bak.$TS 2>/dev/null
echo "=== backups ==="; ls -l $H/*.bak.$TS 2>/dev/null | awk '{print $NF, $5}'
echo "=== config set ==="
hermes config set memory.provider openviking 2>&1 | tail -2
hermes config set memory.openviking.endpoint http://127.0.0.1:1933 2>&1 | tail -2
hermes config set memory.openviking.agent hermes 2>&1 | tail -2
echo "=== env (idempotent) ==="
python3 - <<'PY'
import io, os
p = "/root/.hermes/.env"
keys = [("OPENVIKING_ENDPOINT","http://127.0.0.1:1933"),
        ("OPENVIKING_ACCOUNT","default"),
        ("OPENVIKING_USER","default"),
        ("OPENVIKING_AGENT","hermes")]
txt = io.open(p, encoding="utf-8-sig").read() if os.path.exists(p) else ""
have = set(l.split("=",1)[0].strip() for l in txt.splitlines() if "=" in l)
add = ["%s=%s" % (k,v) for k,v in keys if k not in have]
if add:
    with io.open(p,"a",encoding="utf-8") as f:
        f.write(("\n" if txt and not txt.endswith("\n") else "") + "\n".join(add) + "\n")
print("added:", add)
PY
echo "=== memory status (AFTER) ==="
hermes memory status 2>&1 | head -18
echo "=== server health ==="
curl -s -m 5 http://127.0.0.1:1933/health; echo
echo "=== DONE ==="