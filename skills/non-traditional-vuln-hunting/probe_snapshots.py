# -*- coding: utf-8 -*-
"""快照面探测: 列表/下载端点/字段结构"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ

# 1) 快照列表
c, r = api("GET", "/v2/sandboxes/snapshots?teamId=%s&project=%s&limit=50" % (TEAM, PROJ))
print("list snapshots:", c)
print(r[:2500])

# 2) 尝试单个快照 GET(需 id,先解析列表)
import json
if c == 200:
    try:
        d = json.loads(r)
        snaps = d.get("snapshots", [])
        print("snapshot count:", len(snaps))
        for sn in snaps[:3]:
            print("snap fields:", list(sn.keys()))
            print("snap:", json.dumps(sn)[:500])
            sid = sn.get("id") or sn.get("snapshotId") or sn.get("name")
            if sid:
                c2, r2 = api("GET", "/v2/sandboxes/snapshots/%s?teamId=%s&project=%s" % (sid, TEAM, PROJ))
                print("GET snapshot %s:" % sid, c2, r2[:400])
                break
    except Exception as e:
        print("parse err:", e)
