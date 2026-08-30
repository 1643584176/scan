# -*- coding: utf-8 -*-
"""interactive 面深挖 (v46d)
P1: wss URL 公网可达性 (DNS + TCP 443)
P2: interactive 多次调用 URL/token 变化? token 复用?
P3: interactive 跨租户 (victim 调 attacker)
P4: guest 内 23456 端口是什么
P5: kill signal=9
P6: 无 token / 假 token 连 wss (握手探测)"""
import base64, json, socket, ssl, struct, sys, time, urllib.request, urllib.error, os, re
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, cmd, TOKEN, TEAM, PROJ

NAME = 'sdk46d'
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
            return r.status, r.read().decode(errors='replace')[:1000]
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode(errors='replace')[:1000]
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

def ws_probe(host, path, token=None, t=6):
    """WebSocket 握手探测: 返回握手响应或错误"""
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        raw = socket.create_connection((host, 443), timeout=t)
        s = ctx.wrap_socket(raw, server_hostname=host)
        key = 'dGhlIHNhbXBsZSBub25jZQ=='
        hdr = 'GET %s HTTP/1.1\r\nHost: %s\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Key: %s\r\nSec-WebSocket-Version: 13\r\n' % (path, host, key)
        if token:
            hdr += 'Authorization: Bearer %s\r\n' % token
        hdr += '\r\n'
        s.sendall(hdr.encode())
        s.settimeout(t)
        d = s.recv(1024)
        s.close()
        return repr(d[:200])
    except Exception as e:
        return 'EXC %s' % e

if __name__ == '__main__':
    sid = mk()
    print('sid =', sid, flush=True)
    time.sleep(8)

    print('=== P1/P2: interactive 两次调用 ===', flush=True)
    url1 = tok1 = None
    c, r = api_raw('POST', '/v2/sandboxes/sessions/%s/interactive?teamId=%s' % (sid, TEAM), {})
    print('[int1] -> %d %s' % (c, (r or '')[:400]), flush=True)
    try:
        d = json.loads(r)
        url1, tok1 = d.get('url'), d.get('token')
    except Exception:
        pass
    time.sleep(2)
    c, r = api_raw('POST', '/v2/sandboxes/sessions/%s/interactive?teamId=%s' % (sid, TEAM), {})
    print('[int2] -> %d %s' % (c, (r or '')[:400]), flush=True)
    url2 = tok2 = None
    try:
        d = json.loads(r)
        url2, tok2 = d.get('url'), d.get('token')
    except Exception:
        pass
    print('[compare] url same=%s tok same=%s' % (url1 == url2, tok1 == tok2), flush=True)
    print('url1=%s' % url1, flush=True)
    print('url2=%s' % url2, flush=True)

    print('=== P3: interactive 跨租户 ===', flush=True)
    c, r = api_raw('POST', '/v2/sandboxes/sessions/%s/interactive?teamId=%s' % (sid, TEAM_V), {}, tok=TOK_V)
    print('[victim interactive] -> %d %s' % (c, (r or '')[:150]), flush=True)

    print('=== P4: guest 内 23456 ===', flush=True)
    b64 = base64.b64encode(b'curl -s --max-time 3 http://127.0.0.1:23456/ 2>&1 | head -5; echo ---; curl -s --max-time 3 http://127.0.0.1:26661/ 2>&1 | head -5').decode()
    c, r = cmd(sid, 'sh', ['-c', 'echo %s | base64 -d | sh' % b64], timeout_ms=20000)
    print('[local curl] %s' % parse_data(r).strip()[:300], flush=True)

    print('=== P1b: wss 公网可达性 ===', flush=True)
    if url1:
        m = re.match(r'wss://([^/]+)(/.*)', url1)
        host, path = m.group(1), m.group(2)
        print('host=%s path=%s' % (host, path), flush=True)
        try:
            ips = socket.getaddrinfo(host, 443)
            print('[dns] %s' % sorted(set(i[4][0] for i in ips)), flush=True)
        except Exception as e:
            print('[dns ERR] %s' % e, flush=True)
        print('[wss no-token] %s' % ws_probe(host, path, None), flush=True)
        print('[wss fake-token] %s' % ws_probe(host, path, 'FAKETOKEN123'), flush=True)
        if tok1:
            print('[wss real-token] %s' % ws_probe(host, path, tok1), flush=True)
        # HTTP 探测同一 host
        try:
            raw = socket.create_connection((host, 443), timeout=6)
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            s = ctx.wrap_socket(raw, server_hostname=host)
            s.sendall(b'GET / HTTP/1.1\r\nHost: ' + host.encode() + b'\r\nConnection: close\r\n\r\n')
            s.settimeout(6)
            d = s.recv(1024)
            s.close()
            print('[http root] %s' % repr(d[:200]), flush=True)
        except Exception as e:
            print('[http root EXC] %s' % e, flush=True)

    print('=== P5: kill signal=9 ===', flush=True)
    c, r = api_raw('POST', '/v2/sandboxes/sessions/%s/cmd?teamId=%s' % (sid, TEAM),
                   {"command": "sleep", "args": ["60"], "wait": False})
    cmd_id = None
    try:
        cmd_id = json.loads(r)['command']['id']
    except Exception:
        pass
    if cmd_id:
        c, r = api_raw('POST', '/v2/sandboxes/sessions/%s/cmd/%s/kill?teamId=%s' % (sid, cmd_id, TEAM), {"signal": 9})
        print('[kill 9] -> %d %s' % (c, (r or '')[:150]), flush=True)
        c, r = api_raw('GET', '/v2/sandboxes/sessions/%s/cmd/%s?teamId=%s' % (sid, cmd_id, TEAM))
        print('[get after] -> %d %s' % (c, (r or '')[:200]), flush=True)

    api("DELETE", "/v2/sandboxes/%s?teamId=%s&projectId=%s" % (NAME, TEAM, PROJ))
    print('CLEANED', flush=True)
