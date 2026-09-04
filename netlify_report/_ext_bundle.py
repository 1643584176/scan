# -*- coding: utf-8 -*-
# _ext_bundle.py - find install-extension call shape in bundle
import re, os

D = r"D:/scan/netlify_report/_js"
src = open(os.path.join(D, "net_app.js"), encoding="utf-8", errors="replace").read()

for name in ("install-extension", "uninstall-extension", "delete-all-team-installations-for-team",
             "delete-configurations-for-site", "manage-extension-proxy", "fetch-site-configuration"):
    idxs = [m.start() for m in re.finditer(re.escape(name), src)]
    print("#" * 30, name, len(idxs))
    seen = set()
    for i in idxs:
        ctx = src[max(0, i - 300): i + 300]
        key = ctx[:200]
        if key in seen:
            continue
        seen.add(key)
        print("-" * 60)
        print(ctx.replace("\n", " ")[:560])
        if len(seen) > 4:
            break
