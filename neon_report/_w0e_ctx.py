# -*- coding: utf-8 -*-
"""getNeonAuthWebhookConfig response schema + find auth-enabled branch context files."""
import json, glob, os

spec = json.load(open(r"F:\scan\neon_report\_openapi_v2.json", encoding="utf-8"))
for p, item in spec.get("paths", {}).items():
    if "webhooks" in p and item.get("get"):
        op = item["get"]
        resp = op.get("responses", {}).get("200", {}).get("content", {})
        print("GET", p, op.get("operationId"))
        print(json.dumps(resp)[:900])

# find context of auth-enabled branch (na users registered where)
for f in ["_ctx.json", "_auth_better_auth.json", "_na_sess.json"]:
    fp = os.path.join(r"F:\scan\neon_report", f)
    if os.path.exists(fp):
        try:
            d = json.load(open(fp, encoding="utf-8"))
            s = json.dumps(d, ensure_ascii=False)
            print("\n===", f, "===")
            print(s[:800])
        except Exception as e:
            print(f, "ERR", e)
