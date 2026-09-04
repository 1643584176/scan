# -*- coding: utf-8 -*-
import json, sys, time
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ
c, r = api("GET", "/v2/sandboxes/snapshots?teamId=%s&project=%s&limit=50" % (TEAM, PROJ))
if c != 200:
    print('list fail', c, (r or '')[:200])
    sys.exit(1)
snaps = json.loads(r).get('snapshots', [])
print('snapshots:', len(snaps))
for s in snaps:
    sid = s.get('id')
    print('  %s size=%d status=%s' % (sid, s.get('sizeBytes', 0), s.get('status')))
    c2, r2 = api("DELETE", "/v2/sandboxes/snapshots/%s?teamId=%s" % (sid, TEAM))
    print('  DEL -> %s %s' % (c2, (r2 or '')[:150]))
    time.sleep(1)
# 复查
c, r = api("GET", "/v2/sandboxes/snapshots?teamId=%s&project=%s&limit=50" % (TEAM, PROJ))
if c == 200:
    print('after: %d snapshots' % len(json.loads(r).get('snapshots', [])))
