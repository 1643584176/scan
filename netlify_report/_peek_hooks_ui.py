# -*- coding: utf-8 -*-
# _peek_hooks_ui.py - find agent_runner_hooks usage context in net_app.js
import os, re
src = open(r"D:\scan\netlify_report\_js\net_app.js", encoding="utf-8", errors="replace").read()
idx = 0
cnt = 0
while True:
    i = src.find("agent_runner_hooks", idx)
    if i < 0 or cnt > 8:
        break
    print("### hit at", i)
    print(src[max(0, i-700):i+500])
    print()
    idx = i + 20
    cnt += 1
