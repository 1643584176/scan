# -*- coding: utf-8 -*-
"""Check prod spec for ApiKeyCreateRequest scope + PermissionGrantRequest level param,
and dump flags json for per-project permission enablement."""
import json, os

for tag, path in [("PROD", r"F:\scan\neon_report\_openapi_v2_prod.json"),
                  ("STAGE", r"F:\scan\neon_report\_openapi_v2.json")]:
    try:
        spec = json.load(open(path, encoding="utf-8"))
    except Exception as e:
        print(tag, "ERR", e)
        continue
    sch = spec.get("components", {}).get("schemas", {})
    print("==", tag)
    for n in ("ApiKeyCreateRequest", "ApiKeyCreateResponse"):
        if n in sch:
            print(" ", n, json.dumps(sch[n])[:500])
    # grant request level?
    for n in ("GrantPermissionToProjectRequest", "CreateProjectPermissionRequest"):
        if n in sch:
            print(" ", n, json.dumps(sch[n])[:500])
    # any permission-level grant endpoints
    for p, item in spec.get("paths", {}).items():
        if "permission" in p.lower():
            for m, op in item.items():
                if isinstance(op, dict) and m in ("get", "post", "patch", "delete"):
                    print("  OP", m.upper(), p, op.get("operationId"))
                    rb = op.get("requestBody", {}).get("content", {})
                    for ct, v in rb.items():
                        print("     req:", json.dumps(v)[:300])

for f in [r"F:\scan\neon_report\_p81_flags_user.json", r"F:\scan\neon_report\_p81_flags_org.json"]:
    if os.path.exists(f):
        d = json.load(open(f, encoding="utf-8"))
        print("FLAGS", os.path.basename(f))
        s = json.dumps(d, ensure_ascii=False)
        print(s[:1500])
