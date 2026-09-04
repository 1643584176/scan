# -*- coding: utf-8 -*-
# _sw_detail.py - detail of member/account/user paths in swagger
import yaml, json

d = yaml.safe_load(open(r"D:/scan/netlify_report/_openapi/swagger.yml", encoding="utf-8"))
print("servers/basePath:", d.get("servers"), d.get("basePath"), d.get("host"))
for p in sorted(d.get("paths", {}).keys()):
    if any(s in p.lower() for s in ("member", "user", "account", "audit")):
        item = d["paths"][p]
        print("#" * 40)
        print("PATH:", p)
        for m, op in item.items():
            if m.lower() not in ("get", "post", "put", "patch", "delete", "head", "options"):
                continue
            print("  %s %s -- %s" % (m.upper(), p, op.get("summary", "")))
            params = op.get("parameters", [])
            for pa in params:
                print("    param:", pa.get("name"), pa.get("in"), pa.get("required"), pa.get("schema", {}).get("type", ""), pa.get("description", "")[:60])
            rb = op.get("requestBody")
            if rb:
                print("    body:", json.dumps(rb.get("content", {}), ensure_ascii=False)[:300])
            print("    tags:", op.get("tags"))
