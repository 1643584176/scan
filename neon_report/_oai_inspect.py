# -*- coding: utf-8 -*-
"""Inspect downloaded openapi.json for permission metadata & branch endpoints."""
import json
import os

P = r"F:\scan\neon_report\_openapi.json"
d = json.load(open(P, encoding="utf-8"))
print("top keys:", list(d.keys())[:10])
paths = d.get("paths", {})
print("paths count:", len(paths))

# any security/permission annotations in components/securitySchemes
sc = d.get("components", {}).get("securitySchemes", {})
print("securitySchemes:", list(sc.keys()) if isinstance(sc, dict) else sc)

# inspect branch create + fork related paths for x-* permission markers
hits = [p for p in paths if "branch" in p.lower()]
print("branch paths:", len(hits))
for p in sorted(hits)[:40]:
    item = paths[p]
    ops = ",".join(m.upper() for m in item if m.lower() in ("get", "post", "patch", "put", "delete"))
    tags = item.get("post", {}).get("tags", []) or item.get("get", {}).get("tags", [])
    extra = {k: v for k, v in item.get("post", {}).items() if k.startswith("x-")}
    extra2 = {k: v for k, v in item.get("get", {}).items() if k.startswith("x-") if not extra}
    print("  %-70s %-12s %s %s" % (p, ops, tags, dict(extra, **extra2)))
