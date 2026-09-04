# -*- coding: utf-8 -*-
"""interactive WebSocket PTY 探索 (v46f)
P1: 连接 wss -> 服务器首帧 (协议格式)
P2: 发命令 -> 输出? (PTY 交互)
P3: PTY 权限 (whoami/id)
P4: 路径变体 (绕过 token 校验?)
P5: stop->resume 后 URL/token 生命周期"""
import base64, json, socket, ssl, struct, sys, time, urllib.request, urllib.error, re
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, cmd, TOKEN, TEAM, PROJ

NAME = 'ws46'

def api_raw(method, path, body=None, ctype='application/json', timeout=120):
    req = urllib.request.Request('https://api.vercel.com' + path, method=method)
    req.add_header('Authorization', 'Bearer ' + TOKEN)
    if ctype:
        req.add_header('Content-Type', ctype)
    data = json.dumps(body).encode() if body is not None else None
    try:
        with urllib.request.urlopen(req, data=data, timeout=timeout) as r:
            return r.status, r.read().decode(errors='replace')[:2000]
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode(errors='replace')[:2000]
    except Exception as e:
        return -1, 'EXC %s' % e

class WS:
    def __init__(self, host, path, token, t=10):
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
            raise RuntimeError('handshake failed: %r' % resp[:200])

    def send_text(self, text):
        data = text.encode()
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

    def recv_frame(self, t=8):
        self.s.settimeout(t)
        try:
            h = self.s.recv(2)
        except socket.timeout:
            return None, 'TIMEOUT'
        if len(h) < 2:
            return None, 'EOF'
        fin = h[0] & 0x80
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
    print('[create] -> %d' % c, flush=True)
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
    print('[int] url=%s' % url, flush=True)
    m = re.match(r'wss://([^/]+)(/.*)', url)
    host, path = m.group(1), m.group(2)
    print('host=%s path=%s tok=%s' % (host, path, tok[:8] + '...'), flush=True)

    print('=== P1: 连接 + 首帧 ===', flush=True)
    ws = WS(host, path, tok)
    print('[conn] %s' % ws.resp.split(b'\r\n')[0].decode(), flush=True)
    # 服务器主动消息?
    for i in range(3):
        op, payload = ws.recv_frame(t=3)
        print('[recv%d] op=%s payload=%r' % (i + 1, op, payload[:200]), flush=True)
        if op is None:
            break

    print('=== P2: 发命令 ===', flush=True)
    ws.send_text('whoami\n')
    ws.send_text('id\n')
    for i in range(4):
        op, payload = ws.recv_frame(t=5)
        print('[cmd recv%d] op=%s payload=%r' % (i + 1, op, payload[:400]), flush=True)
        if op is None:
            break
    ws.close()

    print('=== P4: 路径变体 ===', flush=True)
    for p in ['/ws/interactive', '/ws/interactive/', '/ws', '/interactive', '/ws/interactive?token=',
              '/ws/interactive?t=' + tok, '/ws/interactive?access_token=' + tok]:
        try:
            ws2 = WS(host, p, None if '?' in p else tok)
            print('[%s] -> %s' % (p, ws2.resp.split(b'\r\n')[0].decode()), flush=True)
            ws2.close()
        except Exception as e:
            print('[%s] -> ERR %s' % (p, str(e)[:80]), flush=True)
        time.sleep(0.5)

    print('=== P5: stop->resume 生命周期 ===', flush=True)
    url_before, tok_before = url, tok
    c, r = api('POST', '/v2/sandboxes/sessions/%s/stop?teamId=%s&projectId=%s' % (sid, TEAM, PROJ), {}, timeout=90)
    print('[stop] -> %d' % c, flush=True)
    time.sleep(3)
    c, r = api('GET', '/v2/sandboxes/%s?teamId=%s&projectId=%s&resume=true' % (NAME, TEAM, PROJ), timeout=120)
    print('[resume] -> %d' % c, flush=True)
    time.sleep(10)
    c, r = api_raw('POST', '/v2/sandboxes/sessions/%s/interactive?teamId=%s' % (sid, TEAM), {})
    url2 = tok2 = None
    try:
        d = json.loads(r)
        url2, tok2 = d.get('url'), d.get('token')
    except Exception:
        pass
    print('[after resume] url same=%s tok same=%s' % (url_before == url2, tok_before == tok2), flush=True)
    print('  url2=%s tok2=%s' % (url2, (tok2 or '')[:8] + '...'), flush=True)
    if url2 and tok2:
        m2 = re.match(r'wss://([^/]+)(/.*)', url2)
        # 旧 URL + 旧 token 还工作吗?
        try:
            ws3 = WS(host, path, tok_before)
            print('[old url+tok] -> %s' % ws3.resp.split(b'\r\n')[0].decode(), flush=True)
            ws3.close()
        except Exception as e:
            print('[old url+tok] -> ERR %s' % str(e)[:80], flush=True)

    api("DELETE", "/v2/sandboxes/%s?teamId=%s&projectId=%s" % (NAME, TEAM, PROJ))
    print('CLEANED', flush=True)
