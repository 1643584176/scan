# -*- coding: utf-8 -*-
"""Dump spec paths containing 'role' to find the roles list / connection_uri shape."""
import json

spec = json.load(open(r"F:\scan\neon_report\_openapi_v2.json", encoding="utf-8"))
for p in sorted(spec.get("paths", {})):
    if "role" in p.lower() or "connection_uri" in p.lower():
        for m in ("get", "post", "delete", "patch"):
            if m in spec["paths"][p]:
                s = (spec["paths"][p][m].get("summary") or "")[:70]
                print("%-6s %s  %s" % (m.upper(), p, s))
