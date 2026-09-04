# -*- coding: utf-8 -*-
"""幂等清理遗留 sandbox"""
import sys, time, urllib.request, urllib.error
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TOKEN, TEAM, PROJ

def api_raw(method, path, body=None, timeout=60):
    req = urllib.request.Request('https://api.vercel.com' + path, method=method)
    req.add_header('Authorization', 'Bearer ' + TOKEN)
    req.add_header('Content-Type', 'application/json')
    data = None
    if body is not None:
        import json
        data = json.dumps(body).encode()
    try:
        with urllib.request.urlopen(req, data=data, timeout=timeout) as r:
            return r.status, r.read().decode(errors='replace')[:1000]
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode(errors='replace')[:1000]
    except Exception as e:
        return -1, 'EXC %s' % str(e)[:150]

for nm in ['ws46g', 'ws46g2', 'sdk46d', 'fsapi46', 'ws46h']:
    for i in range(3):
        try:
            c, r = api_raw('DELETE', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (nm, TEAM, PROJ))
            print('[del %s] -> %d %s' % (nm, c, (r or '')[:80]), flush=True)
            break
        except Exception as e:
            print('[del %s try%d EXC] %s' % (nm, i + 1, str(e)[:100]), flush=True)
            time.sleep(12)
    time.sleep(1)
print('DONE', flush=True)
