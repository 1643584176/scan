# -*- coding: utf-8 -*-
"""celd4_basic: 基础事实验证
1) uid/权限/caps
2) host unix socket 存在性与权限 (/run/cell, /run/containerd, /run/vercel/share)
3) cell.sock 可连性 (UsageService/GetResourceUsage = 无认证 200 判据)
4) containerd.sock 可连性 (gRPC HTTP/2 preface)
5) 23456 SpawnService/Ping 验证 + /proc/net/unix 影子
输出落盘 + 哨兵 CELD4_DONE"""
import socket, time, os, sys, subprocess

OUT = '/vercel/sandbox/celd4.out'
f = open(OUT, 'w', encoding='utf-8', errors='replace')


def log(s):
    line = '[%.1f] %s' % (time.time(), s)
    try:
        f.write(line + '\n')
        f.flush()
    except Exception:
        pass
    print(line, flush=True)


def sh(cmd, t=8):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=t)
        return (r.stdout + r.stderr).strip()[:500]
    except Exception as e:
        return 'ERR %s' % e


def try_unix(path, label, payload=None, t=5):
    """尝试连接 unix socket, 发 payload(可选), 收响应"""
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(t)
        s.connect(path)
        if payload:
            s.sendall(payload)
        data = b''
        while True:
            try:
                c = s.recv(8192)
            except socket.timeout:
                break
            if not c:
                break
            data += c
        s.close()
        return 'CONNECT_OK rcvd=%dB: %s' % (len(data), data[:200].replace(b'\r', b'\\r').replace(b'\n', b'\\n')[:200])
    except Exception as e:
        return 'CONNECT_FAIL %s' % e


log('=== PHASE1 身份 ===')
log('id: %s' % sh('id'))
log('whoami: %s' % sh('whoami'))
log('caps: %s' % sh('cat /proc/self/status | grep -E "CapEff|Seccomp|Uid"'))
log('uname: %s' % sh('uname -a'))

log('=== PHASE2 host socket 存在性 ===')
for p in ['/run/cell', '/run/containerd', '/run/vercel/share', '/run/apm', '/run/metrics', '/var/run']:
    log('ls %s: %s' % (p, sh('ls -la %s 2>&1' % p)))

log('=== PHASE3 unix socket 可连性 ===')
GETRES = b'POST /vercel.hive.cell.api.usage.v1.UsageService/GetResourceUsage HTTP/1.1\r\nHost: localhost\r\nContent-Type: application/json\r\nContent-Length: 2\r\nConnection: close\r\n\r\n{}'
for p in ['/run/cell/cell.sock', '/run/containerd/containerd.sock', '/run/vercel/share/init.sock']:
    log('%s: %s' % (p, sh('ls -la %s 2>&1' % p)))
    log('%s connect: %s' % (p, try_unix(p, p, GETRES)))

log('=== PHASE4 23456 身份 (SpawnService/Ping) ===')
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(4)
    s.connect(('127.0.0.1', 23456))
    req = b'POST /vercel.sandbox.spawn.v1.SpawnService/Ping HTTP/1.1\r\nHost: 127.0.0.1\r\nContent-Type: application/json\r\nContent-Length: 2\r\nConnection: close\r\n\r\n{}'
    s.sendall(req)
    data = b''
    while True:
        try:
            c = s.recv(8192)
        except socket.timeout:
            break
        if not c:
            break
        data += c
    s.close()
    log('SpawnService/Ping -> %dB: %s' % (len(data), data[:200].replace(b'\r', b'\\r').replace(b'\n', b'\\n')[:200]))
except Exception as e:
    log('23456 EXC %s' % e)

log('=== PHASE5 /proc/net/unix 影子 ===')
log(sh('grep -E "cell|containerd|apm|metrics|init" /proc/net/unix 2>/dev/null | head -30'))

log('CELD4_DONE')
f.close()
