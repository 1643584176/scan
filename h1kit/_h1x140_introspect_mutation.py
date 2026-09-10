# -*- coding: utf-8 -*-
"""Introspection:Mutation 类型 collaborator/share/invite/participant 字段"""
import json
import urllib.request
import urllib.error

q = json.dumps({
    "query": """
    {
      __type(name: "Mutation") {
        fields {
          name
          args { name type { kind name ofType { kind name ofType { kind name } } } }
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

fields = data["data"]["__type"]["fields"]
print("total mutations:", len(fields))
kws = ["collab", "share", "invite", "participant", "access", "grant", "viewer"]
for f in fields:
    n = f["name"].lower()
    if any(k in n for k in kws):
        args = ",".join(a["name"] for a in f.get("args", []))
        print(f["name"], "(", args, ")")
