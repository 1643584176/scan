# -*- coding: utf-8 -*-
# _peek_actions.py - dump all action= param values near support-tickets / other fn
import re, os

for fn in os.listdir(r"D:/scan/netlify_report/_js"):
    if not fn.endswith(".js"):
        continue
    p = os.path.join(r"D:/scan/netlify_report/_js", fn)
    src = open(p, encoding="utf-8", errors="replace").read()
    for patname in ("support-tickets", "usage-and-billing", "labs-list", "labs-toggle",
                    "generate-bandwidth-usage-csv", "private-integration-create"):
        for m in re.finditer(re.escape(patname), src):
            chunk = src[max(0, m.start() - 200):m.end() + 400]
            for a in re.finditer(r'action["\']?\s*,\s*["\']([a-z-]+)["\']', chunk):
                print(fn, patname, "ACTION:", a.group(1))
            for a in re.finditer(r'set\("action","([a-z-]+)"\)', chunk):
                print(fn, patname, "ACTION:", a.group(1))
