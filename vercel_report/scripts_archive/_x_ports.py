# -*- coding: utf-8 -*-
"""端口路由面 + wss token 传递 (v46e)
P1: 创建带 ports 的 sandbox -> routes/subdomain -> 公网访问 (无鉴权?)
P2: wss token 传递方式 (query / Sec-WebSocket-Protocol / cookie)
P3: routes 在 session 响应中的结构"""
import base64, json, socket, ssl, sys, time, urllib.request, urllib.error, re
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, cmd, TOKEN, TEAM, PROJ

NAME = 'port46'

def api_raw(method, path, body=None, ctype='application/json', headers=None, timeout=120):
    req = urllib.request.Request('https://api.vercel.com' + path, method=method)
    req.add_header('Authorization', 'Bearer ' + TOKEN)
    if ctype:
        req.add_header('Content-Type', ctype)
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    data = body if isinstance(body, bytes) else (json.dumps(body).encode() if body is not None else None)
    try:
        with urllib.request.urlopen(req, data=data, timeout=timeout) as r:
            return r.status, r.read().decode(errors='replace')[:3000]
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode(errors='replace')[:3000]
    except Exception as e:
        return -1, 'EXC %s' % e

def parse_data(r):
    out = ''
    for line in r.splitlines():
        if '"data"' in line:
            try:
                out += json.loads(line).get('data', '')
            except Exception:
                pass
    return out

def ws_probe(host, path, token=None, subproto=None, t=6):
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
        if subproto:
            hdr += 'Sec-WebSocket-Protocol: %s\r\n' % subproto
        hdr += '\r\n'
        s.sendall(hdr.encode())
        s.settimeout(t)
        d = s.recv(1024)
        s.close()
        return repr(d[:300])
    except Exception as e:
        return 'EXC %s' % e

if __name__ == '__main__':
    # 清理旧 sandbox
    api("DELETE", "/v2/sandboxes/%s?teamId=%s&projectId=%s" % (NAME, TEAM, PROJ))
    time.sleep(3)
    print('=== P1: 创建带 ports 的 sandbox ===', flush=True)
    c, r = api_raw('POST', '/v4/sandboxes?teamId=%s' % TEAM,
                   {"projectId": PROJ, "name": NAME, "ports": [3000]}, timeout=120)
    print('[create ports] -> %d %s' % (c, (r or '')[:1500]), flush=True)
    sid = None
    try:
        d = json.loads(r)
        sid = d['sandbox']['currentSessionId']
        print('sid =', sid, flush=True)
    except Exception as e:
        print('parse err', e, flush=True)
    if not sid:
        sys.exit(1)
    time.sleep(10)
    # 看 session 响应的 routes
    c, r = api_raw('GET', '/v2/sandboxes/sessions/%s?teamId=%s' % (sid, TEAM))
    print('[session] -> %d %s' % (c, (r or '')[:2000]), flush=True)
    routes = []
    try:
        d = json.loads(r)
        routes = d.get('session', {}).get('routes') or d.get('routes') or []
        print('[routes]', json.dumps(routes), flush=True)
    except Exception:
        pass
    # guest 内起 HTTP 服务
    b64 = base64.b64encode(
        b'python3 -c "import http.server, socketserver; '
        b'h= http.server.SimpleHTTPRequestHandler; '
        b'class H(h):\n def do_GET(self):\n  self.send_response(200); self.send_header(\'Content-Type\',\'text/plain\'); self.end_headers(); self.wfile.write(b\'PORT_3000_MARKER\')'
        b'\nsocketserver.TCPServer((\'0.0.0.0\', 3000), H).serve_forever()" >/tmp/httpd.log 2>&1 &').decode()
    c, r = cmd(sid, 'sh', ['-c', 'echo %s | base64 -d | sh' % b64], timeout_ms=15000)
    print('[start httpd] -> %d' % c, flush=True)
    time.sleep(3)
    b64 = base64.b64encode(b'curl -s --max-time 3 http://127.0.0.1:3000/ ; ss -tlnp | grep 3000').decode()
    c, r = cmd(sid, 'sh', ['-c', 'echo %s | base64 -d | sh' % b64], timeout_ms=15000)
    print('[guest check] %s' % parse_data(r).strip()[:150], flush=True)

    # 公网访问 routes
    for rt in routes:
        sub = rt.get('subdomain')
        port = rt.get('port')
        if not sub:
            continue
        host = '%s.vercel.run' % sub
        print('--- route: %s -> %s:%s' % (host, port, rt), flush=True)
        try:
            ips = socket.getaddrinfo(host, 443)
            print('[dns]', sorted(set(i[4][0] for i in ips)), flush=True)
        except Exception as e:
            print('[dns ERR]', e, flush=True)
        try:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            raw = socket.create_connection((host, 443), timeout=8)
            s = ctx.wrap_socket(raw, server_hostname=host)
            s.sendall(('GET / HTTP/1.1\r\nHost: %s\r\nConnection: close\r\n\r\n' % host).encode())
            s.settimeout(8)
            d = b''
            while True:
                try:
                    ch = s.recv(4096)
                except socket.timeout:
                    break
                if not ch:
                    break
                d += ch
                if len(d) > 800:
                    break
            s.close()
            print('[public %s] %s' % (host, repr(d[:400])), flush=True)
        except Exception as e:
            print('[public EXC] %s' % e, flush=True)

    print('=== P2: wss token 传递 ===', flush=True)
    c, r = api_raw('POST', '/v2/sandboxes/sessions/%s/interactive?teamId=%s' % (sid, TEAM), {})
    url = tok = None
    try:
        d = json.loads(r)
        url, tok = d.get('url'), d.get('token')
    except Exception:
        pass
    print('[interactive] url=%s' % url, flush=True)
    if url:
        m = re.match(r'wss://([^/]+)(/.*)', url)
        host, path = m.group(1), m.group(2)
        print('[wss query token] %s' % ws_probe(host, path + '?token=' + tok, None), flush=True)
        print('[wss subproto token] %s' % ws_probe(host, path, None, subproto='bearer ' + tok), flush=True)
        print('[wss subproto raw] %s' % ws_probe(host, path, None, subproto=tok), flush=True)
        print('[wss auth+query] %s' % ws_probe(host, path + '?token=' + tok, tok), flush=True)
        # 看 401 完整响应
        try:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            raw = socket.create_connection((host, 443), timeout=6)
            s = ctx.wrap_socket(raw, server_hostname=host)
            key = 'dGhlIHNhbXBsZSBub25jZQ=='
            hdr = 'GET %s HTTP/1.1\r\nHost: %s\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Key: %s\r\nSec-WebSocket-Version: 13\r\nAuthorization: Bearer %s\r\n\r\n' % (path, host, key, tok)
            s.sendall(hdr.encode())
            s.settimeout(6)
            d = s.recv(2048)
            s.close()
            print('[wss full resp] %s' % repr(d[:500]), flush=True)
        except Exception as e:
            print('[wss full EXC] %s' % e, flush=True)

    api("DELETE", "/v2/sandboxes/%s?teamId=%s&projectId=%s" % (NAME, TEAM, PROJ))
    print('CLEANED', flush=True)
