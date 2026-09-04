# -*- coding: utf-8 -*-
# _peek_hooks_all.py - find agent_runner_hooks across all js files with context
import os, re
base = r"D:\scan\netlify_report\_js"
for fn in sorted(os.listdir(base)):
    if not fn.endswith(".js"):
        continue
    p = os.path.join(base, fn)
    try:
        src = open(p, encoding="utf-8", errors="replace").read()
    except Exception:
        continue
    if "agent_runner_hooks" not in src and "agentRunnerHook" not in src:
        continue
    print("### FILE:", fn, "len", len(src))
    idx = 0
    cnt = 0
    while True:
        i = src.find("agent_runner_hook", idx)
        if i < 0 or cnt > 6:
            break
        print(src[max(0, i-500):i+400])
        print("----")
        idx = i + 30
        cnt += 1
