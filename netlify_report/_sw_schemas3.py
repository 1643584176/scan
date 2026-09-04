# -*- coding: utf-8 -*-
# _sw_schemas3.py - dump accountAddMemberSetup & accountUpdateMemberSetup + accountMembership
import yaml, json

d = yaml.safe_load(open(r"D:/scan/netlify_report/_openapi/swagger.yml", encoding="utf-8"))
sch = d.get("components", {}).get("schemas", d.get("definitions", {}))
for name in ("accountAddMemberSetup", "accountUpdateMemberSetup", "accountMembership", "member"):
    print("#" * 30, name)
    print(json.dumps(sch.get(name, {}), ensure_ascii=False, indent=1))
