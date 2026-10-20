#!/bin/bash
echo "=== hermes version ==="
hermes --version 2>&1 | head -2
echo "=== memory status (BEFORE) ==="
hermes memory status 2>&1 | head -30
echo "=== gateway status ==="
hermes gateway status 2>&1 | head -12
echo "=== openviking plugin dir ==="
find /root/.local/share/uv/tools/hermes-agent -maxdepth 8 -type d -name openviking 2>/dev/null | head -5
echo "=== DONE ==="