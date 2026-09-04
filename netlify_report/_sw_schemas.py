# -*- coding: utf-8 -*-
# _sw_schemas.py - dump member-related schemas from swagger
import yaml, json

d = yaml.safe_load(open(r"D:/scan/netlify_report/_openapi/swagger.yml", encoding="utf-8"))
sch = d.get("components", {}).get("schemas", d.get("definitions", {}))
for name in sch:
    if any(s in name.lower() for s in ("member", "account", "role", "invite", "audit", "user")):
        s = sch[name]
        print("#" * 30, name)
        print(json.dumps(s, ensure_ascii=False, indent=1)[:1500])
