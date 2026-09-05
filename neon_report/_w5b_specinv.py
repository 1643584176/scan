# -*- coding: utf-8 -*-
"""W5b: spec full route inventory + API key scope model."""
import json, re

spec = json.load(open(r"F:\scan\neon_report\_openapi_v2.json", encoding="utf-8"))
paths = spec.get("paths", {})
print("TOTAL PATHS:", len(paths))

# group by first two segments
from collections import Counter, defaultdict
segs = defaultdict(list)
for p in paths:
    parts = [x for x in p.split("/") if x and not x.startswith("{")]
    key = "/" + "/".join(parts[:3])
    segs[key].append(p)
for k in sorted(segs):
    print(k, "->", len(segs[k]))

# api key schemas
print("\n=== api key related schemas ===")
for name, s in spec.get("components", {}).get("schemas", {}).items():
    if "ApiKey" in name or "api_key" in name.lower() or "apikey" in name.lower():
        print(name, json.dumps(s, ensure_ascii=False)[:600])

# paths mentioning api_key
print("\n=== api key paths ===")
for p in paths:
    if "api_key" in p.lower() or "apikey" in p.lower():
        for m in paths[p]:
            print(m.upper(), p, "|", list(paths[p][m].get("parameters", [])))

# any path containing unusual segments (admin/internal/ops/meta/debug etc)
print("\n=== unusual paths ===")
for p in paths:
    low = p.lower()
    if any(k in low for k in ("admin", "internal", "debug", "meta", "ops", "health",
                              "web", "auth", "sso", "import", "export", "transfer",
                              "keys", "secret", "token", "member", "invite",
                              "email", "support", "zones", "region")):
        print(p)
