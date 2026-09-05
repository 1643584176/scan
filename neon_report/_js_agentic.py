# -*- coding: utf-8 -*-
"""Round 5: agentic provisioning full API defs + UI logic (approve flow, scopes)."""
import os
import re
import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

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


def show(title, regex, span=800, maxhits=6):
    print("=" * 25, title, "=" * 25, flush=True)
    pat = re.compile(regex)
    hits = 0
    for m in pat.finditer(blob):
        seg = blob[max(0, m.start() - span):m.start() + span]
        seg = re.sub(r"\s+", " ", seg)
        print("[%d] ...%s" % (hits, seg))
        print(flush=True)
        hits += 1
        if hits >= maxhits:
            break
    if not hits:
        print("  (no hits)", flush=True)


# 1. SDK method names containing Agentic / AccountRequest / Approve
show("agentic api methods", r"\w*[Aa]gentic\w*=\([^=]{0,40}\)=>this\.request", maxhits=10)
# direct: find path context
show("account_requests def", r"account_requests", maxhits=8, span=900)
print("== DONE", flush=True)
