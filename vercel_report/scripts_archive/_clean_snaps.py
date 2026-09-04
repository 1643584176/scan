# -*- coding: utf-8 -*-
"""清理快照配额: 列出并删除全部快照"""
import sys, json, time
sys.path.insert(0, r'D:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ

c, r = api("GET", "/v2/sandboxes/snapshots?teamId=%s&project=%s&limit=50" % (TEAM, PROJ))
print('list:', c, r[:400])
try:
    snaps = json.loads(r).get('snapshots', [])
    print('count:', len(snaps))
    for s in snaps:
        c2, r2 = api("DELETE", "/v2/sandboxes/snapshots/%s?teamId=%s&project=%s" % (s['id'], TEAM, PROJ))
        print('del', s.get('id'), c2)
        time.sleep(0.3)
except Exception as e:
    print('ERR', e)
