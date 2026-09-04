# -*- coding: utf-8 -*-
# _ui_devservers.py - extract dev_servers API shape from bundles
import re, os

D = r"D:/scan/netlify_report/_js"
for fn in ("net_app.js", "net_7884.js", "net_ui.js", "net_actions.js"):
    src = open(os.path.join(D, fn), encoding="utf-8", errors="replace").read()
    hits = [m.start() for m in re.finditer(r"dev_servers|devServer|dev-server|DevServer", src)]
    if not hits:
        continue
    print("#" * 30, fn, "hits:", len(hits))
    seen = set()
    for i in hits:
        ctx = src[max(0, i - 200): i + 250]
        key = ctx[:150]
        if key in seen:
            continue
        seen.add(key)
        print("-" * 70)
        print(ctx.replace("\n", " ")[:420])
        if len(seen) > 25:
            break
