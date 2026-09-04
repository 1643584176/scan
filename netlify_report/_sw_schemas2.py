# -*- coding: utf-8 -*-
# _sw_schemas2.py - find AddMember/UpdateMember setup schemas
import yaml, json

d = yaml.safe_load(open(r"D:/scan/netlify_report/_openapi/swagger.yml", encoding="utf-8"))
sch = d.get("components", {}).get("schemas", d.get("definitions", {}))
print("schema names:")
for name in sorted(sch.keys()):
    print(" ", name)
# also locate requestBody refs for member ops
for p in d.get("paths", {}):
    if "members" in p:
        for m, op in d["paths"][p].items():
            if isinstance(op, dict) and op.get("requestBody"):
                print(p, m, json.dumps(op["requestBody"], ensure_ascii=False)[:500])
