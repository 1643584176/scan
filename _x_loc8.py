# -*- coding: utf-8 -*-
"""sandbox-init gRPC 面深挖: (1) 沙箱 IP/监听 (2) proto 方法名+认证字符串 (3) 跨沙箱 23456/26661 连通性 (4) h2c 握手"""
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

# 建 A/B 两个沙箱
c, r = api("POST", "/v2/sandboxes?teamId=%s" % TEAM, {"projectId": PROJ, "name": "loc8a"})
if c != 200:
    log('A create failed: %s' % r[:200]); sys.exit(1)
sida = json.loads(r)["sandbox"]["currentSessionId"]
c, r = api("POST", "/v2/sandboxes?teamId=%s" % TEAM, {"projectId": PROJ, "name": "loc8b"})
if c != 200:
    log('B create failed: %s' % r[:200]); sys.exit(1)
sidb = json.loads(r)["sandbox"]["currentSessionId"]
log('A: %s  B: %s' % (sida, sidb))
time.sleep(3)

# 1) A 内: IP + 监听 + share 目录 + 二进制深挖
log('')
log('===== 1) A: ip/listen/share =====')
A1 = '''import socket, struct
# 找本机 IP
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
try:
    s.connect(('172.31.0.2', 53))
    print('MYIP', s.getsockname()[0], flush=True)
except Exception as e:
    print('MYIP-ERR', type(e).__name__, flush=True)
finally:
    s.close()
# 所有监听端口
for f in ['/proc/net/tcp', '/proc/net/tcp6']:
    try:
        for ln in open(f).read().splitlines()[1:]:
            p = ln.split()
            if p[3] in ('0A', '0B', '0C'):
                loc = p[1]
                ip, port = loc.rsplit(':', 1)
                print('LISTEN', f, ip, int(port, 16), 'state', p[3], flush=True)
    except Exception as e:
        print('ERR', f, type(e).__name__, flush=True)
'''
b64 = base64.b64encode(A1.encode()).decode()
c2, out = run_cmd(sida, 'sh', ['-c', 'echo %s | base64 -d | python3' % b64], 30000)
log(out[:1200])

# 2) A 内: 二进制 proto 方法名 + 认证字符串
log('')
log('===== 2) A: proto methods + auth strings =====')
A2 = '''import re
data = open('/run/vercel/share/sandbox-init','rb').read()
seen = set()
# proto 方法/服务名: 找 sandboxinit / Spawn / Exec / Cmd / Attach / Interactive 相关
for m in re.finditer(rb'[\\x20-\\x7e]{6,}', data):
    s = m.group().decode(errors='replace')
    low = s
    if any(k in s for k in ['Spawn', 'Exec', 'Attach', 'Interactive', 'Command', 'sandboxinit', 'Verifier', 'Interceptor', 'RunCmd', 'RunCommand']):
        if '/go/pkg' not in s and '/usr/local/go' not in s and s not in seen and len(s) < 160:
            seen.add(s)
            print('M:', s)
print('---- auth/token strings ----')
seen2 = set()
for m in re.finditer(rb'[\\x20-\\x7e]{4,}', data):
    s = m.group().decode(errors='replace')
    low = s.lower()
    if any(k in low for k in ['bearer', 'x-vercel', 'x-sandbox', 'auth', 'token', 'jwt', 'credential', 'apikey', 'api_key', 'authorization']) and len(s) < 80 and not s.startswith('/go/') and not s.startswith('crypto/') and not s.startswith('golang'):
        if s not in seen2:
            seen2.add(s)
            print('A:', s)
'''
b64 = base64.b64encode(A2.encode()).decode()
c2, out = run_cmd(sida, 'sh', ['-c', 'echo %s | base64 -d | python3' % b64], 90000)
log(out[-4500:])

# 3) B -> A 连通性 (23456/26661)
log('')
log('===== 3) B->A cross-sandbox connect =====')
B1 = '''import socket, struct, time
# 找 B 自己的 IP
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
try:
    s.connect(('172.31.0.2', 53))
    bip = s.getsockname()[0]
    print('BIP', bip, flush=True)
except Exception as e:
    bip = None
    print('BIP-ERR', type(e).__name__, flush=True)
s.close()
# A 的 IP 从参数传入 (hostname 解析不可用, 用 env)
import os
aip = os.environ.get('AIP', '')
print('AIP', aip, flush=True)
if aip:
    for port in [23456, 26661]:
        s2 = socket.socket(); s2.settimeout(3)
        try:
            rc = s2.connect_ex((aip, port))
            print('connect', aip, port, 'RC', rc, flush=True)
            if rc == 0:
                # h2c prior knowledge 前奏
                s2.sendall(b'PRI * HTTP/2.0\\r\\n\\r\\nSM\\r\\n\\r\\n')
                time.sleep(0.5)
                try:
                    d = s2.recv(512)
                    print('  h2 resp', len(d), repr(d[:120]), flush=True)
                except Exception as e:
                    print('  h2 noresp', type(e).__name__, flush=True)
        except Exception as e:
            print('connect err', type(e).__name__, flush=True)
        finally:
            s2.close()
'''
b64 = base64.b64encode(B1.encode()).decode()
# 需要 A 的 IP: 先跑 A1 拿 MYIP, 这里简化: B 内自己枚举猜测 172.31.0.x? 不行.
# 改用: A 内把 IP 写到文件, B 读不到. 方案: A 的 IP 通过 cmd 输出拿, 再传给 B.
# 先重新在 A 内拿 IP
c2, out = run_cmd(sida, 'sh', ['-c', 'python3 -c "import socket; s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM); s.connect((\"172.31.0.2\",53)); print(s.getsockname()[0])"'], 30000)
log('A ip: %s' % out.strip()[:100])
aip = out.strip().splitlines()[-1] if out.strip() else ''
log('AIP = %s' % aip)
if aip:
    cmd2 = 'AIP=%s; echo %s | base64 -d | python3' % (aip, b64)
    c2, out = run_cmd(sidb, 'sh', ['-c', cmd2], 60000)
    log('B->A: %s' % out[-1200:])

# 4) A 内对照: localhost 23456 h2c 握手
log('')
log('===== 4) A: localhost h2c handshake =====')
A3 = '''import socket, time
for port in [23456, 26661]:
    s = socket.socket(); s.settimeout(3)
    try:
        rc = s.connect_ex(('127.0.0.1', port))
        print('localhost', port, 'RC', rc, flush=True)
        if rc == 0:
            s.sendall(b'PRI * HTTP/2.0\\r\\n\\r\\nSM\\r\\n\\r\\n')
            time.sleep(0.5)
            try:
                d = s.recv(1024)
                print('  h2 resp', len(d), repr(d[:150]), flush=True)
            except Exception as e:
                print('  h2 noresp', type(e).__name__, flush=True)
    except Exception as e:
        print('err', type(e).__name__, flush=True)
    finally:
        s.close()
'''
b64 = base64.b64encode(A3.encode()).decode()
c2, out = run_cmd(sida, 'sh', ['-c', 'echo %s | base64 -d | python3' % b64], 30000)
log(out[:1000])

api("DELETE", "/v2/sandboxes/loc8a?teamId=%s&projectId=%s" % (TEAM, PROJ))
api("DELETE", "/v2/sandboxes/loc8b?teamId=%s&projectId=%s" % (TEAM, PROJ))
log('DONE')
