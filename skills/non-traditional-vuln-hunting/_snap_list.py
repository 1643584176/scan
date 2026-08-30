# -*- coding: utf-8 -*-
"""列出当前 team 下所有 sandbox 和 snapshot, 评估可释放空间"""
import json, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vercel_driver import api

# sandboxes
c, r = api("GET", "/v2/sandboxes?teamId=%s&project=%s&limit=50" % (__import__("vercel_driver").TEAM, __import__("vercel_driver").PROJ))
print("sandboxes:", c)
try:
    d = json.loads(r)
    sbs = d.get("sandboxes", d if isinstance(d, list) else [])
    for s in sbs:
        print("  SB", s.get("id"), s.get("name"), s.get("status"))
except Exception as e:
    print("  parse err", e, r[:400])

# snapshots
for ep in ["/v2/snapshots", "/v1/snapshots"]:
    c, r = api("GET", ep + "?teamId=%s&project=%s&limit=50" % (__import__("vercel_driver").TEAM, __import__("vercel_driver").PROJ))
    print(ep, "->", c)
    try:
        d = json.loads(r)
        snaps = d.get("snapshots", d if isinstance(d, list) else [])
        print("  count:", len(snaps) if isinstance(snaps, list) else "?")
        for s in (snaps if isinstance(snaps, list) else [])[:50]:
            print("  SNAP", s.get("id"), s.get("name"), s.get("status"), s.get("createdAt", ""))
    except Exception as e:
        print("  parse err", e, r[:400])
