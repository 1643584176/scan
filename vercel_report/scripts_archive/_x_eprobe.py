# -*- coding: utf-8 -*-
"""探测 stop / snapshot 创建端点"""
import json, sys, time
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
from vercel_driver import api, cmd, TEAM, PROJ

c, r = api('GET', '/v2/sandboxes/xatk1?teamId=%s&projectId=%s' % (TEAM, PROJ))
print('get xatk1:', c, flush=True)
sid = None
if c == 200:
    d = json.loads(r)
    sb = d.get('sandbox', {})
    print('status:', sb.get('status'), 'expiresAt:', sb.get('expiresAt'), 'snapshot:', sb.get('currentSnapshotId'), flush=True)
    print('routes:', json.dumps(d.get('routes', 'NONE')), flush=True)
    print('session.networkPolicy:', json.dumps(d.get('session', {}).get('networkPolicy', 'NONE')), flush=True)
    print('sandbox.networkPolicy:', json.dumps(sb.get('networkPolicy', 'NONE')), flush=True)
    sid = sb.get('currentSessionId')

# stop 端点探测
cands = [
    ('POST', '/v2/sandboxes/xatk1/stop?teamId=%s&projectId=%s' % (TEAM, PROJ), None),
    ('POST', '/v2/sandboxes/sessions/%s/stop?teamId=%s' % (sid, TEAM), None),
    ('POST', '/v2/sandboxes/xatk1/terminate?teamId=%s&projectId=%s' % (TEAM, PROJ), None),
    ('POST', '/v2/sandboxes/sessions/%s/terminate?teamId=%s' % (sid, TEAM), None),
    ('POST', '/v2/sandboxes/xatk1/snapshots?teamId=%s&projectId=%s' % (TEAM, PROJ), {}),
    ('POST', '/v2/sandboxes/snapshots?teamId=%s&project=%s' % (TEAM, PROJ), {'sandboxName': 'xatk1'}),
]
for m, p, b in cands:
    c, r = api(m, p, b)
    print('%s %s -> %d %s' % (m, p.split('?')[0][:60], c, r[:200].replace('\n', ' ')), flush=True)
    time.sleep(0.5)

print('=== ENDPOINT PROBE DONE ===', flush=True)
