# -*- coding: utf-8 -*-
# _peek_edgeaccess2.py - find API endpoint that returns edge_access token
import os, re
src = open(r"D:\scan\netlify_report\_js\net_app.js", encoding="utf-8", errors="replace").read()
# find all occurrences of edge_access, print bigger context to locate request path
for m in re.finditer(r'edge_access', src):
    i = m.start()
    print("### @", i)
    print(src[max(0, i-2500):i+200])
    print("----")
