# -*- coding: utf-8 -*-
"""Introspection:Report 类型字段(找关联/泄露面)"""
import json
import urllib.request
import urllib.error

q = json.dumps({
    "query": """
    {
      __type(name: "Report") {
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

fields = data["data"]["__type"]["fields"]
print("total fields:", len(fields))
kws = ["dup", "relat", "group", "team", "report", "participant", "assignee",
       "collab", "mention", "ref", "source", "similar", "match", "share", "export"]
for f in fields:
    n = f["name"].lower()
    if any(k in n for k in kws):
        t = f["type"]
        def nm(t):
            if not t:
                return "?"
            return t.get("name") or (nm(t.get("ofType")) + "!")
        print(f['name'], "::", nm(t))
