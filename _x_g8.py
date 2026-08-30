# -*- coding: utf-8 -*-
"""sandbox-init 精准提取 2 + vsock 面 + 自启动实例协议探测
M1: Go 模块路径 + 路由 + gRPC 服务名 (精准)
M2: vsock 设备/connect host (23456 vsock?)
M3: 连接 /tmp/me.sock 发 probe (协议探测)
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

def run(tag, sc, maxlen=1700):
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
def dump(title, cond, limit=50):
    print('--- %s ---' % title)
    seen=set(); n=0
    for s in strs:
        if cond(s) and s not in seen and len(s)<200:
            seen.add(s); print(s); n+=1
            if n>=limit: break
    print('(%d shown)' % n)
# Go 模块路径
dump('MODULES', lambda s: bool(re.match(r'^[a-z0-9.]+\\.(com|org|io|dev|sh|app)/[a-z0-9_./-]+$', s)) and 'go' not in s.lower())
# 路由 /v1/ /v2/ 或含 api/sandbox
dump('ROUTES', lambda s: bool(re.match(r'^/[a-zA-Z0-9_./-]*[vV][0-9][a-zA-Z0-9_./-]*$', s)) or ('/api/' in s) or ('sandbox' in s.lower() and s.startswith('/')))
# gRPC 服务名 (Service 结尾驼峰)
dump('GRPC-SVC', lambda s: bool(re.match(r'^[A-Z][A-Za-z0-9]+(Service|API|Server)$', s)))
# main 包函数 (main.xxx)
dump('MAIN-FN', lambda s: bool(re.match(r'^main\\.[A-Za-z0-9_]+$', s)), 60)
# cell/snapshot 关键词上下文
dump('CELL-KW', lambda s: ('cell' in s.lower() or 'snapshot' in s.lower() or 'orchestr' in s.lower()) and len(s)<100)
print('DONE')
'''

b64 = base64.b64encode(EXTRACT_CODE.encode()).decode()
run('M1-extract', 'echo %s | base64 -d | python3' % b64, maxlen=2000)

# M2: vsock
VSOCK_CODE = '''import socket, sys
try:
    s = socket.socket(socket.AF_VSOCK, socket.SOCK_STREAM)
    s.settimeout(3)
    s.connect((2, 23456))
    print('VSOCK2_23456_OK')
    s.sendall(b'hello')
    try:
        d = s.recv(100); print('VSOCK_RESP', d)
    except Exception as e:
        print('VSOCK_RECV', type(e).__name__)
except Exception as e:
    print('VSOCK_ERR', type(e).__name__, str(e)[:80])
'''
b64v = base64.b64encode(VSOCK_CODE.encode()).decode()
run('M2-vsock', 'sudo ls -la /dev/vsock 2>&1; echo %s | base64 -d | python3' % b64v)

# M3: 连接自启动实例 (需先启动)
UNIX2_CODE = '''import socket
s=socket.socket(socket.AF_UNIX); s.settimeout(2)
try:
    s.connect('/tmp/me2.sock'); print('ME2_CONNECT_OK')
    s.sendall(b'hello')
    try:
        d=s.recv(100); print('ME2_RESP', d)
    except Exception as e:
        print('ME2_RECV', type(e).__name__)
except Exception as e:
    print('ME2_ERR', type(e).__name__, str(e)[:60])
'''
b64m = base64.b64encode(UNIX2_CODE.encode()).decode()
run('M3-probe', 'sudo /run/vercel/share/sandbox-init -socket /tmp/me2.sock -pubkey i0LREDAQy/qxuiZbECJEbY12v1cvoHbHzg3OETJq7LA= >/tmp/si2.log 2>&1 & sleep 1; echo %s | base64 -d | python3; sudo pkill -f "me2.sock" 2>/dev/null; echo M3_DONE' % b64m)

print('=== G8 DONE ===', flush=True)
