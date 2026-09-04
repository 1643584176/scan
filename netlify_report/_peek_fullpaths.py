# -*- coding: utf-8 -*-
# _peek_fullpaths.py - dump full path strings for selected api groups from net_lib.js
import re

src = open(r"D:/scan/netlify_report/_js/net_lib.js", encoding="utf-8", errors="replace").read()

# find request("/xxx") with enough context, print full literal paths
pat = re.compile(r'this\.request\("([^"]+)"')
seen = set()
for m in pat.finditer(src):
    p = m.group(1)
    if any(s in p for s in ("project", "agent_runner", "blob", "organization", "dev_server", "audit", "drop", "domain")):
        if p not in seen:
            seen.add(p)
            back = src[max(0, m.start() - 1500):m.start()]
            km = list(re.finditer(r'key:"([A-Za-z0-9_]+)"', back))
            kname = km[-1].group(1) if km else "?"
            print("%-38s %s" % (kname, p))
