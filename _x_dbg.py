# -*- coding: utf-8 -*-
"""临时: 恢复策略 + 手动解析 DNS 调试"""
import json, sys, time
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, cmd, TEAM, PROJ

c, r = api('GET', '/v2/sandboxes/npol1?teamId=%s&projectId=%s' % (TEAM, PROJ))
d = json.loads(r)
sid = d['sandbox']['currentSessionId']
print('npol1 sid:', sid, 'status:', d['sandbox']['status'], flush=True)

# 恢复 custom + allow httpbin.org
body = {"mode": "custom", "allowedDomains": ["httpbin.org"]}
c, r = api('POST', '/v2/sandboxes/sessions/%s/network-policy?teamId=%s' % (sid, TEAM), body)
print('restore policy ->', c, r[:200], flush=True)
time.sleep(5)

# 解析 DNS (原始输出, 不过滤)
c, r = cmd(sid, 'sh', ['-c', 'python3 -c "import socket; print(socket.gethostbyname(\'httpbin.org\'))"'], timeout_ms=30000)
print('RAW RESOLVE RESP:', r[:1500], flush=True)

# curl 基线
c, r = cmd(sid, 'sh', ['-c', 'curl -sk --max-time 8 https://httpbin.org/anything 2>&1 | head -4'], timeout_ms=30000)
print('RAW CURL RESP:', r[:800], flush=True)

print('=== DBG DONE ===', flush=True)
