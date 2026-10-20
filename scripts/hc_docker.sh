#!/bin/bash
echo "=== docker version ==="
docker version 2>&1 | head -14
echo "=== images ==="
docker images 2>&1 | head -15
echo "=== daemon.json ==="
cat /etc/docker/daemon.json 2>/dev/null || echo "(none)"
echo "=== ps ==="
docker ps 2>&1 | head -8
echo "=== pull test (60s) ==="
timeout 60 docker pull python:3.11-slim 2>&1 | tail -6
echo "=== DONE ==="