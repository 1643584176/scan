# -*- coding: utf-8 -*-
"""清理全部沙箱释放快照配额"""
import sys, json, time
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
from vercel_driver import api, TEAM, PROJ

c, r = api('GET', '/v2/sandboxes?teamId=%s&project=%s&limit=50' % (TEAM, PROJ))
print('list:', c)
if c == 200:
    d = json.loads(r)
    boxes = d.get('sandboxes', d if isinstance(d, list) else [])
    if isinstance(d, dict) and 'sandboxes' in d:
        boxes = d['sandboxes']
    print('count:', len(boxes))
    for b in boxes:
        name = b.get('name', b.get('id', '?'))
        cc, rr = api('DELETE', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (name, TEAM, PROJ))
        print('delete %s -> %d %s' % (name, cc, rr[:100]))
        time.sleep(0.5)
else:
    print(r[:500])
