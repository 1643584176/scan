# -*- coding: utf-8 -*-
# _peek_edgeaccess.py - how UI obtains dev server access (edge-access flow)
import os, re
src = open(r"D:\scan\netlify_report\_js\net_app.js", encoding="utf-8", errors="replace").read()
for pat in ("edge-access", "edge_access", "devserver-ar", "devServerToken", "dev_server_token", "ds_token", "preview_session"):
    idx = 0
    cnt = 0
    while True:
        i = src.find(pat, idx)
        if i < 0 or cnt > 3:
            break
        print("###", pat, "@", i)
        print(src[max(0, i-400):i+600])
        print("----")
        idx = i + len(pat)
        cnt += 1
