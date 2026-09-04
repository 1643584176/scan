# -*- coding: utf-8 -*-
# _peek_connect.py - dump /connect/data-layers/ and blobs usage context
import re, os

for fn in os.listdir(r"D:/scan/netlify_report/_js"):
    if not fn.endswith(".js"):
        continue
    p = os.path.join(r"D:/scan/netlify_report/_js", fn)
    src = open(p, encoding="utf-8", errors="replace").read()
    for pat in ("connect/data-layers", "/blobs/", "agent_runners", "analytics-api"):
        hits = list(re.finditer(re.escape(pat), src))
        if not hits:
            continue
        print("### FILE:", fn, "PAT:", pat, "hits:", len(hits))
        for m in hits[:6]:
            s = max(0, m.start() - 250)
            e = min(len(src), m.end() + 250)
            print(repr(src[s:e]))
            print("---")
