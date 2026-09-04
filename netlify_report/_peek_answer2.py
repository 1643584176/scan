# -*- coding: utf-8 -*-
# _peek_answer2.py - find answer payload shape in app bundles
import os, re
base = r"D:\scan\netlify_report\_js"
hits = []
for fn in os.listdir(base):
    if not fn.endswith(".js"):
        continue
    p = os.path.join(base, fn)
    try:
        src = open(p, encoding="utf-8", errors="replace").read()
    except Exception:
        continue
    for m in re.finditer(r'.{200}interaction.{400}', src, re.S):
        seg = m.group(0)
        if "answer" in seg.lower() or "option" in seg.lower() or "response" in seg.lower():
            hits.append((fn, seg[:600]))
for fn, seg in hits[:12]:
    print("###", fn)
    print(seg)
    print()
