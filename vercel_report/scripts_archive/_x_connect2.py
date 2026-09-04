# -*- coding: utf-8 -*-
"""h2 CONNECT 隧道测试: curl 把 allow 域名当 CONNECT 代理
P1: h2 CONNECT 到 example.com (非 allow) -> 隧道?
P2: h1 CONNECT 对照 (预期 awselb 400)
P3: h2 CONNECT 到 1.1.1.1:443
P4: h2 CONNECT 到 172.31.0.2:5432 (私有网段)
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
    c, r = cmd(sid, 'sh', ['-c', sc], timeout_ms=60000)
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

# P1: h2 CONNECT -> example.com
run('P1-h2-connect', 'curl -sv -m 8 --http2 -k -x https://httpbin.org:443 https://example.com/ -o /dev/null 2>&1 | grep -E "CONNECT|HTTP/|error|refused|Connected|Tunnel" | head -8')

# P2: h1 CONNECT 对照
run('P2-h1-connect', 'curl -sv -m 8 --http1.1 -k -x https://httpbin.org:443 https://example.com/ -o /dev/null 2>&1 | grep -E "CONNECT|HTTP/|error|refused|Connected|Tunnel" | head -8')

# P3: h2 CONNECT -> 1.1.1.1
run('P3-h2-1111', 'curl -sv -m 8 --http2 -k -x https://httpbin.org:443 https://1.1.1.1/ -o /dev/null 2>&1 | grep -E "CONNECT|HTTP/|error|refused|Connected|Tunnel" | head -8')

print('=== P DONE ===', flush=True)
