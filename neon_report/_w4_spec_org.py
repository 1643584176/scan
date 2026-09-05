# -*- coding: utf-8 -*-
"""Dump spec paths containing org|billing|plan|payment|invoice|subscription."""
import json

spec = json.load(open(r"F:\scan\neon_report\_openapi_v2.json", encoding="utf-8"))
for p in sorted(spec.get("paths", {})):
    pl = p.lower()
    if any(k in pl for k in ("org", "billing", "plan", "payment", "invoice",
                             "subscription", "quota", "usage")):
        for m in ("get", "post", "delete", "patch", "put"):
            if m in spec["paths"][p]:
                s = (spec["paths"][p][m].get("summary") or "")[:75]
                print("%-6s %s  %s" % (m.upper(), p, s))
