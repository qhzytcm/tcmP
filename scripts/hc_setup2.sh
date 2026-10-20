#!/bin/bash
set -o pipefail
NAME=openviking
VENV=/www/ov-venv
echo "=== ov.conf ==="
cat /root/.openviking/ov.conf
echo "=== language ==="
docker exec $NAME $VENV/bin/openviking language zh-CN 2>&1 | tail -2
echo "=== start server ==="
docker exec -d $NAME bash -lc "$VENV/bin/openviking-server --host 127.0.0.1 --port 1933 > /tmp/ov_server.log 2>&1"
for i in $(seq 1 40); do
  sleep 3
  if curl -s -m 3 http://127.0.0.1:1933/health | grep -q healthy; then echo "HEALTH_OK attempts=$i"; break; fi
done
echo -n "health: "; curl -s -m 5 http://127.0.0.1:1933/health; echo
echo "=== custom connection ==="
docker exec $NAME $VENV/bin/openviking config add custom --name huaweicloud-local --url http://127.0.0.1:1933 --activate 2>&1 | tail -5
docker exec $NAME $VENV/bin/openviking config list 2>&1 | tail -5
echo "=== host wrapper ==="
cat > /usr/local/bin/openviking <<'EOF'
#!/bin/bash
exec docker exec -i openviking /www/ov-venv/bin/openviking "$@"
EOF
chmod +x /usr/local/bin/openviking
/usr/local/bin/openviking health 2>&1 | head -12
echo "=== harness venv ==="
/root/.hermes/bin/uv venv /www/ov-harness-venv --python 3.11 2>&1 | tail -2
/root/.hermes/bin/uv pip install --python /www/ov-harness-venv/bin/python openpyxl 2>&1 | tail -3
/www/ov-harness-venv/bin/python -c "import openpyxl; print('openpyxl', openpyxl.__version__)"
echo "=== DONE ==="