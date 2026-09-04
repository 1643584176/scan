# -*- coding: utf-8 -*-
# _peek_analytics.py - find analytics api client class & methods in net_lib.js
import re

src = open(r"D:/scan/netlify_report/_js/net_lib.js", encoding="utf-8", errors="replace").read()

# find analyticsClientApiBase usages
for m in list(re.finditer(r"analytics", src))[:40]:
    s = max(0, m.start() - 300)
    e = min(len(src), m.end() + 300)
    seg = src[s:e]
    if "request" in seg or "fetch" in seg or "ApiBase" in seg or "api/" in seg:
        print(repr(seg))
        print("---")
