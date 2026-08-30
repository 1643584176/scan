# -*- coding: utf-8 -*-
"""列出并删除全部快照"""
import sys, json, time
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
from vercel_driver import api, TEAM, PROJ

def list_snaps():
    c, r = api('GET', '/v2/sandboxes/snapshots?teamId=%s&project=%s&limit=50' % (TEAM, PROJ))
    if c != 200:
        print('list err', c, r[:300])
        return []
    return json.loads(r).get('snapshots', [])

snaps = list_snaps()
print('count:', len(snaps))
total = 0
while snaps:
    for s in snaps:
        sid = s['id']
        total += s.get('sizeBytes', 0)
        # 试 DELETE 端点变体
        for dpath in ['/v2/sandboxes/snapshots/%s?teamId=%s' % (sid, TEAM),
                      '/v2/sandboxes/snapshots/%s?teamId=%s&projectId=%s' % (sid, TEAM, PROJ),
                      '/v2/sandboxes/snapshots/%s?teamId=%s&project=%s' % (sid, TEAM, PROJ)]:
            c, r = api('DELETE', dpath)
            print('delete %s -> %d %s' % (sid, c, r[:150].replace('\n', ' ')))
            if c == 200:
                break
            time.sleep(0.3)
        time.sleep(0.3)
    snaps = list_snaps()
    print('remaining:', len(snaps))
print('total size freed:', total)
