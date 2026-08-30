# -*- coding: utf-8 -*-
"""N 线最终确认: deniedCIDRs 对私有网段 vs 公网的数据层对照
P1: deny 172.31.0.0/16 -> PG 数据层探针 172.31.0.2:5432 (期望 b'S' = deny 无效)
P2: deny 172.31.0.0/16 -> HTTP 明文探针 172.31.0.2:80 (数据层)
P3: deny 公网 3.234.68.0/24 -> curl --resolve 3.234.68.252 (期望 FAIL = deny 有效)
P4: deny 172.31.0.0/16 + 3.234.68.0/24 -> 两者同测 (复合)
P5: deny-all -> PG 探针 (期望 113 = 模式级 deny 有效)
readback 每步确认策略保存
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

def pg_probe(tag):
    sc = 'python3 -c "import socket,struct,time; s=socket.socket(); s.settimeout(3); s.connect((\'172.31.0.2\',5432)); s.sendall(struct.pack(\'!II\',8,80877103)); time.sleep(0.5);\ntry:\n d=s.recv(4); print(\'PG_RESP\', d)\nexcept Exception as e:\n print(\'PG_ERR\', type(e).__name__)"'
    c, r = cmd(sid, 'python3', ['-c', sc], timeout_ms=30000)
    out = parse_data(r)
    print('[%s] %s' % (tag, out[:120]), flush=True)
    return out

def http_probe(tag):
    sc = 'python3 -c "import socket; s=socket.socket(); s.settimeout(3); s.connect((\'172.31.0.2\',80)); s.sendall(b\'GET / HTTP/1.0\\r\\n\\r\\n\'); d=s.recv(100); print(\'HTTP_RESP\', d)"' 
    c, r = cmd(sid, 'sh', ['-c', sc], timeout_ms=30000)
    out = parse_data(r)
    print('[%s] %s' % (tag, out[:120]), flush=True)
    return out

def curl_pub(tag):
    sc = "curl -sk --max-time 8 --resolve httpbin.org:443:3.234.68.252 https://httpbin.org/anything 2>&1 | head -3"
    c, r = cmd(sid, 'sh', ['-c', sc], timeout_ms=30000)
    out = parse_data(r)
    ok = '"anything"' in out or '"args"' in out
    print('[%s] %s' % (tag, 'OK-200' if ok else 'FAIL(%s)' % out[:60]), flush=True)
    return ok

# 0) 恢复 (上轮 deny-all)
set_policy({"mode": "custom", "allowedDomains": ["httpbin.org"]}, 'RECOVER')

# P1: deny 私有网段 -> PG 数据层
set_policy({"mode": "custom", "allowedDomains": ["httpbin.org"], "deniedCIDRs": ["172.31.0.0/16"]}, 'P1')
pg_probe('P1-deny-vpc16-PG')

# P2: deny 私有网段 -> HTTP 明文数据层
http_probe('P2-deny-vpc16-HTTP')

# P3: deny 公网 -> curl 数据层
set_policy({"mode": "custom", "allowedDomains": ["httpbin.org"], "deniedCIDRs": ["3.234.68.0/24"]}, 'P3')
curl_pub('P3-deny-pub24-curl')
pg_probe('P3-deny-pub24-PG')

# P4: deny 私有 + 公网 复合
set_policy({"mode": "custom", "allowedDomains": ["httpbin.org"], "deniedCIDRs": ["172.31.0.0/16", "3.234.68.0/24"]}, 'P4')
pg_probe('P4-deny-both-PG')
curl_pub('P4-deny-both-curl')

# P5: deny-all 对照
set_policy({"mode": "deny-all"}, 'P5')
pg_probe('P5-denymode-PG')

print('=== N-FINAL3 DONE ===', flush=True)
