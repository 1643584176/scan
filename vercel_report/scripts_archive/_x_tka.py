# -*- coding: utf-8 -*-
"""T 线: HTTP/1.1 keep-alive 连接复用 - 第二请求换 Host 看转发路由"""
import json, sys, time
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, cmd, TEAM, PROJ

c, r = api('GET', '/v2/sandboxes/tinj1?teamId=%s&projectId=%s' % (TEAM, PROJ))
d = json.loads(r)
sid = d['sandbox']['currentSessionId']
print('tinj1 sid:', sid, flush=True)

# python keep-alive: 同一 TLS 连接, 请求1 Host=httpbin.org, 请求2 Host=1.1.1.1
PY = '''
import socket, ssl, time
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
s = socket.create_connection(('httpbin.org', 443), timeout=10)
t = ctx.wrap_socket(s, server_hostname='httpbin.org')
t.sendall(b'GET /anything HTTP/1.1\\r\\nHost: httpbin.org\\r\\nConnection: keep-alive\\r\\n\\r\\n')
time.sleep(0.8)
buf = b''
t.settimeout(5)
try:
    while True:
        d = t.recv(4096)
        if not d: break
        buf += d
        if b'\\r\\n\\r\\n' in buf and b'application/json' in buf or buf.count(b'HTTP/1.1 200') >= 1 and len(buf) > 3000:
            # 第一个响应收完标志: 简单起见收够数据
            if buf.count(b'\\r\\n\\r\\n') >= 1 and len(buf) > 1500:
                break
except Exception as e:
    print('R1_ERR', e)
print('R1_LEN', len(buf), 'R1_HEAD', buf[:80])
# 请求2: 换 Host
t.sendall(b'GET /anything HTTP/1.1\\r\\nHost: 1.1.1.1\\r\\nConnection: close\\r\\nX-Second: 1\\r\\n\\r\\n')
buf2 = b''
t.settimeout(6)
try:
    while True:
        d = t.recv(4096)
        if not d: break
        buf2 += d
except Exception as e:
    print('R2_ERR', type(e).__name__, e)
print('R2_LEN', len(buf2))
print('R2_HEAD', buf2[:400])
print('R2_TAIL', buf2[-300:])
'''
import base64
b64 = base64.b64encode(PY.encode()).decode()
inj = "import base64;open('/vercel/sandbox/ka.py','wb').write(base64.b64decode('%s'))" % b64
c, r = cmd(sid, 'python3', ['-c', inj], timeout_ms=30000)
print('inject:', c, flush=True)
time.sleep(1)
c, r = cmd(sid, 'python3', ['/vercel/sandbox/ka.py'], timeout_ms=60000)
print('=== keepalive ->', c, flush=True)
for line in r.splitlines():
    if '"data"' in line:
        try:
            print(json.loads(line).get('data', '')[:2000], flush=True)
        except Exception:
            pass
print('=== KA DONE ===', flush=True)
