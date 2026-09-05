# -*- coding: utf-8 -*-
"""V33: extract API endpoint strings from console frontend JS bundles"""
import re, os, json, collections

ROOT = r"F:\scan\neon_report\_js"
pat = re.compile(r'"(/api/v2/[a-zA-Z0-9_\-{}./]+)"')
pat2 = re.compile(r"'(/api/v2/[a-zA-Z0-9_\-{}./]+)'")
seen = collections.Counter()
files = []
for dirpath, _, names in os.walk(ROOT):
    for n in names:
        if n.endswith(".js"):
            files.append(os.path.join(dirpath, n))
print("files:", len(files))
for f in files:
    try:
        s = open(f, encoding="utf-8", errors="replace").read()
    except Exception:
        continue
    for m in pat.findall(s) + pat2.findall(s):
        seen[m] += 1

# templates with {id} style path params, keep unique
for k in sorted(seen):
    print("%4d  %s" % (seen[k], k))
print("total unique:", len(seen))
json.dump(sorted(seen), open(r"F:\scan\neon_report\_v33_api_paths.json", "w"), indent=1)
