# -*- coding: utf-8 -*-
"""非传统面J: ①v1 全端点(无 name) ②v4 ports 完整响应 ③interactive WS 协议帧 fuzz"""
import json, sys, time, ssl, socket, base64, os, struct
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TOKEN, TEAM, PROJ

def log(s): print(s, flush=True)

# ① v1 端点矩阵
log('===== ① v1 端点 =====')
c, r = api("POST", "/v1/sandboxes?teamId=%s" % TEAM, {"projectId": PROJ}, 60)
log('v1 create -> %s | %s' % (c, (r or '')[:200].replace(chr(10), ' ')))
if c == 200:
    sb = json.loads(r)['sandbox']
    sb_id = sb['id']
    time.sleep(3)
    for ep, body in [
        ('stop', {}), ('snapshot', {}), ('network-policy', {"mode": "deny-all"}),
        ('fs/read', {"path": "/etc/passwd"}), ('interactive', {}),
        ('extend-timeout', {"duration": 60000}), ('cmd', {"command": "id", "args": [], "wait": True, "timeout": 8000}),
    ]:
        c2, r2 = api("POST", "/v1/sandboxes/%s/%s?teamId=%s" % (sb_id, ep, TEAM), body, 20)
        log('[v1 %s] -> %s | %s' % (ep, c2, (r2 or '')[:180].replace(chr(10), ' ')))
    api("DELETE", "/v1/sandboxes/%s?teamId=%s" % (sb_id, TEAM), None, 15)
    time.sleep(1)
    api("DELETE", "/v2/sandboxes/%s?teamId=%s&projectId=%s" % (sb_id, TEAM, PROJ), None, 15)

# ② v4 ports 完整响应
log('')
log('===== ② v4 ports 响应全文 =====')
api("DELETE", "/v2/sandboxes/n28p?teamId=%s&projectId=%s" % (TEAM, PROJ))
time.sleep(2)
c, r = api("POST", "/v4/sandboxes?teamId=%s" % TEAM, {"projectId": PROJ, "name": "n28p", "ports": [8080]}, 60)
log('v4 ports create -> %s | %s' % (c, (r or '').replace(chr(10), ' ')))
api("DELETE", "/v2/sandboxes/n28p?teamId=%s&projectId=%s" % (TEAM, PROJ))

# ③ interactive WS 协议 fuzz
log('')
log('===== ③ interactive WS fuzz =====')
api("DELETE", "/v2/sandboxes/n28w?teamId=%s&projectId=%s" % (TEAM, PROJ))
time.sleep(2)
c, r = api("POST", "/v4/sandboxes?teamId=%s" % TEAM, {"projectId": PROJ, "name": "n28w"}, 60)
sid = json.loads(r)['sandbox']['currentSessionId']
time.sleep(3)
c, r = api("POST", "/v2/sandboxes/sessions/%s/interactive?teamId=%s" % (sid, TEAM), {}, 15)
d = json.loads(r)
wsurl = d['url'].replace('wss://', 'https://')
wtok = d['token']
log('ws url=%s' % wsurl)
log('token=%s' % wtok)

def ws_connect(url, tok, path='/', extra_headers=None):
    """手写 WS 客户端 (无外部库依赖)"""
    u = url.replace('https://', '').replace('wss://', '')
    host, _, port = u.partition(':')
    port = int(port or 443)
    ctx = ssl.create_default_context()
    sock = socket.create_connection((host, port), timeout=10)
    ws = ctx.wrap_socket(sock, server_hostname=host)
    key = base64.b64encode(os.urandom(16)).decode()
    hdrs = [
        'GET %s HTTP/1.1' % path,
        'Host: %s:%d' % (host, port),
        'Upgrade: websocket',
        'Connection: Upgrade',
        'Sec-WebSocket-Key: %s' % key,
        'Sec-WebSocket-Version: 13',
    ]
    if tok:
        hdrs.append('Authorization: Bearer %s' % tok)
    if extra_headers:
        hdrs.extend(extra_headers)
    ws.sendall(('\r\n'.join(hdrs) + '\r\n\r\n').encode())
    resp = b''
    while b'\r\n\r\n' not in resp:
        resp += ws.recv(4096)
    status = resp.split(b'\r\n')[0].decode()
    log('WS handshake: %s' % status)
    if b'101' not in resp:
        return ws, None
    # 读初始帧
    try:
        ws.settimeout(3)
        fr = recv_frame(ws)
        log('initial frame: %r' % (fr[:200] if fr else None))
    except Exception as e:
        log('initial frame err: %s' % str(e)[:80])
    return ws, resp

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

# 用 query token (之前验证过的 ?token= 方式)
for tag, path, hdr in [('query-token', '/ws/interactive?token=%s' % wtok, None),
                       ('auth-hdr', '/ws/interactive', ['Authorization: Bearer %s' % wtok])]:
    ws, resp = ws_connect(wsurl, None if tag == 'query-token' else wtok, path, hdr)
    if resp is None:
        continue
    # fuzz 消息
    for msg in ['ping', '{"type":"exec","command":"id"}', '{"command":"id"}', '{"type":"cmd","data":"id"}',
                '{"type":"input","data":"id\\n"}', '{"type":"shell","cmd":"id"}', '', '{"op":"echo","text":"hi"}']:
        try:
            send_frame(ws, msg.encode())
            ws.settimeout(2.5)
            out = recv_frame(ws)
            log('[%s] << %r -> %r' % (tag, msg[:40], (out or b'')[:150]))
        except Exception as e:
            log('[%s] << %r err %s' % (tag, msg[:40], str(e)[:60]))
    ws.close()
    break

api("DELETE", "/v2/sandboxes/n28w?teamId=%s&projectId=%s" % (TEAM, PROJ))
log('DONE')
