# -*- coding: utf-8 -*-
# _org_bundle.py - find organizations API call templates in bundle
import re, os

D = r"D:/scan/netlify_report/_js"
for fn in ("net_app.js", "net_7884.js", "net_actions.js", "net_ui.js"):
    src = open(os.path.join(D, fn), encoding="utf-8", errors="replace").read()
    # find path-like strings containing organizations
    hits = set()
    for m in re.finditer(r'["\'](/[^"\']*organizations?[^"\']*)["\']', src, re.I):
        p = m.group(1)
        if not re.search(r'\.(js|css|png|svg|json)$', p) and len(p) < 120:
            hits.add(p)
    if hits:
        print("#" * 20, fn)
        for h in sorted(hits):
            print("  ", h)
