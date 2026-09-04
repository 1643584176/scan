# -*- coding: utf-8 -*-
"""N 线严格对照: deniedCIDRs 是否真的执行 (base64 探针避免引号陷阱)
A: custom+allow (无 deny)  -> PG 172.31.0.2:5432 / HTTP 172.31.0.2:80 / curl pub
B: +deny 172.31.0.0/16     -> 同上 (readback)
C: +deny 3.234.68.0/24     -> curl pub (readback)
D: deny-all                -> PG (对照)
"""
import base64, json, re, sys, time
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, cmd, TEAM, PROJ

c, r = api('GET', '/v2/sandboxes/npol1?teamId=%s&projectId=%s' % (TEAM, PROJ))
d = json.loads(r)
sid = d['sandbox']['currentSessionId']
print('npol1 sid:', sid, flush=True)

def parse_data(r):
    out = ''
    for line in r.splitlines():
        if '"data"' in line:
            try:
                out += json.loads(line).get('data', '')
            except Exception:
                pass
    return out

def run_b64(code, tag):
    b64 = base64.b64encode(code.encode()).decode()
    sc = 'echo %s | base64 -d | python3' % b64
    c, r = cmd(sid, 'sh', ['-c', sc], timeout_ms=30000)
    out = parse_data(r).strip()
    print('[%s] %s' % (tag, out[:150]), flush=True)
    return out

def set_policy(body, tag):
    c, r = api('POST', '/v2/sandboxes/sessions/%s/network-policy?teamId=%s' % (sid, TEAM), body)
    print('[%s] set ->' % tag, c, flush=True)
    time.sleep(3)
    c2, r2 = api('GET', '/v2/sandboxes/npol1?teamId=%s&projectId=%s' % (TEAM, PROJ))
    try:
        d2 = json.loads(r2)
        np = d2.get('session', {}).get('networkPolicy') or d2.get('sandbox', {}).get('networkPolicy')
        print('    readback:', json.dumps(np), flush=True)
    except Exception:
        pass

def curl_pub(tag):
    sc = "curl -sk --max-time 8 --resolve httpbin.org:443:3.234.68.252 https://httpbin.org/anything 2>&1 | head -3"
    c, r = cmd(sid, 'sh', ['-c', sc], timeout_ms=30000)
    out = parse_data(r)
    ok = '"anything"' in out or '"args"' in out
    print('[%s] %s' % (tag, 'OK-200' if ok else 'FAIL(%s)' % out[:60]), flush=True)
    return ok

PG_CODE = '''import socket,struct,time
s=socket.socket(); s.settimeout(4)
rc=s.connect_ex(('172.31.0.2',5432))
print('PG_CONNECT', rc)
if rc==0:
    s.sendall(struct.pack('!II',8,80877103))
    time.sleep(0.8)
    try:
        d=s.recv(4); print('PG_RESP', d)
    except Exception as e:
        print('PG_ERR', type(e).__name__)
'''

HTTP_CODE = '''import socket
s=socket.socket(); s.settimeout(4)
rc=s.connect_ex(('172.31.0.2',80))
print('HTTP_CONNECT', rc)
if rc==0:
    try:
        s.sendall(b'GET / HTTP/1.0\\r\\n\\r\\n')
        d=s.recv(100); print('HTTP_RESP', d)
    except Exception as e:
        print('HTTP_ERR', type(e).__name__)
'''

# 0) 恢复
set_policy({"mode": "custom", "allowedDomains": ["httpbin.org"]}, 'RECOVER')

# A: 基线 无 deny
run_b64(PG_CODE, 'A-base-PG')
run_b64(HTTP_CODE, 'A-base-HTTP')
curl_pub('A-base-curl')

# B: deny 私有网段
set_policy({"mode": "custom", "allowedDomains": ["httpbin.org"], "deniedCIDRs": ["172.31.0.0/16"]}, 'B')
run_b64(PG_CODE, 'B-denyVPC-PG')
run_b64(HTTP_CODE, 'B-denyVPC-HTTP')
curl_pub('B-denyVPC-curl')

# C: deny 公网
set_policy({"mode": "custom", "allowedDomains": ["httpbin.org"], "deniedCIDRs": ["3.234.68.0/24"]}, 'C')
curl_pub('C-denyPUB-curl')
run_b64(PG_CODE, 'C-denyPUB-PG')

# D: deny-all
set_policy({"mode": "deny-all"}, 'D')
run_b64(PG_CODE, 'D-denymode-PG')

print('=== N-FINAL4 DONE ===', flush=True)
