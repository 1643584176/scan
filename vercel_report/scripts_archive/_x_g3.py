# -*- coding: utf-8 -*-
"""Guest 面深入 2: 块设备读取 / virtio1 第二网卡 / 影子 socket / sandbox-init
I1: od 读取 /tmp/rd0 (254:0) + /tmp/rd16 (254:16) 前 2KB 识别文件系统
I2: virtio1 详情 (uevent/net 子目录/driver) + eth0 对应关系
I3: 同会话 /proc/net/unix vs 文件系统 (影子 socket 对照)
I4: sandbox-init 基本信息 (file/strings 头)
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

# I1: od 读设备 (254:0 vs 254:16 对照)
run('I1-rootdev', 'mknod /tmp/rd0 b 254 0 2>&1; mknod /tmp/rd16 b 254 16 2>&1; echo ===RD0===; dd if=/tmp/rd0 bs=512 count=2 2>&1 | od -A x -t x1z | head -24; echo ===RD16===; dd if=/tmp/rd16 bs=512 count=2 2>&1 | od -A x -t x1z | head -24')

# I2: virtio1 第二网卡
run('I2-virtio1', 'echo ==virtio1-uevent==; cat /sys/bus/virtio/devices/virtio1/uevent 2>&1; echo ==net-dir==; ls /sys/bus/virtio/devices/virtio1/net/ 2>&1; echo ==virtio0-net==; ls /sys/bus/virtio/devices/virtio0/net/ 2>&1; echo ==eth0-symlink==; ls -la /sys/class/net/eth0/ 2>&1 | head -5; echo ==ifcfg==; ip link show 2>&1; echo ==routes==; ip route 2>&1')

# I3: 影子 socket 对照
run('I3-unix', 'cat /proc/net/unix 2>&1 | head -25; echo ===LS===; ls -la /run/cell /run/apm /run/vercel 2>&1')

# I4: sandbox-init 基本信息
run('I4-init', 'ls -la /run/vercel/share/sandbox-init; head -c 64 /run/vercel/share/sandbox-init | od -A x -t x1z | head -4; file /run/vercel/share/sandbox-init 2>&1')

print('=== G3 DONE ===', flush=True)
