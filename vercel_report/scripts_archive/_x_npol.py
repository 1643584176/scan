# -*- coding: utf-8 -*-
"""N 线: policy 规范化批量测试
1) deniedCIDRs 优先级: custom + allow httpbin.org + deny 全部私有网段 -> 172.31 仍可达?
2) unmasked CIDR: allowedCIDRs=['10.0.0.1'] (非 CIDR) -> 行为?
3) port suffix / 大小写 / trailing dot / wildcard depth
"""
import json, re, sys, time
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, cmd, TEAM, PROJ

def probe(sid, ip, port, tag):
    sc = 'python3 -c "import socket; s=socket.socket(); s.settimeout(3); rc=s.connect_ex((\'%s\',%d)); print(\'RC_\', rc)"' % (ip, port)
    c, r = cmd(sid, 'sh', ['-c', sc], timeout_ms=30000)
    rc = '?'
    try:
        for line in r.splitlines():
            if '"data"' in line:
                d = json.loads(line).get('data', '')
                m = re.search(r'RC_ (\d+)', d)
                if m:
                    rc = m.group(1)
    except Exception:
        pass
    print('[%s] %s:%d -> %s' % (tag, ip, port, rc), flush=True)
    return rc

def set_policy(sid, body, tag):
    c, r = api('POST', '/v2/sandboxes/sessions/%s/network-policy?teamId=%s' % (sid, TEAM), body)
    print('[%s] set_policy -> %d %s' % (tag, c, r[:200]), flush=True)
    time.sleep(3)
    return c

# 新建沙箱
name = 'npol1'
api('DELETE', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (name, TEAM, PROJ))
time.sleep(2)
c, r = api('POST', '/v2/sandboxes?teamId=%s' % TEAM, {"projectId": PROJ, "name": name})
print('create:', c, r[:150], flush=True)
sid = json.loads(r)['sandbox']['currentSessionId']
print('sid:', sid, flush=True)
time.sleep(3)

# ===== N1: deniedCIDRs 优先级 =====
set_policy(sid, {
    "mode": "custom",
    "allowedDomains": ["httpbin.org"],
    "deniedCIDRs": ["172.31.0.0/16", "100.64.0.0/10", "10.0.0.0/8", "192.168.0.0/16", "169.254.0.0/16"]
}, 'N1-deny-privates')
probe(sid, '172.31.0.2', 5432, 'N1-vpc5432')
probe(sid, '100.64.0.1', 8080, 'N1-cgnat')
probe(sid, '10.0.0.1', 5432, 'N1-10')
probe(sid, '1.1.1.1', 443, 'N1-pub')

# ===== N2: unmasked CIDR =====
set_policy(sid, {
    "mode": "custom",
    "allowedDomains": ["httpbin.org"],
    "allowedCIDRs": ["10.0.0.1"]
}, 'N2-unmasked')
probe(sid, '10.0.0.1', 5432, 'N2-10001')
probe(sid, '10.0.0.2', 5432, 'N2-10002')
probe(sid, '10.1.0.1', 5432, 'N2-10101')
probe(sid, '172.31.0.2', 5432, 'N2-vpc')
probe(sid, '1.1.1.1', 443, 'N2-pub')

# ===== N3: port suffix / 大小写 / trailing dot =====
set_policy(sid, {
    "mode": "custom",
    "allowedDomains": ["httpbin.org:443", "HTTPBIN.ORG.", "*.example.com"]
}, 'N3-variants')
# httpbin.org:443 是否匹配 httpbin.org
probe(sid, 'httpbin.org', 443, 'N3-httpbin-port')
probe(sid, 'httpbin.org', 22, 'N3-httpbin-port22')
# 大写/trailing dot
probe(sid, 'HTTPBIN.ORG', 443, 'N3-upper')
probe(sid, 'httpbin.org.', 443, 'N3-trailingdot')
# wildcard depth
probe(sid, 'www.example.com', 443, 'N3-wild-sub')
probe(sid, 'a.b.example.com', 443, 'N3-wild-deep')
probe(sid, 'example.com', 443, 'N3-wild-apex')

print('=== N DONE ===', flush=True)
