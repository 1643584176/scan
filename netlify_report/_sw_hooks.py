# -*- coding: utf-8 -*-
# _sw_hooks.py - dump hooks paths detail from swagger
import yaml, json

d = yaml.safe_load(open(r"D:/scan/netlify_report/_openapi/swagger.yml", encoding="utf-8"))
for p in d.get("paths", {}):
    if "hook" in p:
        for m, op in d["paths"][p].items():
            if not isinstance(op, dict):
                continue
            print("#" * 30, m.upper(), p, "--", op.get("summary", ""))
            for pa in op.get("parameters", []):
                print("   param:", pa.get("name"), pa.get("in"), "req:", pa.get("required"))
            rb = op.get("requestBody")
            if rb:
                print("   body:", json.dumps(rb, ensure_ascii=False)[:800])
            sch = op.get("responses", {}).get("200", {})
            print("   resp200:", json.dumps(sch, ensure_ascii=False)[:300])
