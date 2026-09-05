# -*- coding: utf-8 -*-
"""Dump spec paths containing 'endpoint' (method + summary) to find create route."""
import json

spec = json.load(open(r"F:\scan\neon_report\_openapi_v2.json", encoding="utf-8"))
paths = spec.get("paths", {})
for p in sorted(paths):
    if "endpoint" in p.lower():
        for m in ("get", "post", "delete", "patch", "put"):
            if m in paths[p]:
                s = (paths[p][m].get("summary") or "")[:60]
                print("%-6s %s  %s" % (m.upper(), p, s))
