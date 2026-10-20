import os, urllib.request
d = r"C:\Users\Administrator\.cache\openviking\models"
os.makedirs(d, exist_ok=True)
dst = os.path.join(d, "bge-small-zh-v1.5-f16.gguf")
url = "https://hf-mirror.com/CompendiumLabs/bge-small-zh-v1.5-gguf/resolve/main/bge-small-zh-v1.5-f16.gguf"
if (not os.path.exists(dst)) or os.path.getsize(dst) < 47000000:
    with urllib.request.urlopen(url, timeout=120) as r, open(dst, "wb") as f:
        while True:
            b = r.read(1 << 20)
            if not b:
                break
            f.write(b)
print("SIZE", os.path.getsize(dst))