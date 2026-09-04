# -*- coding: utf-8 -*-
"""跟进三线: (1) localhost 40532/47354 端口指纹 (2) fs/write Content-Type 变体 (3) 172.31.0.2 UDP DNS 判定"""
import json, sys, time, base64
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ, BASE, TOKEN

def log(s):
    print(s, flush=True)

def run_cmd(sid, command, args, timeout_ms=30000):
    c, r = api("POST", "/v2/sandboxes/sessions/%s/cmd?teamId=%s" % (sid, TEAM),
               {"command": command, "args": args, "wait": True, "logs": True, "timeout": timeout_ms})
    out = ''
    for line in r.splitlines():
        if '"data"' in line:
            try: out += json.loads(line).get('data', '')
            except Exception: pass
    return c, out

# 建沙箱
c, r = api("POST", "/v2/sandboxes?teamId=%s" % TEAM, {"projectId": PROJ, "name": "loc2"})
if c != 200:
    log('create failed: %s' % r[:200]); sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
log('loc2 sid: %s' % sid)
time.sleep(3)

# 1) 端口指纹 40532/47354 (+23456 对照)
log('')
log('===== 1) port fingerprint =====')
FP = '''import socket, time
def probe(port, mode):
    s = socket.socket(); s.settimeout(3)
    try:
        s.connect(('127.0.0.1', port))
        if mode == 'banner':
            try: return repr(s.recv(256))
            except Exception as e: return 'NOBANNER:%s' % type(e).__name__
        if mode == 'get':
            s.sendall(b'GET / HTTP/1.0\\r\\nHost: localhost\\r\\n\\r\\n')
        if mode == 'head':
            s.sendall(b'HEAD / HTTP/1.0\\r\\nHost: localhost\\r\\n\\r\\n')
        if mode == 'opt':
            s.sendall(b'OPTIONS * HTTP/1.1\\r\\nHost: localhost\\r\\n\\r\\n')
        if mode == 'post':
            s.sendall(b'POST / HTTP/1.1\\r\\nHost: localhost\\r\\nContent-Length: 0\\r\\n\\r\\n')
        if mode == 'raw':
            s.sendall(b'\\x00\\x01\\x02ping')
        time.sleep(0.4)
        try: return repr(s.recv(1024))
        except Exception as e: return 'NORESP:%s' % type(e).__name__
    except Exception as e:
        return 'ERR:%s' % type(e).__name__
    finally:
        s.close()
for port in [40532, 47354, 23456]:
    for mode in ['banner', 'get', 'head', 'opt', 'post', 'raw']:
        print(port, mode, probe(port, mode), flush=True)
'''
b64 = base64.b64encode(FP.encode()).decode()
c2, out = run_cmd(sid, 'sh', ['-c', 'echo %s | base64 -d | python3' % b64], 90000)
log(out[-3000:])

# 进程/监听确认 (上轮输出被截断)
c2, out = run_cmd(sid, 'sh', ['-c', 'cat /proc/net/unix 2>/dev/null | head -40; echo ===; for p in /proc/[0-9]*; do e=$(readlink $p/exe 2>/dev/null); [ -n "$e" ] && echo "$p $e"; done | head -30; echo ===; ss -lntp 2>/dev/null'], 30000)
log('procs: %s' % out[:2500])

# 2) fs/write Content-Type 变体
log('')
log('===== 2) fs/write CT variants =====')
import urllib.request, urllib.error
def api_ct(method, path, raw=None, ct=None):
    req = urllib.request.Request(BASE + path, method=method)
    req.add_header('Authorization', 'Bearer ' + TOKEN)
    if ct:
        req.add_header('Content-Type', ct)
    try:
        with urllib.request.urlopen(req, data=raw, timeout=30) as r:
            return r.status, r.read().decode()[:300]
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:300]

variants = [
    ('octet', 'application/octet-stream', b'hello'),
    ('text', 'text/plain', b'hello'),
    ('none', None, b'hello'),
    ('form', 'application/x-www-form-urlencoded', b'path=/vercel/sandbox/t.txt&content=aGVsbG8='),
    ('json-raw', 'application/json', b'{"path":"/vercel/sandbox/t.txt","content":"aGVsbG8="}'),
]
for name, ct, raw in variants:
    c3, r3 = api_ct('POST', '/v2/sandboxes/sessions/%s/fs/write?teamId=%s' % (sid, TEAM), raw=raw, ct=ct)
    log('fs/write %-6s -> %s | %s' % (name, c3, r3[:250].replace('\n', ' ')))

# 3) UDP DNS 判定 (TCP timeout 是否真实 DNS)
log('')
log('===== 3) UDP DNS =====')
UDP = '''import socket, struct
def udp_dns(ip, qname=b'\\x07example\\x03com\\x00'):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(3)
    hdr = struct.pack('!HHHHHH', 0x1234, 0x0100, 1, 0, 0, 0)
    try:
        s.sendto(hdr + qname + struct.pack('!HH', 1, 1), (ip, 53))
        d, _ = s.recvfrom(512)
        flags = struct.unpack('!H', d[2:4])[0]
        return 'UDP %dB rcode=%d' % (len(d), flags & 0xF)
    except Exception as e:
        return 'UDP %s' % type(e).__name__
    finally:
        s.close()
for ip in ['172.31.0.2', '172.31.0.3', '10.0.0.2']:
    print(ip, udp_dns(ip), flush=True)
'''
b64 = base64.b64encode(UDP.encode()).decode()
c2, out = run_cmd(sid, 'sh', ['-c', 'echo %s | base64 -d | python3' % b64], 60000)
log('udp dns: %s' % out[-500:])

# 清理
api("DELETE", "/v2/sandboxes/loc2?teamId=%s&projectId=%s" % (TEAM, PROJ))
log('DONE')
