# -*- coding: utf-8 -*-
# _peek_edgeaccess3.py - find edgeAccess client method in net_lib.js
import os, re
src = open(r"D:\scan\netlify_report\_js\net_lib.js", encoding="utf-8", errors="replace").read()
for pat in ("edgeAccess", "edge_access", "edge-access", "EdgeAccess", "/edge"):
    idx = 0
    cnt = 0
    while True:
        i = src.find(pat, idx)
        if i < 0 or cnt > 5:
            break
        seg = src[max(0, i-300):i+400]
        if "request(" in seg or "access" in pat:
            print("###", pat, "@", i)
            print(seg)
            print("----")
        idx = i + len(pat)
        cnt += 1
