# -*- coding: utf-8 -*-
"""v51g: GET /v2/sandboxes/snapshots/tree 快照树端点
T1: 自己快照树 (功能)
T2: 跨租户: attacker 读 victim 快照树
T3: 无 snapshotId / 不存在的 id"""
import json, sys, time, urllib.request, urllib.error
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, cmd, TOKEN, TEAM, PROJ

TEAM_V = 'team_jnske5hDpDfj9eDG2PAfDqWf'
PROJ_V = 'prj_LX0QDsEAlWA0uRZvVTunSef3lllF'

def load_token(path):
    for ln in open(path, encoding='utf-8'):
        if ln.startswith('authorization=Bearer '):
            return ln.split('Bearer ')[1].strip()
    raise RuntimeError('no token in ' + path)

TOK_V = load_token(r'F:\scan\vercel_cookies2.txt')

def api_raw(method, path, body=None, tok=None, timeout=180, maxlen=200000):
    req = urllib.request.Request('https://api.vercel.com' + path, method=method)
    req.add_header('Authorization', 'Bearer ' + (tok or TOKEN))
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
    # 准备: 自己快照
    api_raw('DELETE', '/v2/sandboxes/tree51?teamId=%s&projectId=%s' % (TEAM, PROJ))
    time.sleep(2)
    c, r = api_raw('POST', '/v4/sandboxes?teamId=%s' % TEAM, {"projectId": PROJ, "name": 'tree51'})
    if c != 200:
        print('create failed', r[:200], flush=True)
        sys.exit(1)
    sid = json.loads(r)['sandbox']['currentSessionId']
    time.sleep(8)
    c2, r2 = api_raw('POST', '/v2/sandboxes/sessions/%s/snapshot?teamId=%s' % (sid, TEAM), {}, timeout=180)
    print('[mk snap] -> %d %s' % (c2, (r2 or '')[:120]), flush=True)
    try:
        snap_own = json.loads(r2)['snapshot']['id']
    except Exception:
        snap_own = None
    time.sleep(5)

    # victim 快照
    api_raw('DELETE', '/v2/sandboxes/vtree51?teamId=%s&projectId=%s' % (TEAM_V, PROJ_V), tok=TOK_V)
    time.sleep(2)
    c, r = api_raw('POST', '/v4/sandboxes?teamId=%s' % TEAM_V,
                   {"projectId": PROJ_V, "name": 'vtree51'}, tok=TOK_V)
    print('[victim create] -> %d' % c, flush=True)
    snap_v = None
    if c == 200:
        vsid = json.loads(r)['sandbox']['currentSessionId']
        time.sleep(8)
        c2, r2 = api_raw('POST', '/v2/sandboxes/sessions/%s/snapshot?teamId=%s' % (vsid, TEAM_V), {}, tok=TOK_V, timeout=180)
        print('[victim snap] -> %d %s' % (c2, (r2 or '')[:120]), flush=True)
        try:
            snap_v = json.loads(r2)['snapshot']['id']
        except Exception:
            pass
        time.sleep(5)

    print('snap_own =', snap_own, flush=True)
    print('snap_v   =', snap_v, flush=True)

    print('=== T1: 自己快照树 ===', flush=True)
    c3, r3 = api_raw('GET', '/v2/sandboxes/snapshots/tree?project=%s&snapshotId=%s' % (PROJ, snap_own))
    print('[own tree] -> %d %s' % (c3, (r3 or '')[:400]), flush=True)

    print('=== T2: 跨租户读 victim 快照树 ===', flush=True)
    c4, r4 = api_raw('GET', '/v2/sandboxes/snapshots/tree?project=%s&snapshotId=%s' % (PROJ_V, snap_v))
    print('[victim tree attacker tok] -> %d %s' % (c4, (r4 or '')[:400]), flush=True)
    c5, r5 = api_raw('GET', '/v2/sandboxes/snapshots/tree?project=%s&snapshotId=%s' % (PROJ, snap_v))
    print('[victim snap own project] -> %d %s' % (c5, (r5 or '')[:400]), flush=True)

    print('=== T3: 无/假 snapshotId ===', flush=True)
    c6, r6 = api_raw('GET', '/v2/sandboxes/snapshots/tree?project=%s' % PROJ)
    print('[no snapshotId] -> %d %s' % (c6, (r6 or '')[:300]), flush=True)
    c7, r7 = api_raw('GET', '/v2/sandboxes/snapshots/tree?project=%s&snapshotId=snap_fake123' % PROJ)
    print('[fake snapshotId] -> %d %s' % (c7, (r7 or '')[:300]), flush=True)

    # 清理
    api_raw('DELETE', '/v2/sandboxes/tree51?teamId=%s&projectId=%s' % (TEAM, PROJ))
    api_raw('DELETE', '/v2/sandboxes/vtree51?teamId=%s&projectId=%s' % (TEAM_V, PROJ_V), tok=TOK_V)
    for s in [snap_own]:
        if s:
            api_raw('DELETE', '/v2/sandboxes/snapshots/%s?teamId=%s&project=%s' % (s, TEAM, PROJ))
    for s in [snap_v]:
        if s:
            api_raw('DELETE', '/v2/sandboxes/snapshots/%s?teamId=%s&project=%s' % (s, TEAM_V, PROJ_V), tok=TOK_V)
    print('DONE', flush=True)
