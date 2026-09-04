# -*- coding: utf-8 -*-
# _peek_identeer.py - dump identeer-proxy usage context from bundles
import re, os

for fn in os.listdir(r"D:/scan/netlify_report/_js"):
    if not fn.endswith(".js"):
        continue
    p = os.path.join(r"D:/scan/netlify_report/_js", fn)
    src = open(p, encoding="utf-8", errors="replace").read()
    hits = list(re.finditer(r"identeer", src))
    if not hits:
        continue
    print("### FILE:", fn, "hits:", len(hits))
    for m in hits[:12]:
        s = max(0, m.start() - 200)
        e = min(len(src), m.end() + 200)
        print(repr(src[s:e]))
        print("---")
