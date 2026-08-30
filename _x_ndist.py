# -*- coding: utf-8 -*-
"""N 线区分: deniedCIDRs 对公网真实服务是否生效 (deny httpbin.org IP -> curl 仍通?)"""
import json, re, sys, time
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, cmd, TEAM, PROJ

c, r = api('GET', '/v2/sandboxes/npol1?teamId=%s&projectId=%s' % (TEAM, PROJ))
d = json.loads(r)
sid = d['sandbox']['currentSessionId']
print('npol1 sid:', sid, flush=True)

# 0) 先恢复策略 (上轮结束为 deny-all)
body0 = {"mode": "custom", "allowedDomains": ["httpbin.org"]}
api('POST', '/v2/sandboxes/sessions/%s/network-policy?teamId=%s' % (sid, TEAM), body0)
time.sleep(3)

# 1) 沙箱内解析 httpbin.org IP
c, r = cmd(sid, 'sh', ['-c', 'python3 -c "import socket; print(socket.gethostbyname(\'httpbin.org\'))"'], timeout_ms=30000)
ip = None
for line in r.splitlines():
    if '"data"' in line:
        try:
            ip = json.loads(line).get('data', '').strip()
        except Exception:
            pass
print('httpbin.org IP:', ip, flush=True)

if not ip or not re.match(r'^\d+\.\d+\.\d+\.\d+$', ip):
    print('IP resolve failed, abort', flush=True)
    sys.exit(1)

# 2) 基线: allow httpbin.org (无 deny) -> curl 应 200 (策略已在步骤0设置)
c, r = cmd(sid, 'sh', ['-c', 'curl -sk --max-time 8 https://httpbin.org/anything 2>&1 | head -8'], timeout_ms=30000)
out0 = ''
for line in r.splitlines():
    if '"data"' in line:
        try:
            out0 += json.loads(line).get('data', '')[:200]
        except Exception:
            pass
print('BASE (no deny) curl:', 'OK' if 'anything' in out0 else out0[:150], flush=True)

# 3) deny httpbin.org IP/32 -> curl 仍通?
body = {"mode": "custom", "allowedDomains": ["httpbin.org"], "deniedCIDRs": [ip + '/32']}
c, r = api('POST', '/v2/sandboxes/sessions/%s/network-policy?teamId=%s' % (sid, TEAM), body)
print('set deny %s/32 ->' % ip, c, flush=True)
time.sleep(3)
c, r = cmd(sid, 'sh', ['-c', 'curl -sk --max-time 8 https://httpbin.org/anything 2>&1 | head -8'], timeout_ms=30000)
out1 = ''
for line in r.splitlines():
    if '"data"' in line:
        try:
            out1 += json.loads(line).get('data', '')[:200]
        except Exception:
            pass
print('DENY-IP curl:', 'OK-REACHABLE' if 'anything' in out1 else out1[:150], flush=True)

# 4) 对照: deny-all 模式 -> curl 应失败
body2 = {"mode": "deny-all"}
api('POST', '/v2/sandboxes/sessions/%s/network-policy?teamId=%s' % (sid, TEAM), body2)
time.sleep(3)
c, r = cmd(sid, 'sh', ['-c', 'curl -sk --max-time 8 https://httpbin.org/anything 2>&1 | head -8'], timeout_ms=30000)
out2 = ''
for line in r.splitlines():
    if '"data"' in line:
        try:
            out2 += json.loads(line).get('data', '')[:200]
        except Exception:
            pass
print('DENY-ALL curl:', 'FAIL-OK' if 'anything' not in out2 else out2[:150], flush=True)

print('=== N-DIST DONE ===', flush=True)
