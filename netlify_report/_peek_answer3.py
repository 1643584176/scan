# -*- coding: utf-8 -*-
# _peek_answer3.py - precise: find "/answers" or answerAgentRunnerSession callers
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
    for m in re.finditer(r'.{600}/answers.{200}', src, re.S):
        seg = m.group(0)
        if "agent" in seg.lower() or "interaction" in seg.lower() or "question" in seg.lower():
            print("###", fn)
            print(seg[:1200])
            print()
