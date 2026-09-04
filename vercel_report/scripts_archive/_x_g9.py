# -*- coding: utf-8 -*-
"""sandbox-init 协议深挖: proto 字段 / Ping 无签名 / HTTPProxy / sudo vsock
N1: 提取 spawn proto 字段名 + service 名 + HTTPProxy 上下文
N2: init.sock Connect RPC Ping (无签名) -> 未签名方法?
N3: sudo vsock connect 2:23456 (A 线补充)
N4: HTTPProxy 字符串上下文 (上游地址?)
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

def run(tag, sc, maxlen=1800):
    c, r = cmd(sid, 'sh', ['-c', sc], timeout_ms=90000)
    out = ''
    for line in r.splitlines():
        if '"data"' in line:
            try:
                out += json.loads(line).get('data', '')
            except Exception:
                pass
    print('[%s] %s' % (tag, out[:maxlen]), flush=True)
    return out

EXTRACT_CODE = '''import re
data = open('/run/vercel/share/sandbox-init','rb').read()
strs = [s.decode('utf-8','replace') for s in re.findall(rb'[\\x20-\\x7e]{4,}', data)]
def dump(title, cond, limit=60):
    print('--- %s ---' % title)
    seen=set(); n=0
    for s in strs:
        if cond(s) and s not in seen and len(s)<160:
            seen.add(s); print(s); n+=1
            if n>=limit: break
    print('(%d shown)' % n)
# spawn 相关字段 (驼峰 Request/Response 字段)
dump('SPAWN-FIELDS', lambda s: ('Request' in s or 'Response' in s or 'Event' in s) and 'connect' not in s)
# service 名 (spawnv1...)
dump('SERVICE', lambda s: bool(re.match(r'^[A-Za-z0-9]*(v1|V1)[A-Za-z0-9]*$', s)) or 'spawnv1' in s.lower())
# HTTPProxy 上下文 (前后 40 字节)
i = data.find(b'HTTPProxy')
if i>0:
    ctx = data[max(0,i-300):i+300]
    print('--- HTTPPROXY CTX ---')
    print(ctx.decode('utf-8','replace').replace('\\x00','|')[:500])
# URL 列表 (http:// https:// 短串)
dump('URLS', lambda s: ('http://' in s or 'https://' in s) and len(s)<80, 30)
print('DONE')
'''

b64 = base64.b64encode(EXTRACT_CODE.encode()).decode()
run('N1-extract', 'echo %s | base64 -d | python3' % b64, maxlen=2100)

# N2: init.sock Connect RPC Ping (无签名)
PING_CODE = '''import socket
s=socket.socket(socket.AF_UNIX); s.settimeout(4)
try:
    s.connect('/run/vercel/share/init.sock')
    print('INIT_CONNECT_OK')
    req = b'POST /spawnv1.SpawnService/Ping HTTP/1.1\\r\\nHost: localhost\\r\\nContent-Type: application/json\\r\\nContent-Length: 2\\r\\n\\r\\n{}'
    s.sendall(req)
    d = s.recv(400)
    print('PING_RESP', repr(d[:300]))
except Exception as e:
    print('INIT_ERR', type(e).__name__, str(e)[:80])
'''
b64p = base64.b64encode(PING_CODE.encode()).decode()
run('N2-ping', 'echo %s | base64 -d | python3' % b64p)

# N3: sudo vsock
VSOCK2_CODE = '''import socket
for cid,port in [(2,23456),(2,2379),(2,443),(1,23456)]:
    try:
        s = socket.socket(socket.AF_VSOCK, socket.SOCK_STREAM)
        s.settimeout(3)
        s.connect((cid, port))
        print('VSOCK_OK', cid, port)
        s.close()
    except Exception as e:
        print('VSOCK_ERR', cid, port, type(e).__name__, str(e)[:50])
'''
b64v = base64.b64encode(VSOCK2_CODE.encode()).decode()
run('N3-vsock', 'echo %s | base64 -d | sudo python3' % b64v)

print('=== G9 DONE ===', flush=True)
