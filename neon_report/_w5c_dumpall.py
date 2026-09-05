# -*- coding: utf-8 -*-
"""W5c: dump all paths with methods + relevant schemas."""
import json

spec = json.load(open(r"F:\scan\neon_report\_openapi_v2.json", encoding="utf-8"))
paths = spec.get("paths", {})
for p in sorted(paths):
    for m in paths[p]:
        if m.lower() not in ("get", "post", "put", "patch", "delete", "head", "options"):
            continue
        op = paths[p][m]
        # parameters can be list or object
        print("%-6s %s" % (m.upper(), p))
