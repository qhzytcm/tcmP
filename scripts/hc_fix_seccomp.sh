#!/bin/bash
set -o pipefail
IMG=docker.m.daocloud.io/library/python:3.11-slim
NAME=openviking
docker rm -f $NAME 2>/dev/null
docker run -d --name $NAME --network host --security-opt seccomp=unconfined \
  -v /www:/www \
  -v /root/.openviking:/root/.openviking \
  -v /root/.cache/openviking:/root/.cache/openviking \
  -v /www/openviking-data:/data \
  $IMG sleep infinity
echo "=== container ==="; docker ps --filter name=openviking --no-trunc | head -3
echo "=== thread test ==="
docker exec $NAME bash -lc 'python -c "import threading; ts=[threading.Thread(target=lambda:None) for _ in range(8)]; [t.start() for t in ts]; [t.join() for t in ts]; print(\"threads OK\")"'
echo "=== imports ==="
docker exec $NAME bash -lc '/www/ov-venv/bin/python -c "import openviking, openpyxl, numpy, llama_cpp; print(\"imports OK\")" 2>&1 | tail -6'
echo "=== version ==="
docker exec $NAME bash -lc '/www/ov-venv/bin/openviking --version 2>&1 | head -4'
echo "=== DONE ==="