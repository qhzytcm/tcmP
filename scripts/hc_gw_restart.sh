#!/bin/bash
set -o pipefail
BAK=$(ls -1t /root/.hermes/config.yaml.bak.* 2>/dev/null | head -1)
echo "=== backup: $BAK ==="
echo "=== before ==="; systemctl is-active hermes-gateway
echo "=== restart ==="
systemctl restart hermes-gateway
sleep 10
ST=$(systemctl is-active hermes-gateway)
echo "=== after: $ST ==="
if [ "$ST" != "active" ]; then
  echo "!!! FAILED to start, reverting config"
  [ -n "$BAK" ] && cp -a "$BAK" /root/.hermes/config.yaml
  systemctl restart hermes-gateway
  sleep 8
  echo "reverted, active=$(systemctl is-active hermes-gateway)"
else
  systemctl status hermes-gateway --no-pager 2>&1 | head -10
fi
echo "=== logs (last 2 min) ==="
journalctl -u hermes-gateway --since "2 min ago" --no-pager 2>&1 | grep -iE "openviking|memory|error|traceback|Started|listening|gateway" | tail -20
echo "=== DONE ==="