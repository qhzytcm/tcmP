#!/bin/bash
IMG=docker.m.daocloud.io/library/python:3.11-slim
echo "=== pull $IMG ==="
timeout 300 docker pull $IMG 2>&1 | tail -8
echo "=== images ==="
docker images | head -12
echo "=== disk ==="
df -h / | tail -1
echo "=== DONE ==="