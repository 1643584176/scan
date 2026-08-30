# -*- coding: utf-8 -*-
"""列出当前 sandbox 并清理遗留"""
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
            return r.status, r.read().decode(errors='replace')[:3000]
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode(errors='replace')[:3000]
    except Exception as e:
        return -1, 'EXC %s' % str(e)[:150]

for i in range(5):
    try:
        c, r = api_raw('GET', '/v4/sandboxes?teamId=%s&projectId=%s&limit=50' % (TEAM, PROJ))
        print('[list] ->', c, flush=True)
        import json
        d = json.loads(r)
        names = []
        for sb in d.get('sandboxes', []):
            nm = sb.get('name')
            names.append(nm)
            print('  %s id=%s status=%s' % (nm, sb.get('id'), sb.get('status')), flush=True)
        for nm in names:
            if nm.startswith(('ws46g', 'sdk46', 'fsapi', 'ws46')):
                c2, _ = api_raw('DELETE', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (nm, TEAM, PROJ))
                print('[clean %s] -> %d' % (nm, c2), flush=True)
                time.sleep(1)
        break
    except Exception as e:
        print('[try%d EXC] %s' % (i + 1, str(e)[:120]), flush=True)
        time.sleep(15)
print('DONE', flush=True)
