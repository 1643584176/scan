# -*- coding: utf-8 -*-
"""列出沙箱 + 删除所有 fwtest*"""
import sys, time, json
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, r'D:\scan\skills\non-traditional-vuln-hunting')
from fw_driver import api, TEAM, PROJ

c, r = api("GET", "/v2/sandboxes?teamId=%s&project=%s&limit=50" % (TEAM, PROJ))
print("list:", c, r[:4000])
try:
    d = json.loads(r)
    names = [sb.get("name") for sb in d.get("sandboxes", [])]
    print("names:", names)
    for n in names:
        if n and n.startswith("fwtest"):
            c2, r2 = api("DELETE", "/v2/sandboxes/%s?teamId=%s&projectId=%s" % (n, TEAM, PROJ))
            print("del", n, c2, r2[:200])
            time.sleep(1)
except Exception as e:
    print("parse exc", e)
print("done")
