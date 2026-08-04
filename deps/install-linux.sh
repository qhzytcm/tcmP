#!/bin/bash
# ============================================================
# tcmP API 依赖离线安装脚本（华为云 CentOS 7 / anaconda3）
# 用法：把 deps/ 目录整体传到服务器后执行：
#   bash deps/install-linux.sh
# ============================================================
set -e

PY=/www/anaconda3/bin/python3
PIP=/www/anaconda3/bin/pip
DIR="$(cd "$(dirname "$0")" && pwd)"

echo "═══ tcmP 依赖离线安装 ═══"
echo "Python: $($PY --version 2>&1)"
echo "Wheel 目录: $DIR/wheels-linux"

$PIP install --no-index --find-links "$DIR/wheels-linux" \
    fastapi==0.95.1 uvicorn==0.21.1 pydantic==1.10.7 starlette==0.26.1

echo ""
echo "═══ 安装完成，验证 ═══"
$PIP show fastapi uvicorn pydantic starlette | grep -E "^(Name|Version)"
