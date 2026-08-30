# -*- coding: utf-8 -*-
"""非传统面K: interactive WS 协议帧 fuzz + resume 前后 token 生命周期"""
import json, sys, time, ssl, socket, base64, os, struct
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ

def log(s): print(s, flush=True)

def recv_frame(ws):
    h = ws.recv(2)
    if len(h) < 2: return None
    b0, b1 = h[0], h[1]
    ln = b1 & 0x7F
    if ln == 126:
        ln = struct.unpack('>H', ws.recv(2))[0]
    elif ln == 127:
        ln = struct.unpack('>Q', ws.recv(8))[0]
    if b0 & 0x80:
        mask = ws.recv(4)
    else:
        mask = None
    data = b''
    while len(data) < ln:
        data += ws.recv(ln - len(data))
    if mask:
        data = bytes(c ^ mask[i % 4] for i, c in enumerate(data))
    return data

def send_frame(ws, data, opcode=1):
    ln = len(data)
    hdr = bytes([0x80 | opcode])
    if ln < 126:
        hdr += bytes([0x80 | ln])
    elif ln < 65536:
        hdr += bytes([0x80 | 126]) + struct.pack('>H', ln)
    else:
        hdr += bytes([0x80 | 127]) + struct.pack('>Q', ln)
    mask = os.urandom(4)
    hdr += mask
    ws.sendall(hdr + bytes(c ^ mask[i % 4] for i, c in enumerate(data)))

def wait_dns(host, tries=30, delay=3):
    """等待沙箱域名 DNS 生效"""
    import socket as _s
    for i in range(tries):
        try:
            _s.gethostbyname(host)
            log('dns ok after %ds: %s' % ((i + 1) * delay, host))
            return True
        except Exception:
            time.sleep(delay)
    log('dns timeout: %s' % host)
    return False

def ws_connect(url, path, tok=None):
    u = url.replace('https://', '').replace('wss://', '').split('/')[0]
    host, _, port = u.partition(':')
    port = int(port or 443)
    ctx = ssl.create_default_context()
    sock = socket.create_connection((host, port), timeout=10)
    ws = ctx.wrap_socket(sock, server_hostname=host)
    key = base64.b64encode(os.urandom(16)).decode()
    hdrs = ['GET %s HTTP/1.1' % path, 'Host: %s' % host, 'Upgrade: websocket',
            'Connection: Upgrade', 'Sec-WebSocket-Key: %s' % key,
            'Sec-WebSocket-Version: 13']
    if tok:
        hdrs.append('Authorization: Bearer %s' % tok)
    ws.sendall(('\r\n'.join(hdrs) + '\r\n\r\n').encode())
    resp = b''
    while b'\r\n\r\n' not in resp:
        resp += ws.recv(4096)
    status = resp.split(b'\r\n')[0].decode()
    return ws, status

api("DELETE", "/v2/sandboxes/n29?teamId=%s&projectId=%s" % (TEAM, PROJ))
time.sleep(2)
c, r = api("POST", "/v4/sandboxes?teamId=%s" % TEAM, {"projectId": PROJ, "name": "n29"}, 60)
sid = json.loads(r)['sandbox']['currentSessionId']
time.sleep(3)
c, r = api("POST", "/v2/sandboxes/sessions/%s/interactive?teamId=%s" % (sid, TEAM), {}, 15)
d = json.loads(r)
wsurl = d['url'].replace('wss://', 'https://')
wtok = d['token']
log('url=%s' % wsurl)
host0 = wsurl.replace('https://', '').split('/')[0]
wait_dns(host0)

# ① 握手 + 初始帧 + 协议 fuzz
log('===== ① WS 协议 fuzz =====')
ws, st = ws_connect(wsurl, '/ws/interactive?token=%s' % wtok)
log('handshake: %s' % st)
if '101' in st:
    try:
        ws.settimeout(3)
        fr = recv_frame(ws)
        log('initial: %r' % (fr[:300] if fr else None))
    except Exception as e:
        log('initial err: %s' % str(e)[:60])
    msgs = [
        b'ping',
        b'{"type":"exec","command":"id"}',
        b'{"command":"id"}',
        b'{"type":"input","data":"id\n"}',
        b'{"type":"shell","cmd":"id"}',
        b'{"type":"connect","cols":80,"rows":24}',
        b'id\n',
        b'{"type":"resize","cols":120,"rows":30}',
        b'{"type":"tty"}',
        b'{"type":"spawn","file":"/bin/sh","args":[]}',
    ]
    for m in msgs:
        try:
            send_frame(ws, m)
            ws.settimeout(2.5)
            out = recv_frame(ws)
            log('<< %r -> %r' % (m[:50], (out or b'')[:200]))
        except Exception as e:
            log('<< %r err %s' % (m[:50], str(e)[:60]))
    ws.close()

# ② resume 前后 token 生命周期
log('')
log('===== ② token 跨 resume =====')
# stop
api("POST", "/v2/sandboxes/sessions/%s/stop?teamId=%s" % (sid, TEAM), {}, 25)
time.sleep(3)
# resume
c, r = api("GET", "/v2/sandboxes/n29?teamId=%s&projectId=%s&resume=true" % (TEAM, PROJ), None, 30)
nsid = json.loads(r)['sandbox']['currentSessionId']
log('new sid: %s' % nsid)
time.sleep(3)
# 新会话再拿 token
c, r = api("POST", "/v2/sandboxes/sessions/%s/interactive?teamId=%s" % (nsid, TEAM), {}, 15)
d2 = json.loads(r)
wsurl2 = d2['url'].replace('wss://', 'https://')
wtok2 = d2['token']
log('new token: %s' % wtok2)
log('old token == new? %s' % (wtok == wtok2))
# 旧 token + 旧 url (resume 后)
ws, st = ws_connect(wsurl, '/ws/interactive?token=%s' % wtok)
log('old tok + old url after resume: %s' % st)
if '101' in st:
    ws.close()
# 新 token + 旧 url
ws, st = ws_connect(wsurl, '/ws/interactive?token=%s' % wtok2)
log('new tok + old url: %s' % st)
if '101' in st:
    ws.close()
# 新 token + 新 url
ws, st = ws_connect(wsurl2, '/ws/interactive?token=%s' % wtok2)
log('new tok + new url: %s' % st)
if '101' in st:
    ws.close()

api("DELETE", "/v2/sandboxes/n29?teamId=%s&projectId=%s" % (TEAM, PROJ))
log('DONE')
