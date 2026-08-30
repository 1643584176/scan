# -*- coding: utf-8 -*-
"""Guest 面系统枚举: mount / dev / virtio / proc 面 (逃逸面检查)
G1 /proc/mounts              挂载点 (virtiofs? host 共享?)
G2 ls /dev                   设备列表 (新设备?)
G3 /sys/bus/virtio/devices/  virtio 设备
G4 /proc/net/unix            unix socket (服务面)
G5 /proc/1/mountinfo         详细挂载
G6 /sys/class/net/           网络接口 (macvtap?)
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

def run(tag, sc):
    c, r = cmd(sid, 'sh', ['-c', sc], timeout_ms=30000)
    out = ''
    for line in r.splitlines():
        if '"data"' in line:
            try:
                out += json.loads(line).get('data', '')
            except Exception:
                pass
    print('[%s] %s' % (tag, out[:800]), flush=True)
    return out

run('G1-mounts', 'cat /proc/mounts 2>&1')
run('G2-dev', 'ls -la /dev/ 2>&1 | head -40')
run('G3-virtio', 'ls /sys/bus/virtio/devices/ 2>&1; for d in /sys/bus/virtio/devices/*/; do echo "== $d"; cat $d/status 2>/dev/null; done')
run('G4-unix', 'cat /proc/net/unix 2>&1 | head -30')
run('G5-mountinfo', 'head -30 /proc/1/mountinfo 2>&1')
run('G6-net', 'ls /sys/class/net/ 2>&1; cat /sys/class/net/*/address 2>&1')

print('=== GUEST DONE ===', flush=True)
