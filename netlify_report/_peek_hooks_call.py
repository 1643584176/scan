# -*- coding: utf-8 -*-
# _peek_hooks_call.py - find addAgentRunnerHook/addDevServerHook caller context in net_app.js
import os, re
src = open(r"D:\scan\netlify_report\_js\net_app.js", encoding="utf-8", errors="replace").read()
for pat in ("addAgentRunnerHook", "agentRunnerHooks(", "addDevServerHook", "siteDevServerHooks(", "removeAgentRunnerHook"):
    idx = 0
    cnt = 0
    while True:
        i = src.find(pat, idx)
        if i < 0 or cnt > 4:
            break
        seg = src[max(0, i-350):i+350]
        # caller context (not the lib definition inside net_containers/net_lib dupe)
        if "value:function" not in seg[max(0, i-350):i]:
            print("###", pat, "at", i)
            print(seg)
            print("----")
        idx = i + len(pat)
        cnt += 1
