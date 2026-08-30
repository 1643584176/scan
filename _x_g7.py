# -*- coding: utf-8 -*-
"""sandbox-init 精准逆向: gRPC 方法/URL/端口 + 真实 pubkey 启动观察
L1: 提取 gRPC 方法模式 (/pkg.Service/Method)
L2: 提取 URL/端口模式 (http(s):// IP:port :port)
L3: 提取路径模式 (/var /etc /run /usr)
L4: 真实 pubkey 启动 sandbox-init 观察连接目标/行为
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

def run(tag, sc, maxlen=1600):
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
print('--- GRPC METHODS (slash patterns) ---')
seen=set()
for s in strs:
    if re.match(r'^/[A-Za-z0-9_.]+/[A-Za-z0-9_.]+$', s) and s not in seen:
        seen.add(s); print(s)
        if len(seen)>60: break
print('--- URLS ---')
seen=set()
for s in strs:
    if re.search(r'https?://', s) and s not in seen:
        seen.add(s); print(s)
        if len(seen)>40: break
print('--- IP:PORT ---')
seen=set()
for s in strs:
    if re.search(r'\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}:\\d+', s) and s not in seen:
        seen.add(s); print(s)
        if len(seen)>40: break
print('--- PATHS ---')
seen=set()
for s in strs:
    if re.match(r'^/(var|etc|usr|run|tmp|home|opt|vercel)/', s) and s not in seen:
        seen.add(s); print(s)
        if len(seen)>40: break
print('--- AUTH WORDS ---')
seen=set()
for s in strs:
    if re.search(r'(bearer|authorization|api[_-]?key|access[_-]?token|secret|credential)', s, re.I) and len(s)<120 and s not in seen:
        seen.add(s); print(s)
        if len(seen)>40: break
print('DONE')
'''

b64 = base64.b64encode(EXTRACT_CODE.encode()).decode()
run('L1-extract', 'echo %s | base64 -d | python3' % b64, maxlen=1800)

# L4: 真实 pubkey 启动
run('L4-run', 'sudo /run/vercel/share/sandbox-init -socket /tmp/me.sock -pubkey i0LREDAQy/qxuiZbECJEbY12v1cvoHbHzg3OETJq7LA= >/tmp/si.log 2>&1 & sleep 2; ls -la /tmp/me.sock 2>&1; echo ===LOG===; cat /tmp/si.log 2>&1 | head -5; echo ===PS===; ps aux 2>&1 | grep -i "me.sock" | head -3; echo ===NET===; sudo cat /proc/net/tcp 2>/dev/null | head -8; sudo pkill -f "me.sock" 2>/dev/null; echo L4_DONE')

print('=== G7 DONE ===', flush=True)
