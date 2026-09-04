# -*- coding: utf-8 -*-
# _ui_member_calls.py - find member/invite/organization API call sites in bundle
import re, os

D = r"D:/scan/netlify_report/_js"
src = open(os.path.join(D, "net_app.js"), encoding="utf-8", errors="replace").read()
print("size:", len(src))

# find contexts around 'members' strings that look like api path templates
idxs = [m.start() for m in re.finditer(r'members', src)]
print("members occurrences:", len(idxs))

seen = set()
for i in idxs:
    ctx = src[max(0, i - 120): i + 160]
    # keep only when near /api/ or /v1 or access-control or fetch-ish
    if re.search(r'api|v1|fetch|/teams|url|axios', ctx):
        key = ctx[:120]
        if key in seen:
            continue
        seen.add(key)
        print("-" * 70)
        print(ctx.replace("\n", " ")[:260])

print()
print("### organization-related paths")
for m in re.finditer(r'["\'](/[a-zA-Z0-9_./{}${}:-]*organi[a-zA-Z0-9_./{}${}:-]*)["\']', src):
    print(m.group(1))
