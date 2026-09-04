# -*- coding: utf-8 -*-
# _org_bundle2.py - find how UI fetches organizations (data layer)
import re, os

D = r"D:/scan/netlify_report/_js"
src = open(os.path.join(D, "net_app.js"), encoding="utf-8", errors="replace").read()

# contexts of "organizations" that involve fetch/url/api words within +/-400 chars
for m in re.finditer(r"organizations", src):
    i = m.start()
    ctx = src[max(0, i - 350): i + 350]
    if re.search(r"fetch|\.json\(|bb-api|access-control|url:", ctx):
        print("-" * 60)
        print(ctx.replace("\n", " ")[:600])
