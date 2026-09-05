# -*- coding: utf-8 -*-
"""Find branch-create related schemas and any schema-only / mode / data fields in spec."""
import json

spec = json.load(open(r"F:\scan\neon_report\_openapi_v2.json", encoding="utf-8"))
comp = spec.get("components", {}).get("schemas", {})

# candidates: branch create request schemas
for n in comp:
    if any(k in n for k in ("BranchCreate", "Branch", "CreateBranch")):
        s = comp[n]
        props = s.get("properties", {})
        if isinstance(props, dict):
            interesting = {k: v for k, v in props.items() if any(
                kw in k.lower() for kw in ("mode", "schema", "data", "lsn", "timestamp", "parent", "protect", "name"))}
            if interesting or n in ("BranchCreateRequest", "Branch", "CreateProjectBranchRequest"):
                print("SCHEMA", n, "required:", s.get("required"))
                for k, v in interesting.items():
                    print("   ", k, "=", json.dumps(v)[:180])
print("---- full Branch schema ----")
if "Branch" in comp:
    print(json.dumps(comp["Branch"])[:2500])
