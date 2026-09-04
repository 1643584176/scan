# -*- coding: utf-8 -*-
"""Guest 面深入 3: 254:0 归属确认 / sandbox-init strings / containerd
J1: ls -la /dev/vd* (设备号归属: 254:0 是否=vda)
J2: 尝试只读挂载 254:0 -> ls 顶层 (确认内容)
J3: sandbox-init strings 侦察 (gRPC/API/路径关键词)
J4: ls /run/containerd (socket 真实性)
"""
import json, sys, time
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

def run(tag, sc, maxlen=1000):
    c, r = cmd(sid, 'sh', ['-c', sc], timeout_ms=60000)
    out = ''
    for line in r.splitlines():
        if '"data"' in line:
            try:
                out += json.loads(line).get('data', '')
            except Exception:
                pass
    print('[%s] %s' % (tag, out[:maxlen]), flush=True)
    return out

# J1: vd 设备号
run('J1-vd', 'ls -la /dev/vd* 2>&1; echo ===; ls -la /dev/ | grep -E "vda|vdb|root" 2>&1')

# J2: 挂载 254:0 (只读)
run('J2-mount', 'mkdir -p /tmp/hfs; mount -o ro /tmp/rd0 /tmp/hfs 2>&1; echo ===; ls -la /tmp/hfs/ 2>&1 | head -30')

# J3: sandbox-init strings (关键词)
run('J3-strings', 'strings -n 8 /run/vercel/share/sandbox-init 2>&1 | grep -iE "grpc|/v[0-9]/|service|method|token|secret|/var/|/etc/|kuber|containerd|cell|snapshot|base_url|/api|http" | head -40')

# J4: containerd
run('J4-containerd', 'ls -la /run/containerd/ 2>&1; echo ===; ls -la /run/containerd/s/ 2>&1 | head -5')

print('=== G4 DONE ===', flush=True)
