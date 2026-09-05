# -*- coding: utf-8 -*-
"""Deep-dive into console JS: locate real URL construction + call contexts
for SQL editor chain, transfer, reset, passwordless, auth/init, saved queries.
"""
import os
import re
import json

JS_DIR = r"F:\scan\neon_report\_js"
blob = ""
for root, _, files in os.walk(JS_DIR):
    for fn in files:
        if fn.endswith(".js"):
            fp = os.path.join(root, fn)
            try:
                blob += open(fp, encoding="utf-8", errors="replace").read() + "\n"
            except Exception:
                pass

print("total js bytes:", len(blob), flush=True)
OUT = {}


def dump(key, maxhits=2, span=700, regex=None):
    print("=" * 25, key, "=" * 25, flush=True)
    pat = re.compile(regex or re.escape(key))
    hits = 0
    for m in pat.finditer(blob):
        seg = blob[max(0, m.start() - span):m.start() + span]
        seg = re.sub(r"\s+", " ", seg)
        print("[%d]" % hits)
        print("  ...%s" % seg)
        print(flush=True)
        hits += 1
        if hits >= maxhits:
            break
    if not hits:
        print("  (no hits)", flush=True)
    OUT[key] = hits


# 1. runProjectQuery definition + SQL editor endpoints
dump("runProjectQuery", maxhits=1, span=900)
dump("query/history", maxhits=3, span=400)
dump("saved_queries", maxhits=3, span=400)
dump("role_change_preview", maxhits=2, span=500)
# 2. transfer_ownership context
dump("transfer_ownership", maxhits=3, span=700)
# 3. reset + source_branch_id
dump("source_branch_id", maxhits=4, span=450)
dump("reset_to_parent", maxhits=3, span=600)
# 4. passwordless session flow
dump("passwordless", maxhits=4, span=600)
dump("session_id", maxhits=4, span=400)
# 5. auth/init providers
dump("auth/init", maxhits=4, span=600)
# 6. org-scoped vs user-scoped api keys
dump("organization-scoped", maxhits=3, span=600)
dump("scope", maxhits=3, span=300)
print("== DONE", flush=True)
