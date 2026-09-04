# -*- coding: utf-8 -*-
"""N 线确认: deniedCIDRs 是否整体失效 (公网 deny 对照) + readback 确认"""
import json, re, sys, time
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, cmd, TEAM, PROJ

c, r = api('GET', '/v2/sandboxes/npol1?teamId=%s&projectId=%s' % (TEAM, PROJ))
d = json.loads(r)
sid = d['sandbox']['currentSessionId']
print('npol1 sid:', sid, 'status:', d['sandbox']['status'], flush=True)

def probe(sid, ip, port, tag):
    sc = 'python3 -c "import socket; s=socket.socket(); s.settimeout(3); rc=s.connect_ex((\'%s\',%d)); print(\'RC_\', rc)"' % (ip, port)
    c, r = cmd(sid, 'sh', ['-c', sc], timeout_ms=30000)
    rc = '?'
    try:
        for line in r.splitlines():
            if '"data"' in line:
                dd = json.loads(line).get('data', '')
                m = re.search(r'RC_ (\d+)', dd)
                if m:
                    rc = m.group(1)
    except Exception:
        pass
    print('[%s] %s:%d -> %s' % (tag, ip, port, rc), flush=True)
    return rc

# N1b: 仅 deny 公网 8.8.8.0/24 + 172.31.0.0/16
body = {
    "mode": "custom",
    "allowedDomains": ["httpbin.org"],
    "deniedCIDRs": ["8.8.8.0/24", "172.31.0.0/16"]
}
c, r = api('POST', '/v2/sandboxes/sessions/%s/network-policy?teamId=%s' % (sid, TEAM), body)
print('set N1b ->', c, r[:200], flush=True)
time.sleep(3)
# readback
c2, r2 = api('GET', '/v2/sandboxes/npol1?teamId=%s&projectId=%s' % (TEAM, PROJ))
try:
    d2 = json.loads(r2)
    print('readback:', json.dumps(d2.get('session', {}).get('networkPolicy')), flush=True)
except Exception:
    print('rb err', r2[:200], flush=True)

probe(sid, '8.8.8.8', 53, 'N1b-deny8888')
probe(sid, '8.8.4.4', 53, 'N1b-notdeny8844')
probe(sid, '172.31.0.2', 5432, 'N1b-vpc')
probe(sid, '1.1.1.1', 443, 'N1b-pub1111')

# N1c: deny-all 模式对照 (mode=deny-all 应该全拦)
body = {"mode": "deny-all"}
c, r = api('POST', '/v2/sandboxes/sessions/%s/network-policy?teamId=%s' % (sid, TEAM), body)
print('set deny-all ->', c, flush=True)
time.sleep(3)
probe(sid, '8.8.8.8', 53, 'N1c-denymode')
probe(sid, '172.31.0.2', 5432, 'N1c-denymode-vpc')
probe(sid, '1.1.1.1', 443, 'N1c-denymode-pub')

print('=== N1B DONE ===', flush=True)
