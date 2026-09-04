# -*- coding: utf-8 -*-
# _peek_root.py - find root / apiBase values in net_lib.js
import re
src = open(r"D:\scan\netlify_report\_js\net_lib.js", encoding="utf-8", errors="replace").read()
for pat in ("this.root", "root=", "apiBase", "root:", "api_root", "API_ROOT", "apiRoot"):
    idx = 0
    cnt = 0
    while True:
        i = src.find(pat, idx)
        if i < 0 or cnt > 4:
            break
        print("###", pat, "@", i)
        print(src[max(0, i-250):i+350])
        print("----")
        idx = i + len(pat)
        cnt += 1
