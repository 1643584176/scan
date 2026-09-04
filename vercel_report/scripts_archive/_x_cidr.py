# -*- coding: utf-8 -*-
"""allowedCIDRs 功能确认 + custom 空列表行为 (D 线归因完整化)
E1: custom {} 空 -> curl httpbin.org (文档: behaves as deny-all)
E2: custom + allowedCIDRs=["8.8.8.0/24"] -> TCP DNS 8.8.8.8:53 数据层 (IP 白名单生效?)
E3: E2 下 1.1.1.1:53 对照 (应不可达)
E4: custom + allowedCIDRs=["8.8.8.0/24"] + deniedCIDRs=["8.8.8.0/24"] -> 冲突时行为
E5: custom + allowedCIDRs=["172.31.0.0/16"] -> PG 172.31.0.2:5432 (显式 allow 私有网段=预期?)
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

def set_policy(body, tag):
    c, r = api('POST', '/v2/sandboxes/sessions/%s/network-policy?teamId=%s' % (sid, TEAM), body)
    print('[%s] set ->' % tag, c, r[:150], flush=True)
    time.sleep(3)
    c2, r2 = api('GET', '/v2/sandboxes/npol1?teamId=%s&projectId=%s' % (TEAM, PROJ))
    try:
        d2 = json.loads(r2)
        np = d2.get('session', {}).get('networkPolicy') or d2.get('sandbox', {}).get('networkPolicy')
        print('    readback:', json.dumps(np), flush=True)
    except Exception:
        pass

DNS_CODE = '''import socket, sys
ip = sys.argv[1]
# TCP DNS 查询 (数据层): A 记录 www.example.com
import struct
tid = b'\\x12\\x34'
hdr = struct.pack('!HHHHHH', 0x1234, 0x0100, 1, 0, 0, 0)
q = b'\\x07example\\x03com\\x00' + struct.pack('!HH', 1, 1)
try:
    s = socket.socket(); s.settimeout(4)
    rc = s.connect_ex((ip, 53))
    print('DNS_CONNECT', rc)
    if rc == 0:
        s.sendall(hdr + q)
        d = s.recv(512)
        print('DNS_RESP', len(d), d[:20])
except Exception as e:
    print('DNS_ERR', type(e).__name__, str(e)[:60])
'''

def dns_probe(ip, tag):
    b64 = base64.b64encode(DNS_CODE.encode()).decode()
    sc = 'echo %s | base64 -d | python3 - %s' % (b64, ip)
    c, r = cmd(sid, 'sh', ['-c', sc], timeout_ms=30000)
    out = parse_data(r).strip()
    print('[%s] %s' % (tag, out[:200]), flush=True)
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
    print('[%s] %s' % (tag, out[:200]), flush=True)
    return out

# E1: custom 空
set_policy({"mode": "custom"}, 'E1-empty')
sc = "curl -sk --max-time 6 https://httpbin.org/anything 2>&1 | head -3"
c, r = cmd(sid, 'sh', ['-c', sc], timeout_ms=30000)
out = parse_data(r)
print('[E1-empty-curl]', 'OK-200' if 'anything' in out or '"args"' in out else 'FAIL(%s)' % out[:80], flush=True)

# E2: allowedCIDRs 8.8.8.0/24
set_policy({"mode": "custom", "allowedCIDRs": ["8.8.8.0/24"]}, 'E2-allowCIDR')
dns_probe('8.8.8.8', 'E2-dns8888')
dns_probe('1.1.1.1', 'E3-dns1111-ctrl')
sc = "curl -sk --max-time 6 https://httpbin.org/anything 2>&1 | head -3"
c, r = cmd(sid, 'sh', ['-c', sc], timeout_ms=30000)
out = parse_data(r)
print('[E2-domain-curl]', 'OK-200' if 'anything' in out or '"args"' in out else 'FAIL(%s)' % out[:80], flush=True)

# E4: allow + deny 同一网段
set_policy({"mode": "custom", "allowedCIDRs": ["8.8.8.0/24"], "deniedCIDRs": ["8.8.8.0/24"]}, 'E4-conflict')
dns_probe('8.8.8.8', 'E4-dns8888')

# E5: allowedCIDRs 私有网段 (显式 allow)
set_policy({"mode": "custom", "allowedCIDRs": ["172.31.0.0/16"]}, 'E5-allowVPC')
pg_probe('E5-PG')

print('=== CIDR DONE ===', flush=True)
