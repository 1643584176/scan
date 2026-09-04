# -*- coding: utf-8 -*-
"""v190 阶段B: 用户 - Remove 宿主标记文件测试 (guest-A 创建, 用户删, guest-C 验证)"""
import socket, json, time

OUT = '/vercel/sandbox/v190u.out'
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


FS = 'vercel.sandbox.api.controller.v1.FileSystemService'
log('=== 1 Remove host marker ===')
# guest-A 创建的 /proc/1/root/tmp/v190rm.txt
for path in ['/proc/1/root/tmp/v190rm.txt', '/tmp/v190rm.txt']:
    st, pay = tcp(23456, '/' + FS + '/Remove', {'path': path}, t=3)
    log('RM %s -> %s %r' % (path, st, pay[:300]))
    time.sleep(0.3)

log('=== 2 remove sandbox test file (control) ===')
open('/vercel/sandbox/v190ctl.txt', 'w').write('CTL190')
st, pay = tcp(23456, '/' + FS + '/Remove', {'path': '/vercel/sandbox/v190ctl.txt'}, t=3)
log('RM ctl -> %s %r' % (st, pay[:300]))
import os
try:
    os.stat('/vercel/sandbox/v190ctl.txt')
    log('CTL EXISTS')
except Exception:
    log('CTL GONE')

log('V190U_DONE')
f.close()
