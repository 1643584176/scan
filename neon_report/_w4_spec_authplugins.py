# -*- coding: utf-8 -*-
"""Dump auth/plugins/* paths + schemas from spec."""
import json

spec = json.load(open(r"F:\scan\neon_report\_openapi_v2.json", encoding="utf-8"))
paths = spec["paths"]
for p in sorted(paths):
    if "auth/plugins" in p or "/auth" == p or p.endswith("/auth"):
        for m in ("get", "post", "patch", "delete", "put"):
            if m in paths[p]:
                op = paths[p][m]
                print("%-6s %s  %s" % (m.upper(), p, (op.get("summary") or "")[:70]))
                ref = (op.get("requestBody", {}).get("content", {})
                       .get("application/json", {}).get("schema", {}))
                nm = ref.get("$ref", "").rsplit("/", 1)[-1]
                if nm:
                    s = spec["components"]["schemas"].get(nm, {})
                    print("      BODY", nm, "required:", s.get("required"))
                    print("      props:", json.dumps(s.get("properties", {}))[:600])
# also find plugin-ish schemas
comp = spec.get("components", {}).get("schemas", {})
for n in comp:
    if "lugin" in n or "Auth" in n and "Config" in n:
        props = comp[n].get("properties", {})
        if isinstance(props, dict) and any("organization" in str(k).lower() or "plugin" in str(k).lower() for k in props):
            print("SCHEMA?", n, json.dumps(comp[n])[:400])
