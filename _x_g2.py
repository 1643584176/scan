# -*- coding: utf-8 -*-
"""Guest 面深入: 254:0 块设备归属 / cell.sock / apm.sock / virtio 类型 (base64 注入版)
H1: cat /etc/hosts + /etc/resolv.conf (bind 自 254:0, 内容判断来源)
H2: ls /run/vercel/share /run/cell /run/apm (rw 共享目录内容)
H3: mknod 254:0 读取前 512B (host rootfs?) + 254:16 (vdb) 对照
H4: 探测 /run/cell/cell.sock (A 线复活)
H5: 探测 /run/apm/apm.sock
H6: virtio 设备类型 (device/subsystem)
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

def run(tag, sc, maxlen=900):
    c, r = cmd(sid, 'sh', ['-c', sc], timeout_ms=45000)
    out = ''
    for line in r.splitlines():
        if '"data"' in line:
            try:
                out += json.loads(line).get('data', '')
            except Exception:
                pass
    print('[%s] %s' % (tag, out[:maxlen]), flush=True)
    return out

UNIX_CODE = '''import socket,sys
p=sys.argv[1]
s=socket.socket(socket.AF_UNIX)
s.settimeout(3)
try:
    s.connect(p)
    print('CONNECT_OK')
    s.sendall(b'hello')
    try:
        d=s.recv(200); print('RESP', d)
    except Exception as e:
        print('RECV', type(e).__name__)
except Exception as e:
    print('ERR', type(e).__name__, str(e)[:60])
'''

# H1: hosts/resolv 内容 (bind 自 254:0)
run('H1-hosts', 'cat /etc/hosts 2>&1; echo ===; cat /etc/resolv.conf 2>&1')

# H2: 共享目录
run('H2-share', 'ls -la /run/vercel/share/ 2>&1; echo ===; ls -la /run/cell/ /run/apm/ 2>&1')

# H3: mknod 254:0 / 254:16 读取
run('H3-rootdev', 'mknod /tmp/rd0 b 254 0 2>&1; mknod /tmp/rd16 b 254 16 2>&1; dd if=/tmp/rd0 bs=512 count=1 2>/dev/null | xxd | head -12; echo ===VDB===; dd if=/tmp/rd16 bs=512 count=1 2>/dev/null | xxd | head -4')

# H4: cell.sock
b64 = base64.b64encode(UNIX_CODE.encode()).decode()
run('H4-cell', 'ls -la /run/cell/cell.sock 2>&1; echo %s | base64 -d | python3 - /run/cell/cell.sock' % b64)

# H5: apm.sock
run('H5-apm', 'ls -la /run/apm/apm.sock 2>&1; echo %s | base64 -d | python3 - /run/apm/apm.sock' % b64)

# H6: virtio 类型
run('H6-virtio', 'for d in /sys/bus/virtio/devices/virtio*/; do echo "== $d"; cat $d/device 2>/dev/null; cat $d/status 2>/dev/null; ls $d/driver 2>/dev/null; done')

print('=== G2 DONE ===', flush=True)
