# -*- coding: utf-8 -*-
"""gRPC 面: (1) proto 注册名 (2) A 内 env 变量名 (3) HTTP/1.1 Connect Ping 认证行为 (4) B->A 跨沙箱连通+认证"""
import json, sys, time, base64
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ

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

c, r = api("POST", "/v2/sandboxes?teamId=%s" % TEAM, {"projectId": PROJ, "name": "loc9a"})
if c != 200:
    log('A create failed: %s' % r[:200]); sys.exit(1)
sida = json.loads(r)["sandbox"]["currentSessionId"]
c, r = api("POST", "/v2/sandboxes?teamId=%s" % TEAM, {"projectId": PROJ, "name": "loc9b"})
if c != 200:
    log('B create failed: %s' % r[:200]); sys.exit(1)
sidb = json.loads(r)["sandbox"]["currentSessionId"]
log('A: %s  B: %s' % (sida, sidb))
time.sleep(3)

# 1) proto 注册名搜索
log('')
log('===== 1) proto reg names =====')
A1 = '''import re
data = open('/run/vercel/share/sandbox-init','rb').read()
seen = set()
for pat in [rb'[A-Za-z0-9_.]{5,60}Service', rb'[A-Za-z0-9_.]{4,60}/Ping', rb'[A-Za-z0-9_.]{4,60}/Spawn', rb'[A-Za-z0-9_.]{4,60}/Kill', rb'sandboxinit[A-Za-z0-9_.]{0,40}']:
    for m in re.finditer(pat, data):
        s = m.group().decode(errors='replace')
        if s not in seen and '/go/' not in s and 'golang' not in s and 'google' not in s and 'crypto' not in s:
            seen.add(s)
            print(s[:150])
'''
b64 = base64.b64encode(A1.encode()).decode()
c2, out = run_cmd(sida, 'sh', ['-c', 'echo %s | base64 -d | python3' % b64], 60000)
log(out[:2500])

# 2) A 内 env 变量名 (只看名字)
log('')
log('===== 2) A: pid1 env names =====')
A2 = '''import os, re
for pidf in ['/proc/1/environ', '/proc/self/environ']:
    try:
        d = open(pidf, 'rb').read()
        keys = [x.split(b'=')[0].decode(errors='replace') for x in d.split(b'\\x00') if b'=' in x]
        print(pidf, len(keys), sorted(keys), flush=True)
    except Exception as e:
        print(pidf, 'ERR', type(e).__name__, flush=True)
'''
b64 = base64.b64encode(A2.encode()).decode()
c2, out = run_cmd(sida, 'sh', ['-c', 'echo %s | base64 -d | python3' % b64], 30000)
log(out[:2000])

# 3) A 内 HTTP/1.1 Connect Ping
log('')
log('===== 3) A: connect ping (http1.1) =====')
A3 = '''import socket
paths = [
    '/sandboxinit.SpawnService/Ping',
    '/vercel.sandboxinit.SpawnService/Ping',
    '/vercel.sandboxinit.v1.SpawnService/Ping',
    '/sandboxinit.v1.SpawnService/Ping',
    '/hive.SpawnService/Ping',
]
for p in paths:
    for port in [23456]:
        s = socket.socket(); s.settimeout(3)
        try:
            s.connect(('127.0.0.1', port))
            body = b'{}'
            req = ('POST %s HTTP/1.1\\r\\nHost: localhost\\r\\nContent-Type: application/json\\r\\n'
                   'Connect-Protocol-Version: 1\\r\\nAccept: application/json\\r\\n'
                   'Content-Length: %d\\r\\n\\r\\n' % (p, len(body))).encode() + body
            s.sendall(req)
            import time; time.sleep(0.4)
            d = b''
            try:
                while True:
                    chunk = s.recv(2048)
                    if not chunk: break
                    d += chunk
                    if len(d) > 3000: break
            except Exception:
                pass
            first = d.split(b'\\r\\n')[0] if d else b'EMPTY'
            print(p, '->', first.decode(errors='replace'), '|', repr(d[:180]), flush=True)
        except Exception as e:
            print(p, 'ERR', type(e).__name__, flush=True)
        finally:
            s.close()
'''
b64 = base64.b64encode(A3.encode()).decode()
c2, out = run_cmd(sida, 'sh', ['-c', 'echo %s | base64 -d | python3' % b64], 60000)
log(out[-3000:])

# 4) B->A 跨沙箱
log('')
log('===== 4) B->A cross-sandbox =====')
A4 = '''import socket
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
try:
    s.connect(('172.31.0.2', 53))
    print(s.getsockname()[0], flush=True)
except Exception as e:
    print('ERR', flush=True)
'''
b64 = base64.b64encode(A4.encode()).decode()
c2, out = run_cmd(sida, 'sh', ['-c', 'echo %s | base64 -d | python3' % b64], 30000)
aip = out.strip().splitlines()[-1] if out.strip() else ''
log('AIP = %s' % aip)

B1 = '''import socket, time, os
aip = os.environ.get('AIP', '')
print('AIP', aip, flush=True)
if not aip:
    raise SystemExit
for port in [23456, 26661]:
    s = socket.socket(); s.settimeout(3)
    try:
        rc = s.connect_ex((aip, port))
        print('connect', aip, port, 'RC', rc, flush=True)
        if rc == 0:
            # HTTP/1.1 Connect Ping
            body = b'{}'
            req = ('POST /sandboxinit.SpawnService/Ping HTTP/1.1\\r\\nHost: %s\\r\\nContent-Type: application/json\\r\\n'
                   'Connect-Protocol-Version: 1\\r\\nAccept: application/json\\r\\n'
                   'Content-Length: %d\\r\\n\\r\\n' % (aip, len(body))).encode() + body
            s.sendall(req)
            time.sleep(0.5)
            try:
                d = s.recv(2048)
                print('  resp', repr(d[:250]), flush=True)
            except Exception as e:
                print('  noresp', type(e).__name__, flush=True)
    except Exception as e:
        print('err', type(e).__name__, flush=True)
    finally:
        s.close()
'''
b64 = base64.b64encode(B1.encode()).decode()
cmd2 = 'AIP=%s; echo %s | base64 -d | python3' % (aip, b64)
c2, out = run_cmd(sidb, 'sh', ['-c', cmd2], 60000)
log('B->A: %s' % out[-1500:])

api("DELETE", "/v2/sandboxes/loc9a?teamId=%s&projectId=%s" % (TEAM, PROJ))
api("DELETE", "/v2/sandboxes/loc9b?teamId=%s&projectId=%s" % (TEAM, PROJ))
log('DONE')
