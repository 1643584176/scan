# -*- coding: utf-8 -*-
"""快照列表 400 根因对照: api_raw vs api x limit=50 vs 100 (2x2)"""
import json, sys, urllib.request, urllib.error
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TOKEN, TEAM, PROJ

def api_raw(method, path, timeout=60):
    req = urllib.request.Request('https://api.vercel.com' + path, method=method)
    req.add_header('Authorization', 'Bearer ' + TOKEN)
    try:
        with urllib.request.urlopen(req, data=None, timeout=timeout) as r:
            return r.status, r.read().decode(errors='replace')[:200]
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode(errors='replace')[:200]
    except Exception as e:
        return -1, 'EXC %s' % str(e)[:120]

cases = [
    ('api_raw  + limit=50 ', lambda: api_raw('GET', '/v2/sandboxes/snapshots?teamId=%s&project=%s&limit=50' % (TEAM, PROJ))),
    ('api_raw  + limit=100', lambda: api_raw('GET', '/v2/sandboxes/snapshots?teamId=%s&project=%s&limit=100' % (TEAM, PROJ))),
    ('api()    + limit=50 ', lambda: api('GET', '/v2/sandboxes/snapshots?teamId=%s&project=%s&limit=50' % (TEAM, PROJ))),
    ('api()    + limit=100', lambda: api('GET', '/v2/sandboxes/snapshots?teamId=%s&project=%s&limit=100' % (TEAM, PROJ))),
]
for tag, fn in cases:
    try:
        c, r = fn()
        print('[%s] -> %d %s' % (tag, c, (r or '')[:120].replace('\n', ' ')), flush=True)
    except Exception as e:
        print('[%s] -> EXC %s' % (tag, str(e)[:100]), flush=True)
