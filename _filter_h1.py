# -*- coding: utf-8 -*-
"""Filter H1 programs matching our experience profile (cloud/API/dev-tools/SaaS)"""
import json

with open(r"F:\scan\h1_programs.json", encoding="utf-8") as fh:
    data = json.load(fh)

# Experience keywords: cloud sandbox / serverless / api platform / dev tools / collaboration
AREA_KW = [
    "cloud", "serverless", "deploy", "hosting", "devops", "infra", "container",
    "api", "developer", "sdk", "platform", "saas", "collaboration", "design",
    "analytics", "automation", "workflow", "database", "postgres", "messaging",
]

# Big players we want to avoid (huge attack surface, crowded): keep list small
BIG = ["google", "microsoft", "facebook", "meta", "amazon", "apple", "ibm",
       "oracle", "salesforce", "adobe", "uber", "twitter", "linkedin", "github"]

print("=== candidates: open + bounty + area keyword ===")
cands = []
for p in data:
    if p.get("submission_state") != "open":
        continue
    if not p.get("offers_bounties"):
        continue
    name = (p.get("name") or "").lower()
    handle = (p.get("handle") or "").lower()
    if any(b in name or b in handle for b in BIG):
        continue
    # collect scope identifiers
    ids = []
    for t in p.get("targets", {}).get("in_scope", []):
        ids.append((t.get("asset_identifier") or "") + "|" + (t.get("asset_type") or ""))
    blob = (name + " " + handle + " " + " ".join(ids)).lower()
    if any(k in blob for k in AREA_KW):
        cands.append({
            "name": p.get("name"), "handle": p.get("handle"),
            "url": p.get("url"), "managed": p.get("managed_program"),
            "response_eff": p.get("response_efficiency_percentage"),
            "avg_first_resp_h": p.get("average_time_to_first_program_response"),
            "avg_resolve_d": p.get("average_time_to_report_resolved"),
            "n_targets": len(p.get("targets", {}).get("in_scope", [])),
            "targets": ids[:8],
        })

print("count:", len(cands))
for c in sorted(cands, key=lambda x: -(x["n_targets"])):
    print("- %s | handle=%s | managed=%s | respEff=%s | firstResp=%sh | resolve=%sd | targets=%d"
          % (c["name"], c["handle"], c["managed"], c["response_eff"],
             c["avg_first_resp_h"], c["avg_resolve_d"], c["n_targets"]))
    for t in c["targets"][:4]:
        print("    scope:", t)
