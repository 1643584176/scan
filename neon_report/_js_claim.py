# -*- coding: utf-8 -*-
"""Round 6: claim-project flow APIs + agentic route params source + csrf/auth."""
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


def show(title, regex, span=800, maxhits=5):
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


# claim APIs
show("claim api defs", r"\w*[Cc]laim\w*=\([^=]{0,60}\)=>this\.request", maxhits=8)
show("claim callers", r"claimProject|ClaimProject|/claim", maxhits=5, span=500)
# agentic route params (b0 orchestrator) — find route path w/ :orchestrator
show("agentic route", r"agentic_provisioning[^`\"]{0,200}", maxhits=3, span=400)
# csrf token fn
show("csrf", r"function cS\(\)\{[^}]{0,200}\}", maxhits=2, span=200)
# what oS is (axios base)
show("oS axios", r"oS=[^;]{0,300}", maxhits=2, span=100)
print("== DONE", flush=True)
