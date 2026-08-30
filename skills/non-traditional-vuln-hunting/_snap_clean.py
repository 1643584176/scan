# -*- coding: utf-8 -*-
"""快照配额清理: 列出所有旧快照并删除, 释放 Hobby 5GB 配额"""
import json, sys, time
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ

c, r = api("GET", "/v2/sandboxes/snapshots?teamId=%s&project=%s&limit=50" % (TEAM, PROJ))
print("list snapshots:", c)
if c != 200:
    print(r[:800])
    sys.exit(1)
d = json.loads(r)
snaps = d.get("snapshots", [])
print("snapshot count:", len(snaps))
for sn in snaps:
    sid = sn.get("id") or sn.get("snapshotId") or sn.get("name")
    name = sn.get("name", "")
    st = sn.get("status", "")
    sz = sn.get("size", sn.get("sizeBytes", ""))
    print("  SNAP %s name=%s status=%s size=%s" % (sid, name, st, sz))

deleted = 0
for sn in snaps:
    sid = sn.get("id") or sn.get("snapshotId") or sn.get("name")
    if not sid:
        continue
    c2, r2 = api("DELETE", "/v2/sandboxes/snapshots/%s?teamId=%s&project=%s" % (sid, TEAM, PROJ))
    print("del %s: %d %s" % (sid, c2, r2[:150]))
    if c2 in (200, 204, 404):
        deleted += 1
    time.sleep(0.5)
print("deleted:", deleted)
