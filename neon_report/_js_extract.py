# -*- coding: utf-8 -*-
"""Extract API paths from console prod JS: focus on NON-v2 internal endpoints."""
import os
import re
import json

JS_DIR = r"F:\scan\neon_report\_js"
OUT = {}

path_re = re.compile(r'["\'`](/api/[A-Za-z0-9_\-/{}.:%?=&]+)["\'`]')
full_re = re.compile(r'["\'`](https?://[^"\']*?/api/[^"\']*)["\'`]')
fetch_re = re.compile(r'fetch\(\s*["\'`]([^"\'`]{3,120})["\'`]')

non_v2 = {}
v2 = {}
fetch_urls = []

for root, _, files in os.walk(JS_DIR):
    for fn in files:
        if not fn.endswith(".js"):
            continue
        fp = os.path.join(root, fn)
        try:
            data = open(fp, encoding="utf-8", errors="replace").read()
        except Exception:
            continue
        for m in path_re.finditer(data):
            p = m.group(1)
            if "/api/v2/" in p:
                v2[p] = v2.get(p, 0) + 1
            else:
                non_v2[p] = non_v2.get(p, 0) + 1
        for m in full_re.finditer(data):
            u = m.group(1)
            if "/api/v2/" not in u:
                non_v2[u] = non_v2.get(u, 0) + 1
        for m in fetch_re.finditer(data):
            fetch_urls.append((fn, m.group(1)))

print("==== NON-v2 API paths (%d) ====" % len(non_v2))
for p in sorted(non_v2, key=lambda x: -non_v2[x]):
    print("%5d  %s" % (non_v2[p], p[:220]))

print("\n==== fetch() dynamic URLs (%d, sample 60) ====" % len(fetch_urls))
seen = set()
for fn, u in fetch_urls:
    if u.startswith("http") or u.startswith("/"):
        k = (fn, u)
        if k in seen:
            continue
        seen.add(k)
        print("  [%s] %s" % (fn[:40], u[:180]))
    if len(seen) > 60:
        break
