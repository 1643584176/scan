# -*- coding: utf-8 -*-
# _peek_bbh.py - dump bitbucket-self-hosted client class definition from net_lib.js
import re

src = open(r"D:/scan/netlify_report/_js/net_lib.js", encoding="utf-8", errors="replace").read()

# find all occurrences of bitbucket-self-hosted and dump big context
for m in list(re.finditer(r"bitbucket-self-hosted", src))[:4]:
    s = max(0, m.start() - 4000)
    e = min(len(src), m.end() + 2500)
    print("=== context around hit at %d ===" % m.start())
    print(src[s:e])
    print()
