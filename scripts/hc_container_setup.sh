#!/bin/bash
set -o pipefail
IMG=docker.m.daocloud.io/library/python:3.11-slim
NAME=openviking
docker rm -f $NAME 2>/dev/null
mkdir -p /root/.openviking /root/.cache/openviking /www/openviking-data
docker run -d --name $NAME --network host \
  -v /www:/www \
  -v /root/.openviking:/root/.openviking \
  -v /root/.cache/openviking:/root/.cache/openviking \
  -v /www/openviking-data:/data \
  $IMG sleep infinity
echo "=== container ==="; docker ps | grep openviking
echo "=== venv (on /www) ==="
docker exec $NAME bash -lc 'python -m venv /www/ov-venv && /www/ov-venv/bin/python --version'
echo "=== pip config ==="
docker exec $NAME bash -lc '/www/ov-venv/bin/pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple && /www/ov-venv/bin/pip config list'
echo "=== install openviking ==="
docker exec $NAME bash -lc '/www/ov-venv/bin/pip install --no-cache-dir -q openviking openpyxl 2>&1 | tail -25; echo "PIP_EXIT=$?"'
echo "=== install llama wheel ==="
docker exec $NAME bash -lc '/www/ov-venv/bin/pip install --no-cache-dir -q /www/llama_cpp_python-0.3.36-py3-none-manylinux2014_x86_64.whl 2>&1 | tail -15; echo "WHEEL_EXIT=$?"'
echo "=== verify imports ==="
docker exec $NAME bash -lc '/www/ov-venv/bin/python -c "import openviking, openpyxl, llama_cpp; print(\"imports OK\")"'
echo "=== version ==="
docker exec $NAME bash -lc '/www/ov-venv/bin/openviking --version 2>&1 | head -3'
echo "=== DONE ==="