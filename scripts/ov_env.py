# -*- coding: utf-8 -*-
import io, os
p = os.path.join(os.path.expanduser("~"), "AppData", "Local", "hermes", ".env")
keys = [("OPENVIKING_ENDPOINT", "http://127.0.0.1:1933"),
        ("OPENVIKING_ACCOUNT", "default"),
        ("OPENVIKING_USER", "default"),
        ("OPENVIKING_AGENT", "hermes")]
txt = ""
if os.path.exists(p):
    txt = io.open(p, "r", encoding="utf-8-sig").read()
existing = set(l.split("=", 1)[0].strip() for l in txt.splitlines() if "=" in l)
add = ["%s=%s" % (k, v) for k, v in keys if k not in existing]
if add:
    with io.open(p, "a", encoding="utf-8") as f:
        f.write(("\n" if txt and not txt.endswith("\n") else "") + "\n".join(add) + "\n")
print("env_path=%s added=%s" % (p, add))