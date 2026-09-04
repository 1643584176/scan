# -*- coding: utf-8 -*-
# _ui_bundle_api.py - extract API endpoints from app.netlify.com bundles
import re, os, json, collections

D = r"D:/scan/netlify_report/_js"
targets = ["net_app.js", "net_7884.js", "net_ui.js", "net_actions.js"]

pat_url = re.compile(r'["\'](https?://[^"\']{4,140})["\']')
pat_path = re.compile(r'["\'](/[a-zA-Z0-9_./{}${}:-]{3,120})["\']')

urls = collections.Counter()
paths = collections.Counter()

for fn in targets:
    p = os.path.join(D, fn)
    try:
        src = open(p, encoding="utf-8", errors="replace").read()
    except Exception as e:
        print(fn, "ERR", e)
        continue
    for m in pat_url.finditer(src):
        u = m.group(1)
        if any(s in u for s in ("netlify", "netlify.app", "netlify.com")):
            urls[u] += 1
    for m in pat_path.finditer(src):
        pth = m.group(1)
        if ("api/v1" in pth or "functions" in pth or "access-control" in pth
                or pth.startswith("/.netlify") or "account" in pth.lower()
                or "member" in pth.lower() or "team" in pth.lower()
                or "invite" in pth.lower() or "user" in pth.lower()):
            # skip obvious noise
            if re.search(r'\s|\.\.', pth):
                continue
            paths[pth] += 1

print("### URLs")
for u, c in urls.most_common(80):
    print(c, u)
print()
print("### PATHS (interesting)")
for pth, c in paths.most_common(400):
    print(c, pth)
