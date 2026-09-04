# -*- coding: utf-8 -*-
# _peek_fnctx.py - dump usage context of selected internal functions
import re, os, sys

WANT = sys.argv[1] if len(sys.argv) > 1 else "support-tickets"

for fn in os.listdir(r"D:/scan/netlify_report/_js"):
    if not fn.endswith(".js"):
        continue
    p = os.path.join(r"D:/scan/netlify_report/_js", fn)
    src = open(p, encoding="utf-8", errors="replace").read()
    hits = list(re.finditer(re.escape(WANT), src))
    if not hits:
        continue
    print("### FILE:", fn, "hits:", len(hits))
    for m in hits[:8]:
        s = max(0, m.start() - 350)
        e = min(len(src), m.end() + 350)
        print(repr(src[s:e]))
        print("---")
