# -*- coding: utf-8 -*-
import json
spec = json.load(open(r"F:\scan\neon_report\_openapi_v2.json", encoding="utf-8"))
paths = spec.get("paths", {})
for p in paths:
    if "send_test_email" in p or ("email_provider" in p and "test" in p):
        for m in paths[p]:
            if m.lower() not in ("get", "post", "put", "patch", "delete"):
                continue
            op = paths[p][m]
            print(m.upper(), p)
            print("  desc:", (op.get("summary") or "")[:150])
            # request body schema ref
            rb = op.get("requestBody", {})
            cont = rb.get("content", {})
            for ct, cval in cont.items():
                sch = cval.get("schema", {})
                print("  body ct:", ct, json.dumps(sch, ensure_ascii=False)[:800])
                # resolve $ref
                ref = sch.get("$ref", "")
                if ref:
                    name = ref.split("/")[-1]
                    s2 = spec["components"]["schemas"].get(name, {})
                    print("  resolved:", json.dumps(s2, ensure_ascii=False)[:900])
            # parameters
            params = op.get("parameters", [])
            if isinstance(params, list):
                for par in params:
                    print("  param:", par.get("name"), par.get("in"), json.dumps(par.get("schema", {}))[:200])
            else:
                print("  params obj:", json.dumps(params)[:300])
