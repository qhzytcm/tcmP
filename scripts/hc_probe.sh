#!/bin/bash
echo "=== NET ==="
for u in https://pypi.tuna.tsinghua.edu.cn/simple/ https://pypi.org/simple/ https://hf-mirror.com/ https://github.com/ https://gh-proxy.com/ https://mirrors.aliyun.com/; do
  code=$(curl -s -o /dev/null -w '%{http_code}' -m 15 "$u")
  echo "$u -> $code"
done
echo "=== DISK ==="
df -h | head -20
echo "=== PY ==="
python3 -c "import sys; print(sys.version)"
python3 -m pip --version
echo "=== HERMES ==="
hermes --version 2>&1 | head -2
hermes config path 2>&1 | head -2
echo "=== ~/.hermes ==="
ls /root/.hermes 2>/dev/null | head -20
echo "=== GLIBC ==="
ldd --version | head -1
echo "=== DONE ==="