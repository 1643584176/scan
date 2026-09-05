# -*- coding: utf-8 -*-
import json
spec = json.load(open(r"F:\scan\neon_report\_openapi_v2.json", encoding="utf-8"))
p = "/projects/{project_id}/transfer_requests/{request_id}"
for m in spec["paths"].get(p, {}):
    if m.lower() != "put":
        continue
    op = spec["paths"][p][m]
    print("summary:", op.get("summary"), "|", op.get("description", "")[:300])
    for ct, cval in op.get("requestBody", {}).get("content", {}).items():
        sch = cval.get("schema", {})
        print("body:", json.dumps(sch, ensure_ascii=False))
        ref = sch.get("$ref", "")
        if ref:
            nm = ref.split("/")[-1]
            s2 = spec["components"]["schemas"].get(nm, {})
            print("resolved:", json.dumps(s2, ensure_ascii=False)[:1000])
    # response codes
    for code in op.get("responses", {}):
        print("resp:", code)
