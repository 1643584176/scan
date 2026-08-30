# -*- coding: utf-8 -*-
"""列出当前沙箱, 判断配额占用"""
import sys, json
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
from vercel_driver import api, TEAM, PROJ

c, r = api("GET", "/v2/sandboxes?teamId=%s&project=%s&limit=50" % (TEAM, PROJ))
print("status:", c)
print("raw:", r[:1500])
try:
    j = json.loads(r)
    sbs = j.get('sandboxes', j if isinstance(j, list) else [])
    for s in sbs:
        print(s.get('name'), s.get('id'), s.get('status'), s.get('createdAt'))
    print('count:', len(sbs))
except Exception as e:
    print("parse err", e, r[:800])
