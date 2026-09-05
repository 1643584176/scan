# -*- coding: utf-8 -*-
"""Round 2 deep-dive: find CALLERS of dangerous APIs + passwordless psql template.
- who calls runProjectQuery (SQL editor) & with what body
- passwordless psql template (wZ / psql_passwordless) — session_id source
- jwks context (who owns JWKS, what key type)
- permissions grant body
- transfer_requests body
"""
import os
import re

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

# Work on minified blob: find "runProjectQuery(" occurrences OTHER than the definition.
# The definition line contains `path:\`/projects/${encodeURIComponent(t)}/query\``.
# Callers appear like: .runProjectQuery( or }runProjectQuery( or N.runProjectQuery(


def show(key, span=500, maxhits=6, regex=None, exclude_def=True):
    print("=" * 25, key, "=" * 25, flush=True)
    pat = re.compile(regex or re.escape(key))
    hits = 0
    for m in pat.finditer(blob):
        seg = blob[max(0, m.start() - span):m.start() + span]
        seg = re.sub(r"\s+", " ", seg)
        if exclude_def and "path:`" in seg and "method:" in seg and "request({path" in seg:
            continue
        print("[%d] ...%s" % (hits, seg))
        print(flush=True)
        hits += 1
        if hits >= maxhits:
            break
    if not hits:
        print("  (no caller hits)", flush=True)


# 1. SQL editor: callers of runProjectQuery + query body builder
show("runProjectQuery(", span=700, maxhits=4)
show("runProjectQuery", span=900, maxhits=1,
     regex=r"runProjectQuery\([^)]{0,80}\)")
# 2. passwordless psql template content
show("psql_passwordless", span=800, maxhits=2)
show("passwordless", span=800, maxhits=2,
     regex=r"passwordless[^;]{0,500}auth")
# 3. jwks callers
show("Jwks", span=700, maxhits=4)
# 4. permissions grant body + callers
show("grantPermissionToProject", span=800, maxhits=2, exclude_def=False)
show("ProjectPermissions", span=600, maxhits=2, exclude_def=False)
# 5. transfer_requests body
show("transfer_requests", span=700, maxhits=3, exclude_def=False)
print("== DONE", flush=True)
