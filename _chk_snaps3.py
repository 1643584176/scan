# -*- coding: utf-8 -*-
"""清理 created 状态快照 (v45d/v45d3 测试产生)
注意: GET list 的 limit 上限 50 (服务端校验, limit=100 会 400 "limit should be <= 50")"""
import json, sys, time, urllib.request, urllib.error
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import TOKEN, TEAM, PROJ

def api_raw(method, path, timeout=60, maxlen=20000):
    req = urllib.request.Request('https://api.vercel.com' + path, method=method)
    req.add_header('Authorization', 'Bearer ' + TOKEN)
    try:
        with urllib.request.urlopen(req, data=None, timeout=timeout) as r:
            return r.status, r.read().decode(errors='replace')[:maxlen]
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode(errors='replace')[:maxlen]
    except Exception as e:
        return -1, 'EXC %s' % str(e)[:120]

for i in range(5):
    try:
        c, r = api_raw('GET', '/v2/sandboxes/snapshots?teamId=%s&project=%s&limit=50' % (TEAM, PROJ))
        print('[list] ->', c, flush=True)
        d = json.loads(r)
        snaps = d.get('snapshots') or d.get('data') or []
        n = 0
        for s in snaps:
            sid = s.get('id')
            st = s.get('status')
            sz = s.get('sizeBytes')
            print('  %s status=%s size=%s' % (sid, st, sz), flush=True)
            if st == 'created':
                for j in range(3):
                    try:
                        c2, r2 = api_raw('DELETE', '/v2/sandboxes/snapshots/%s?teamId=%s&project=%s' % (sid, TEAM, PROJ))
                        print('    [del] -> %d %s' % (c2, (r2 or '')[:80]), flush=True)
                        break
                    except Exception as e:
                        print('    [del EXC] %s' % str(e)[:100], flush=True)
                        time.sleep(10)
                n += 1
                time.sleep(1)
        print('deleted %d created snaps' % n, flush=True)
        break
    except Exception as e:
        print('[try%d EXC] %s' % (i + 1, str(e)[:120]), flush=True)
        time.sleep(15)
print('DONE', flush=True)
