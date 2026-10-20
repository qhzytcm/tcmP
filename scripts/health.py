import sys, urllib.request
try:
    d = urllib.request.urlopen("http://127.0.0.1:1933/health", timeout=4).read()
    sys.exit(0 if b'"healthy":true' in d else 1)
except Exception:
    sys.exit(1)