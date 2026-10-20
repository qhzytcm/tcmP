#!/bin/bash
export OV_EXE=/usr/local/bin/openviking
export OPENVIKING_ENDPOINT=http://127.0.0.1:1933
export OPENVIKING_ACCOUNT=default
export OPENVIKING_USER=default
export OPENVIKING_AGENT=hermes
cd /tmp
/www/ov-harness-venv/bin/python /tmp/ov_custom_connectivity_test.py --out /www/OV-test-huaweicloud.xlsx
echo "EXIT=$?"
ls -l /www/OV-test-huaweicloud.xlsx