# -*- coding: utf-8 -*-
"""Inspect CreateComputeEndpoint requestBody schema."""
import json

spec = json.load(open(r"F:\scan\neon_report\_openapi_v2.json", encoding="utf-8"))
op = spec["paths"]["/projects/{project_id}/endpoints"]["post"]
ref = op.get("requestBody", {}).get("content", {}).get("application/json", {}).get("schema", {})
print("requestBody schema:", json.dumps(ref)[:400])
name = ref.get("$ref", "").rsplit("/", 1)[-1]
if name:
    s = spec["components"]["schemas"].get(name, {})
    print("SCHEMA", name)
    print(" required:", s.get("required"))
    print(" props:", json.dumps(s.get("properties", {}))[:800])
    print(" example:", json.dumps(s.get("example", {}))[:400])
