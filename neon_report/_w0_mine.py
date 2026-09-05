# -*- coding: utf-8 -*-
"""Mine _openapi_v2.json: (1) createApiKey scope/permission params + schema,
(2) webhook-ish endpoints, (3) project permissions endpoints, (4) transfer."""
import json

spec = json.load(open(r"F:\scan\neon_report\_openapi_v2.json", encoding="utf-8"))

# 1. find api key create op and its schema
paths = spec.get("paths", {})
for p, item in paths.items():
    if "api_keys" in p or "apikey" in p.lower():
        for m, op in item.items():
            if isinstance(op, dict) and m in ("get", "post", "delete"):
                print("OP", m.upper(), p, "->", op.get("operationId"))
                if m == "post":
                    rb = op.get("requestBody", {}).get("content", {})
                    for ct, v in rb.items():
                        ref = v.get("schema", {}).get("$ref", "")
                        print("   req schema ref:", ref)
                        if ref:
                            name = ref.split("/")[-1]
                            sch = spec["components"]["schemas"][name]
                            props = sch.get("properties", {})
                            for pn, pv in props.items():
                                print("     prop:", pn, "|", json.dumps(pv)[:200])
                            print("   required:", sch.get("required"))
                if m == "get":
                    print("   resp:", json.dumps(op.get("responses", {}).get("200", {}))[:200])

# 2. schema for scoped permission (ApiKeyScope?)
comp = spec.get("components", {}).get("schemas", {})
for name in comp:
    if any(k in name.lower() for k in ("apikey", "key_scope", "permission")):
        s = comp[name]
        if name.lower().startswith("api") or "scope" in name.lower() or "permission" in name.lower():
            print("SCHEMA", name, "|", json.dumps(s)[:400])

# 3. webhook endpoints
print("\n--- webhook-ish paths ---")
for p, item in paths.items():
    if "webhook" in p.lower():
        for m, op in item.items():
            if isinstance(op, dict):
                print("OP", m.upper(), p, op.get("operationId"))
