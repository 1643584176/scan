# -*- coding: utf-8 -*-
"""guest_fast: 快速 host 面筛选(30s级)
1. 监听表(tcp + uid)
2. unix socket 全列表(state + 路径) + cell/metrics 连接测试
3. 23456 基础指纹
输出落盘 + 哨兵 FASTPROBE_DONE"""
import socket, time, os

OUT = '/vercel/sandbox/fast_probe.out'
f = open(OUT, 'w', encoding='utf-8')


def log(s):
    f.write(str(s) + '\n')
    f.flush()


def unix_conn(path, t=3):
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(t)
        s.connect(path)
        s.close()
        return 'CONNECT_OK'
    except Exception as e:
        return 'EXC:%s' % type(e).__name__


log('=== LISTEN tcp ===')
try:
    for fn in ['/proc/net/tcp', '/proc/net/tcp6']:
        for ln in open(fn).read().splitlines()[1:]:
            p = ln.split()
            if p[3] == '0A':
                log('LISTEN %s:%d uid=%s' % (p[1].split(':')[0], int(p[1].split(':')[1], 16), p[7]))
except Exception as e:
    log('tcp err %s' % e)

log('=== UNIX sockets ===')
try:
    unix = open('/proc/net/unix').read().splitlines()[1:]
    log('count=%d' % len(unix))
    for ln in unix:
        p = ln.split()
        if len(p) < 8:
            continue
        log('  %s state=%s' % (p[7] if p[7] else '(empty)', p[5]))
except Exception as e:
    log('unix err %s' % e)

log('=== cell/metrics/init/containerd conn ===')
for path in ['/run/cell/cell.sock', '/run/metrics/metrics.sock',
             '/run/vercel/share/init.sock', '/run/containerd/containerd.sock']:
    log('%s -> %s' % (path, unix_conn(path)))

log('=== 23456/30001/30002/26661 fingerprint ===')
for port in [23456, 26661, 30001, 30002]:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(3)
        r = s.connect_ex(('127.0.0.1', port))
        log('%d connect_ex=%d' % (port, r))
        if r == 0:
            req = 'GET / HTTP/1.1\r\nHost: 127.0.0.1:%d\r\nConnection: close\r\n\r\n' % port
            s.sendall(req.encode())
            data = b''
            while True:
                try:
                    chunk = s.recv(4096)
                except socket.timeout:
                    break
                if not chunk:
                    break
                data += chunk
            log('%d GET / -> %s | %s' % (port, data.split(b'\r\n')[0].decode(errors='replace'), data.split(b'\r\n\r\n')[-1][:100].decode(errors='replace').replace('\n', ' ')))
        s.close()
    except Exception as e:
        log('%d EXC:%s' % (port, type(e).__name__))

log('FASTPROBE_DONE')
f.close()
