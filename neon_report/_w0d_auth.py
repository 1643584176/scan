# -*- coding: utf-8 -*-
"""Detail auth webhook config + updateNeonAuthUserRole + data-api create schemas."""
import json

spec = json.load(open(r"F:\scan\neon_report\_openapi_v2.json", encoding="utf-8"))
comp = spec.get("components", {}).get("schemas", {})

want = ["NeonAuthWebhookConfig", "UpdateNeonAuthWebhookConfigRequest", "WebhookConfig",
        "UpdateNeonAuthUserRoleRequest", "CreateNeonAuthUserRequest", "NeonAuthUser"]
for n in want:
    if n in comp:
        print("SCHEMA", n)
        print(json.dumps(comp[n], indent=1)[:1400])

paths = spec.get("paths", {})
print("\n--- ops ---")
for p, item in paths.items():
    if any(k in p for k in ("webhook", "user-role", "neon-auth", "users")):
        for m, op in item.items():
            if isinstance(op, dict):
                print("OP", m.upper(), p, "->", op.get("operationId"))
                rb = op.get("requestBody", {}).get("content", {})
                for ct, v in rb.items():
                    print("   req:", json.dumps(v)[:260])
