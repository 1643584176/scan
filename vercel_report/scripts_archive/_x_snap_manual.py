# -*- coding: utf-8 -*-
"""手动快照面 (v45g)
P1: POST /sessions/{sid}/snapshot 是否停止 sandbox? currentSnapshotId 是否更新?
P2: 手动快照跨租户 (victim 对 attacker session 创建快照) -> 404?
P3: GET /v2/sandboxes/snapshots/{id} 响应字段 (是否有下载链接/敏感数据?)
P4: PATCH network-policy / snapshot body 参数变体"""
import json, sys, time, urllib.request, urllib.error
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TOKEN, TEAM, PROJ

NAME = 'snap45'
TEAM_V = 'team_jnske5hDpDfj9eDG2PAfDqWf'
PROJ_V = 'prj_LX0QDsEAlWA0uRZvVTunSef3lllF'

def load_token(path):
    for ln in open(path, encoding='utf-8'):
        if ln.startswith('authorization=Bearer '):
            return ln.split('Bearer ')[1].strip()
    raise RuntimeError('no token in ' + path)

TOK_V = load_token(r'F:\scan\vercel_cookies2.txt')

def api_tok(tok, method, path, body=None, timeout=90):
    req = urllib.request.Request('https://api.vercel.com' + path, method=method)
    req.add_header('Authorization', 'Bearer ' + tok)
    req.add_header('Content-Type', 'application/json')
    data = json.dumps(body).encode() if body is not None else None
    try:
        with urllib.request.urlopen(req, data=data, timeout=timeout) as r:
            return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:400]
    except Exception as e:
        return -1, 'EXC %s' % e

def mk():
    api("DELETE", "/v2/sandboxes/%s?teamId=%s&projectId=%s" % (NAME, TEAM, PROJ))
    time.sleep(3)
    for attempt in range(8):
        c, r = api("POST", "/v4/sandboxes?teamId=%s" % TEAM, {"projectId": PROJ, "name": NAME}, 60)
        if c == 429:
            print('[create] 429 retry %d' % (attempt + 1), flush=True)
            time.sleep(20)
            continue
        break
    print('[create] -> %s' % c, flush=True)
    if c != 200:
        sys.exit(1)
    return json.loads(r)['sandbox']['currentSessionId']

def get_state(tag):
    c, r = api('GET', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (NAME, TEAM, PROJ))
    try:
        d = json.loads(r)
        sb = d.get('sandbox', {})
        print('[%s] status=%s snap=%s' % (tag, sb.get('status'), sb.get('currentSnapshotId')), flush=True)
    except Exception as e:
        print('[%s ERR] %d %s' % (tag, c, (r or '')[:150]), flush=True)

if __name__ == '__main__':
    sid = mk()
    print('sid =', sid, flush=True)
    time.sleep(10)
    get_state('fresh')

    print('=== P1: 手动快照行为 ===', flush=True)
    c, r = api('POST', '/v2/sandboxes/sessions/%s/snapshot?teamId=%s' % (sid, TEAM), {}, timeout=90)
    print('[snapshot] -> %d %s' % (c, (r or '')[:300]), flush=True)
    snap = None
    try:
        snap = json.loads(r)['snapshot']['id']
        print('snap id =', snap, flush=True)
    except Exception:
        pass
    get_state('after-manual-snap')

    print('=== P3: GET 快照响应 ===', flush=True)
    if snap:
        c, r = api('GET', '/v2/sandboxes/snapshots/%s?teamId=%s' % (snap, TEAM))
        print('[GET snap] -> %d %s' % (c, (r or '')[:600]), flush=True)
        c, r = api('GET', '/v2/sandboxes/snapshots/%s?teamId=%s&projectId=%s' % (snap, TEAM, PROJ))
        print('[GET snap+proj] -> %d %s' % (c, (r or '')[:600]), flush=True)

    print('=== P2: 手动快照跨租户 ===', flush=True)
    c, r = api_tok(TOK_V, 'POST', '/v2/sandboxes/sessions/%s/snapshot?teamId=%s' % (sid, TEAM_V), {}, timeout=90)
    print('[victim snap] -> %d %s' % (c, (r or '')[:200]), flush=True)
    if snap:
        c, r = api_tok(TOK_V, 'GET', '/v2/sandboxes/snapshots/%s?teamId=%s' % (snap, TEAM_V), timeout=90)
        print('[victim get snap] -> %d %s' % (c, (r or '')[:200]), flush=True)

    print('=== P4: PATCH network-policy / snapshot body ===', flush=True)
    c, r = api('PATCH', '/v2/sandboxes/sessions/%s/network-policy?teamId=%s' % (sid, TEAM), {"mode": "deny-all"}, 30)
    print('[PATCH policy] -> %d %s' % (c, (r or '')[:150]), flush=True)
    c, r = api('POST', '/v2/sandboxes/sessions/%s/snapshot?teamId=%s' % (sid, TEAM), {"name": "custom45", "keep": 5}, 60)
    print('[snap body] -> %d %s' % (c, (r or '')[:200]), flush=True)
    c, r = api('GET', '/v2/sandboxes/sessions/%s/snapshots?teamId=%s' % (sid, TEAM))
    print('[list session snaps] -> %d %s' % (c, (r or '')[:200]), flush=True)
    c, r = api('GET', '/v2/sandboxes/%s/snapshots?teamId=%s&projectId=%s' % (NAME, TEAM, PROJ))
    print('[list sandbox snaps] -> %d %s' % (c, (r or '')[:400]), flush=True)

    api("DELETE", "/v2/sandboxes/%s?teamId=%s&projectId=%s" % (NAME, TEAM, PROJ))
    print('CLEANED', flush=True)
