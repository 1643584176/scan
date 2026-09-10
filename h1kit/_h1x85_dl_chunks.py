# -*- coding: utf-8 -*-
"""全量下载 chunk 建立本地源码树(2026-09-09)"""
import os
import re
import time
import urllib.request

SRC = r"D:\scan\h1kit\_h1x4_app.js"
DST = r"D:\scan\h1kit\_src_chunks"
os.makedirs(DST, exist_ok=True)

with open(SRC, "r", encoding="utf-8", errors="replace") as f:
    data = f.read()

chunks = sorted(set(m.group(1) for m in re.finditer(r"static/([a-z_0-9]+-[A-Za-z0-9_-]+\.js)", data)))
print("total chunks:", len(chunks))

ok = fail = skip = 0
for i, c in enumerate(chunks):
    out_path = os.path.join(DST, c)
    if os.path.exists(out_path) and os.path.getsize(out_path) > 100:
        skip += 1
        continue
    url = "https://hackerone.com/assets/static/" + c
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            body = r.read()
        with open(out_path, "wb") as f:
            f.write(body)
        ok += 1
    except Exception as e:
        fail += 1
        print("FAIL", c, e)
    if (i + 1) % 30 == 0:
        print(f"progress {i+1}/{len(chunks)} ok={ok} fail={fail}")
    time.sleep(0.15)

print(f"DONE ok={ok} fail={fail} skip={skip}")
