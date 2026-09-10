# -*- coding: utf-8 -*-
"""Introspection:User 类型 2FA/API 相关字段(匿名)"""
import json
import urllib.request
import urllib.error

q = json.dumps({
    "query": """
    {
      __type(name: "User") {
        fields {
          name
          type { kind name ofType { kind name ofType { kind name } } }
        }
      }
    }
    """
}).encode()

r = urllib.request.Request("https://hackerone.com/graphql", data=q, method="POST")
r.add_header("Content-Type", "application/json")
try:
    with urllib.request.urlopen(r, timeout=25) as resp:
        data = json.loads(resp.read().decode("utf-8", "replace"))
except urllib.error.HTTPError as e:
    print("HTTP", e.code, e.read().decode("utf-8", "replace")[:300])
    raise SystemExit

out = []
try:
    fields = data["data"]["__type"]["fields"]
except Exception:
    print("unexpected:", json.dumps(data)[:500])
    raise SystemExit

for f in fields:
    n = f["name"].lower()
    if any(k in n for k in ["two", "factor", "otp", "api", "token", "mfa"]):
        out.append(f["name"])

print("\n".join(sorted(out)))
