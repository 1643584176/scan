# -*- coding: utf-8 -*-
"""Show full scope detail for db candidates"""
import json

WANT = ["neon_bbp", "mongodb", "supabase", "databricks", "gocardless_bbp"]

with open(r"F:\scan\h1_programs.json", encoding="utf-8") as fh:
    data = json.load(fh)

for p in data:
    if (p.get("handle") or "") not in WANT:
        continue
    print("=" * 60)
    print("NAME:", p.get("name"), "| @" + str(p.get("handle")),
          "| managed=", p.get("managed_program"),
          "| bounty=", p.get("offers_bounties"),
          "| state=", p.get("submission_state"))
    print("eff=", p.get("response_efficiency_percentage"),
          "| firstResp=", p.get("average_time_to_first_program_response"), "h",
          "| resolve=", p.get("average_time_to_report_resolved"), "d")
    print("url:", p.get("url"))
    for t in p.get("targets", {}).get("in_scope", []):
        print("  IN  [%s] %s" % (t.get("asset_type"), t.get("asset_identifier")))
    outs = p.get("targets", {}).get("out_of_scope", [])
    print("  -- out_of_scope:", len(outs))
    for t in outs[:10]:
        print("  OUT [%s] %s" % (t.get("asset_type"), t.get("asset_identifier")))
