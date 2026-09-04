# -*- coding: utf-8 -*-
"""v45d6: resume 后用新 sessionId 验证数据 (快照前数据存在? 快照后写入不存在?)"""
import base64, json, sys, time
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, cmd, TOKEN, TEAM, PROJ

NAME = 'snapresume49'

def api_raw(method, path, body=None, timeout=120):
    import urllib.request, urllib.error
    req = urllib.request.Request('https://api.vercel.com' + path, method=method)
    req.add_header('Authorization', 'Bearer ' + TOKEN)
    req.add_header('Content-Type', 'application/json')
    data = json.dumps(body).encode() if body is not None else None
    try:
        with urllib.request.urlopen(req, data=data, timeout=timeout) as r:
            return r.status, r.read().decode(errors='replace')[:800]
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode(errors='replace')[:800]
    except Exception as e:
        return -1, 'EXC %s' % str(e)[:120]

def parse_data(r):
    out = ''
    for line in r.splitlines():
        if '"data"' in line:
            try:
                out += json.loads(line).get('data', '')
            except Exception:
                pass
    return out

# 先 resume (sandbox 可能已被清理, 若无则创建+snapshot+resume)
c, r = api('GET', '/v2/sandboxes/%s?teamId=%s&projectId=%s&resume=true' % (NAME, TEAM, PROJ), timeout=120)
print('[resume] -> %d %s' % (c, (r or '')[:200]), flush=True)
try:
    d = json.loads(r)
    new_sid = d['sandbox']['currentSessionId']
    snap_id = d['sandbox'].get('currentSnapshotId')
    print('new sid =', new_sid, 'snap =', snap_id, flush=True)
except Exception as e:
    print('parse err', e, flush=True)
    sys.exit(1)

time.sleep(10)
b64 = base64.b64encode(b'echo "== snap_data (before):"; cat /tmp/snap_data.txt 2>&1; echo "== snap_data2 (after):"; cat /tmp/snap_data2.txt 2>&1; echo "== uid:"; id -u').decode()
c, r = cmd(new_sid, 'sh', ['-c', 'echo %s | base64 -d | sh' % b64], timeout_ms=20000)
print('[verify new-sid] -> %d' % c, flush=True)
print(parse_data(r).strip()[:400], flush=True)

api("DELETE", "/v2/sandboxes/%s?teamId=%s&projectId=%s" % (NAME, TEAM, PROJ))
print('CLEANED', flush=True)
