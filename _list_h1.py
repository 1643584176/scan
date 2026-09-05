# -*- coding: utf-8 -*-
"""List all open bounty programs with target counts for manual review"""
import json

with open(r"F:\scan\h1_programs.json", encoding="utf-8") as fh:
    data = json.load(fh)

rows = []
for p in data:
    if p.get("submission_state") != "open":
        continue
    if not p.get("offers_bounties"):
        continue
    targets = p.get("targets", {}).get("in_scope", [])
    n_url = sum(1 for t in targets if t.get("asset_type") in ("URL", "WILDCARD"))
    rows.append({
        "name": p.get("name"),
        "handle": p.get("handle"),
        "n": len(targets),
        "n_url": n_url,
        "eff": p.get("response_efficiency_percentage"),
    })

rows.sort(key=lambda r: (r["n_url"]))
print("total open+bounty:", len(rows))
print("--- by url-target count (smallest first) ---")
for r in rows:
    print("%-3d url %-3d all | %s | @%s | eff=%s" % (r["n_url"], r["n"], r["name"], r["handle"], r["eff"]))
