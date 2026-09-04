# -*- coding: utf-8 -*-
# _peek_devsrv.py - extract createDevServer + dev server related client methods
import re
src = open(r"D:\scan\netlify_report\_js\net_lib.js", encoding="utf-8", errors="replace").read()
for pat in ("createDevServer", "dev_server_hooks", "devServer", "DevServer"):
    idx = 0
    cnt = 0
    while True:
        i = src.find(pat, idx)
        if i < 0 or cnt > 6:
            break
        print("###", pat, "@", i)
        print(src[max(0, i-200):i+500])
        print()
        idx = i + len(pat)
        cnt += 1
