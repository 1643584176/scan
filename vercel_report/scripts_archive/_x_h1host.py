# -*- coding: utf-8 -*-
"""h1 Host 校验边界矩阵 (决定报告性质: h2-only vs h1+h2 都无校验)
U1: Host=httpbin.org (基线)
U2: Host=example.com (域名)
U3: Host=1.1.1.1 (公网 IP)
U4: Host=172.31.0.2 (私有 IP)
U5: Host=evil.com (恶意域名)
U6: 无 Host (curl 自动)
U7: Host=httpbin.org:8443 (端口变体)
"""
import json, sys, time
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

def run(tag, sc, maxlen=900):
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

for tag, host in [
    ('U1-base', 'httpbin.org'),
    ('U2-domain', 'example.com'),
    ('U3-pubip', '1.1.1.1'),
    ('U4-privip', '172.31.0.2'),
    ('U5-evil', 'evil.com'),
    ('U6-nohost', ''),
    ('U7-port', 'httpbin.org:8443'),
]:
    h = '-H "Host: %s"' % host if host else ''
    sc = 'curl -s -o /dev/null -w "CODE:%%{http_code}\\n" --http1.1 https://httpbin.org/anything %s 2>&1 | head -2' % h
    run(tag, sc)

print('=== H1M DONE ===', flush=True)
