# -*- coding: utf-8 -*-
"""Deep-dive selected candidates: show full in-scope targets & response stats"""
import json

WANT = ["neon_bbp", "doppler", "mergify", "kong", "basecamp", "smtp2go",
        "portswigger", "files", "matomo", "notion", "faraday_inc", "judgeme",
        "inspectorio", "floqast", "django", "nodejs", "ruby", "vercel-open-source"]

with open(r"F:\scan\h1_programs.json", encoding="utf-8") as fh:
    data = json.load(fh)

for p in data:
    if (p.get("handle") or "") not in WANT:
        continue
    print("=" * 70)
    print("NAME: %s | @%s | managed=%s | bounties=%s | state=%s" % (
        p.get("name"), p.get("handle"), p.get("managed_program"),
        p.get("offers_bounties"), p.get("submission_state")))
    print("response_eff=%s | avg_first_resp=%sh | avg_resolve=%sd | url=%s" % (
        p.get("response_efficiency_percentage"),
        p.get("average_time_to_first_program_response"),
        p.get("average_time_to_report_resolved"), p.get("url")))
    ins = p.get("targets", {}).get("in_scope", [])
    print("--- in_scope (%d) ---" % len(ins))
    for t in ins:
        print("  [%s] %s" % (t.get("asset_type"), t.get("asset_identifier")))
    outs = p.get("targets", {}).get("out_of_scope", [])
    if outs:
        print("--- out_of_scope (%d) ---" % len(outs))
        for t in outs[:12]:
            print("  [%s] %s" % (t.get("asset_type"), t.get("asset_identifier")))
