# -*- coding: utf-8 -*-
# _peek_answer4.py - find field names near interaction handling in net_app.js
import os, re
base = r"D:\scan\netlify_report\_js"
for fn in sorted(os.listdir(base)):
    if not (fn.endswith(".js") and ("app" in fn or "agent" in fn)):
        continue
    p = os.path.join(base, fn)
    try:
        src = open(p, encoding="utf-8", errors="replace").read()
    except Exception:
        continue
    for m in re.finditer(r'.{80}(option_index|interaction_id|awaiting|question_id).{200}', src, re.S):
        seg = m.group(0)
        # filter real hits
        if "agent" in seg.lower() or "interaction" in seg.lower() or "option" in seg.lower():
            print("###", fn)
            print(seg[:420])
            print()
