# -*- coding: utf-8 -*-
"""v52e: CIDR 单独值 500 定位 (C2 的 500 触发条件)"""
import json, sys, urllib.request, urllib.error
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, cmd, TOKEN, TEAM, PROJ

def api_raw(method, path, body=None, timeout=120, maxlen=30000):
    req = urllib.request.Request('https://api.vercel.com' + path, method=method)
    req.add_header('Authorization', 'Bearer ' + TOKEN)
    req.add_header('Content-Type', 'application/json')
    data = json.dumps(body).encode() if body is not None else None
    try:
        with urllib.request.urlopen(req, data=data, timeout=timeout) as r:
            return r.status, r.read().decode(errors='replace')[:maxlen]
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode(errors='replace')[:maxlen]
    except Exception as e:
        return -1, 'EXC %s' % str(e)[:120]

if __name__ == '__main__':
    cases = [('A', ['0.0.0.0/1']), ('B', ['128.0.0.0/1']), ('C', ['0.0.0.0/0', '10.0.0.0/8']),
             ('D', ['0.0.0.0/2']), ('E', ['240.0.0.0/4']), ('F', ['255.255.255.255/32'])]
    for tag, cidrs in cases:
        api_raw('DELETE', '/v2/sandboxes/cx51?teamId=%s&projectId=%s' % (TEAM, PROJ))
        c, r = api_raw('POST', '/v4/sandboxes?teamId=%s' % TEAM,
                       {"projectId": PROJ, "name": 'cx51', "networkPolicy": {"mode": "custom", "allowedCIDRs": cidrs}})
        msg = ''
        try:
            d = json.loads(r)
            msg = d.get('error', {}).get('message', '')[:70]
        except Exception:
            msg = r[:70]
        print('[%s %s] -> %d %s' % (tag, cidrs, c, msg), flush=True)
        api_raw('DELETE', '/v2/sandboxes/cx51?teamId=%s&projectId=%s' % (TEAM, PROJ))
    print('DONE', flush=True)
