#!/bin/bash
set -o pipefail
export PATH=/root/.hermes/bin:$PATH
export UV_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
VENV=/www/openviking-venv
echo "=== VENV ==="
uv venv --python 3.11 $VENV 2>&1 | tail -3
$VENV/bin/python --version
echo "=== tiktoken pin (manylinux2014 for glibc2.17) ==="
uv pip install --python $VENV/bin/python "tiktoken==0.8.0" 2>&1 | tail -10
echo "=== openviking ==="
uv pip install --python $VENV/bin/python openviking openpyxl 2>&1 | tail -25
echo "=== EXIT=$? ==="
$VENV/bin/python -c "import openviking, openpyxl; print('import OK')" 2>&1 | tail -5
echo "=== DONE ==="