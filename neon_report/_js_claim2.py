# -*- coding: utf-8 -*-
"""Round 7: approve-page detail rows (what fields shown), claim page API calls,
CSRF header source, request id/orchestrator format hints."""
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


def show(title, regex, span=900, maxhits=4):
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


# detail rows rendering after success (fields)
show("approve success fields", r"Connection approved successfully[^;]{0,1200}", maxhits=2, span=200)
show("detail row fields", r"detailRow[^;]{0,800}", maxhits=3, span=400)
# claim component fetch calls
show("claim component calls", r"displayName=\"Claim\"[^}]{0,1500}", maxhits=1, span=100)
# CSRF token source
show("csrf source", r"[Xx]\-CSRF[^;]{0,200}", maxhits=4, span=200)
# agentic request id sample (uuid?)
show("orchestrator usage", r"orchestrator[^;]{0,250}", maxhits=5, span=300)
print("== DONE", flush=True)
