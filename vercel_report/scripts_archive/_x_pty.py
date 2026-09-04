# -*- coding: utf-8 -*-
"""PTY 协议探索 + 23456 端口 (v46g)
P1: JSON 消息变体 (input/data/cmd) -> PTY 响应?
P2: resize/init 消息
P3: guest 内 23456 服务探测 (pprof/metrics/healthz)
P4: 完全无 token 的 wss (无 query) -> 401 确认
P5: PTY 权限 (whoami/uid)"""
import base64, json, socket, ssl, struct, sys, time, urllib.request, urllib.error, re
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, cmd, TOKEN, TEAM, PROJ

NAME = 'ws46g'

def api_raw(method, path, body=None, ctype='application/json', timeout=120):
    req = urllib.request.Request('https://api.vercel.com' + path, method=method)
    req.add_header('Authorization', 'Bearer ' + TOKEN)
    if ctype:
        req.add_header('Content-Type', ctype)
    data = json.dumps(body).encode() if body is not None else None
    try:
        with urllib.request.urlopen(req, data=data, timeout=timeout) as r:
            return r.status, r.read().decode(errors='replace')[:1500]
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode(errors='replace')[:1500]
    except Exception as e:
        return -1, 'EXC %s' % e

class WS:
    def __init__(self, host, path, token=None, t=10):
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        self.s = ctx.wrap_socket(socket.create_connection((host, 443), timeout=t), server_hostname=host)
        key = base64.b64encode(b'0123456789abcdef').decode()
        q = '?token=' + token if token else ''
        hdr = ('GET %s%s HTTP/1.1\r\nHost: %s\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n'
               'Sec-WebSocket-Key: %s\r\nSec-WebSocket-Version: 13\r\n\r\n' % (path, q, host, key))
        self.s.sendall(hdr.encode())
        self.s.settimeout(t)
        resp = b''
        while b'\r\n\r\n' not in resp:
            ch = self.s.recv(4096)
            if not ch:
                break
            resp += ch
        self.resp = resp
        if b'101' not in resp.split(b'\r\n')[0]:
            raise RuntimeError('handshake: %r' % resp[:150])

    def send(self, data: bytes):
        mask = b'\x01\x02\x03\x04'
        masked = bytes(b ^ mask[i % 4] for i, b in enumerate(data))
        header = bytes([0x81])
        n = len(masked)
        if n < 126:
            header += bytes([0x80 | n])
        elif n < 65536:
            header += bytes([0x80 | 126]) + struct.pack('>H', n)
        else:
            header += bytes([0x80 | 127]) + struct.pack('>Q', n)
        self.s.sendall(header + mask + masked)

    def recv(self, t=5):
        self.s.settimeout(t)
        try:
            h = self.s.recv(2)
        except socket.timeout:
            return None, 'TIMEOUT'
        except Exception as e:
            return None, 'ERR %s' % e
        if len(h) < 2:
            return None, 'EOF'
        opcode = h[0] & 0x0F
        n = h[1] & 0x7F
        if n == 126:
            n = struct.unpack('>H', self.s.recv(2))[0]
        elif n == 127:
            n = struct.unpack('>Q', self.s.recv(8))[0]
        payload = b''
        while len(payload) < n:
            ch = self.s.recv(n - len(payload))
            if not ch:
                break
            payload += ch
        return opcode, payload

    def close(self):
        try:
            self.s.close()
        except Exception:
            pass

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
    api("DELETE", "/v2/sandboxes/%s?teamId=%s&projectId=%s" % (NAME, TEAM, PROJ))
    time.sleep(3)
    for attempt in range(8):
        c, r = api("POST", "/v4/sandboxes?teamId=%s" % TEAM, {"projectId": PROJ, "name": NAME}, 60)
        if c == 429:
            print('[create] 429 retry', flush=True)
            time.sleep(20)
            continue
        break
    if c != 200:
        sys.exit(1)
    sid = json.loads(r)['sandbox']['currentSessionId']
    print('sid =', sid, flush=True)
    time.sleep(10)

    c, r = api_raw('POST', '/v2/sandboxes/sessions/%s/interactive?teamId=%s' % (sid, TEAM), {})
    url = tok = None
    try:
        d = json.loads(r)
        url, tok = d.get('url'), d.get('token')
    except Exception:
        pass
    m = re.match(r'wss://([^/]+)(/.*)', url)
    host, path = m.group(1), m.group(2)
    print('host=%s' % host, flush=True)

    print('=== P4: 完全无 token ===', flush=True)
    try:
        ws = WS(host, path, None)
        print('[no token] -> %s' % ws.resp.split(b'\r\n')[0].decode(), flush=True)
        ws.close()
    except Exception as e:
        print('[no token] -> ERR %s' % str(e)[:100], flush=True)

    print('=== P1/P2: PTY 协议消息变体 ===', flush=True)
    msgs = [
        ('json-input', b'{"type":"input","data":"whoami\\n"}'),
        ('json-cmd', b'{"cmd":"whoami"}'),
        ('raw-whoami', b'whoami'),
        ('json-shell', b'{"type":"shell","command":"whoami"}'),
        ('json-data', b'{"data":"whoami\\n"}'),
        ('resize', b'{"type":"resize","cols":80,"rows":24}'),
        ('json-pty', b'{"type":"pty","data":"whoami\\n"}'),
        ('json-run', b'{"type":"run","cmd":"whoami"}'),
    ]
    for tag, msg in msgs:
        try:
            ws = WS(host, path, tok)
            ws.send(msg)
            got = []
            for _ in range(2):
                op, payload = ws.recv(t=3)
                got.append('%s:%r' % (op, payload[:120]))
                if op is None:
                    break
            print('[%s] -> %s' % (tag, ' | '.join(got)), flush=True)
            ws.close()
        except Exception as e:
            print('[%s] -> ERR %s' % (tag, str(e)[:80]), flush=True)
        time.sleep(0.8)

    print('=== P3: guest 内 23456 探测 ===', flush=True)
    b64 = base64.b64encode(
        b'for p in / /healthz /metrics /debug/pprof/ /api /v1 /version /info; do '
        b'echo "== $p"; curl -s --max-time 2 http://127.0.0.1:23456$p 2>&1 | head -3; done; '
        b'echo "== 26661"; curl -s --max-time 2 http://127.0.0.1:26661/ 2>&1 | head -3').decode()
    c, r = cmd(sid, 'sh', ['-c', 'echo %s | base64 -d | sh' % b64], timeout_ms=40000)
    print('[probe] %s' % parse_data(r).strip()[:800], flush=True)

    api("DELETE", "/v2/sandboxes/%s?teamId=%s&projectId=%s" % (NAME, TEAM, PROJ))
    print('CLEANED', flush=True)
