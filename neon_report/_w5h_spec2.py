# -*- coding: utf-8 -*-
import json
spec = json.load(open(r"F:\scan\neon_report\_openapi_v2.json", encoding="utf-8"))
paths = spec.get("paths", {})
want = ["transfer_requests", "email_server", "members", "permissions", "shared",
        "recover", "auth/config", "auth/users"]
for p in sorted(paths):
    if not any(w in p for w in want):
        continue
    for m in paths[p]:
        if m.lower() not in ("get", "post", "put", "patch", "delete"):
            continue
        op = paths[p][m]
        refs = []
        rb = op.get("requestBody", {})
        for ct, cval in rb.get("content", {}).items():
            sch = cval.get("schema", {})
            ref = sch.get("$ref", "")
            if ref:
                nm = ref.split("/")[-1]
                resolved = spec["components"]["schemas"].get(nm, {})
                req = resolved.get("required", [])
                props = {k: (v.get("type", "") + " " + (v.get("enum") and str(v["enum"]) or ""))
                         for k, v in resolved.get("properties", {}).items()}
                refs.append((nm, req, props))
        print("%-6s %s" % (m.upper(), p))
        for nm, req, props in refs:
            print("     body %s required=%s props=%s" % (nm, req, json.dumps(props, ensure_ascii=False)[:400]))
