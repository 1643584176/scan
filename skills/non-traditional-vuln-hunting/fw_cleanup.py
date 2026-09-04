# -*- coding: utf-8 -*-
"""清理所有 fwtest* 沙箱,释放快照存储配额"""
import sys, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, r'D:\scan\skills\non-traditional-vuln-hunting')
from fw_driver import api, TEAM, PROJ

if __name__ == "__main__":
    # list sandboxes
    c, r = api("GET", "/v2/sandboxes?teamId=%s&projectId=%s&limit=100" % (TEAM, PROJ))
    print("list:", c, r[:3000])
    names = []
    try:
        import json
        d = json.loads(r)
        for sb in d.get("sandboxes", []):
            names.append(sb.get("name"))
    except Exception as e:
        print("parse exc", e)
    print("names:", names)
    # delete all fwtest*
    for n in names:
        if n and n.startswith("fwtest"):
            c2, r2 = api("DELETE", "/v2/sandboxes/%s?teamId=%s&projectId=%s" % (n, TEAM, PROJ))
            print("del", n, c2, r2[:200])
            time.sleep(1)
    print("done")
