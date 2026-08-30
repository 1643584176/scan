# -*- coding: utf-8 -*-
"""防火墙代理 HTTP/2 支持验证
O1: curl --http2 到 httpbin.org (代理转发路径) -> 支持 h2?
O2: curl --http1.1 对照
O3: ALPN 协商结果 (openssl s_client 不可用则 python)
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

def run(tag, sc, maxlen=1200):
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

# 恢复策略
api('POST', '/v2/sandboxes/sessions/%s/network-policy?teamId=%s' % (sid, TEAM),
    {"mode": "custom", "allowedDomains": ["httpbin.org"]})
time.sleep(3)

# O1: h2
run('O1-h2', 'curl -s --http2 -o /dev/null -w "H2_CODE:%{http_code} VER:%{http_version}\\n" -I https://httpbin.org/get 2>&1 | head -3')

# O2: h1.1
run('O2-h1', 'curl -s --http1.1 -o /dev/null -w "H1_CODE:%{http_code} VER:%{http_version}\\n" -I https://httpbin.org/get 2>&1 | head -3')

print('=== H2 DONE ===', flush=True)
