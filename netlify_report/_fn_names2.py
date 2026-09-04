# -*- coding: utf-8 -*-
# _fn_names2.py - extract all .netlify/functions/<name> and internal endpoint patterns from bundles
import re, os, collections

D = r"D:/scan/netlify_report/_js"
out = []

fn_pat = re.compile(r'functions/([a-zA-Z0-9_-]{2,80})')
paths_pat = re.compile(r'["\'](/[a-zA-Z0-9_./\-{}:]{2,120})["\']')

funcs = collections.Counter()
all_paths = collections.Counter()

for fn in os.listdir(D):
    if not fn.endswith(".js"):
        continue
    p = os.path.join(D, fn)
    try:
        src = open(p, encoding="utf-8", errors="replace").read()
    except Exception:
        continue
    for m in fn_pat.finditer(src):
        funcs[m.group(1)] += 1
    for m in paths_pat.finditer(src):
        pth = m.group(1)
        if re.search(r"\s|\.\.", pth):
            continue
        all_paths[pth] += 1

print("### functions names (count>=1, top 200)")
for name, c in funcs.most_common(200):
    print(c, name)
print()
print("### paths containing api/function/control (filtered)")
for pth, c in all_paths.most_common(400):
    if any(s in pth for s in ("access-control", "netlify/functions", "spark", "workflow",
                              "labs", "self-host", "bitbucket", "connect", "graphql",
                              "analytics", "audit", "agent", "runner", "gateway",
                              "ai-", "database", "blobs", "v1/", "api/")):
        print(c, pth)
