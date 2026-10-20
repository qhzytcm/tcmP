#!/bin/bash
set -o pipefail
IMG=docker.m.daocloud.io/library/python:3.11-slim
NAME=openviking
VENV=/www/ov-venv
docker rm -f $NAME 2>/dev/null
docker run -d --name $NAME --network host --security-opt seccomp=unconfined --restart unless-stopped \
  -v /www:/www \
  -v /root/.openviking:/root/.openviking \
  -v /root/.cache/openviking:/root/.cache/openviking \
  -v /www/openviking-data:/data \
  $IMG $VENV/bin/openviking-server --host 127.0.0.1 --port 1933
echo "=== wait health ==="
for i in $(seq 1 40); do
  sleep 3
  if curl -s -m 3 http://127.0.0.1:1933/health | grep -q healthy; then echo "HEALTH_OK attempts=$i"; break; fi
done
curl -s -m 5 http://127.0.0.1:1933/health; echo
echo "=== restart policy ==="
docker inspect --format '{{.HostConfig.RestartPolicy.Name}}' $NAME
echo "=== cli still works ==="
/usr/local/bin/openviking health 2>&1 | head -6
echo "=== cleanup failed native venv ==="
rm -rf /www/openviking-venv && echo removed
df -h / /www | tail -2
echo "=== DONE ==="