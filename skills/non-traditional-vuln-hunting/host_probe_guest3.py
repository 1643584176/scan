# -*- coding: utf-8 -*-
"""host_probe v3: 新面深化
Phase1: /run/cell/cell.sock 连接 + HTTP/RAW 协议交互
Phase2: /run/metrics/metrics.sock 连接 + 读数据(HTTP GET /)
Phase3: /run/apm/apm.sock + containerd 变体连接测试(全记录)
Phase4: 23456 快速字典(Go 常见路径 + celld 变体)
输出落盘 + 哨兵 HOSTPROBE3_DONE"""
import socket, time, os

OUT = '/vercel/sandbox/host_probe3.out'
f = open(OUT, 'w', encoding='utf-8')


def log(s):
    f.write(str(s) + '\n')
    f.flush()


def unix_req(path, req_bytes, t=5, recv_bytes=65536):
    """连接 unix socket, 发送原始字节, 读取响应"""
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(t)
        s.connect(path)
        if req_bytes:
            s.sendall(req_bytes)
        data = b''
        while True:
            try:
                chunk = s.recv(recv_bytes)
            except socket.timeout:
                break
            if not chunk:
                break
            data += chunk
        s.close()
        return 'OK', data[:4000]
    except Exception as e:
        return 'EXC:%s' % type(e).__name__, b''


log('=== PHASE1 cell.sock ===')
for name, req in [
    ('raw-empty', b''),
    ('http-get', b'GET / HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n'),
    ('http-healthz', b'GET /healthz HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n'),
    ('http-post-json', b'POST / HTTP/1.1\r\nHost: localhost\r\nContent-Type: application/json\r\nContent-Length: 2\r\nConnection: close\r\n\r\n{}'),
    ('grpc-empty', b'\x00\x00\x00\x00\x00'),
]:
    st, data = unix_req('/run/cell/cell.sock', req)
    log('cell.sock %s -> %s | %s' % (name, st, data[:300].decode(errors='replace').replace('\n', ' ')))

log('=== PHASE2 metrics.sock ===')
for name, req in [
    ('raw-empty', b''),
    ('http-get', b'GET / HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n'),
    ('http-metrics', b'GET /metrics HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n'),
]:
    st, data = unix_req('/run/metrics/metrics.sock', req)
    log('metrics.sock %s -> %s | %s' % (name, st, data[:300].decode(errors='replace').replace('\n', ' ')))

log('=== PHASE3 other sockets ===')
for path in ['/run/apm/apm.sock', '/run/containerd/containerd.sock',
             '/run/containerd/containerd.sock.ttrpc', '/run/cell/cell.sock']:
    st, data = unix_req(path, b'')
    log('conn %s -> %s' % (path, st))
    if data:
        log('  data: %s' % data[:200].decode(errors='replace').replace('\n', ' '))
    time.sleep(0.2)

log('=== PHASE4 23456 dict ===')
DICT = ['/api', '/api/v1', '/v1', '/v2', '/internal', '/internal/health', '/debug',
        '/debug/pprof', '/debug/pprof/', '/metrics', '/health', '/healthz', '/readyz',
        '/livez', '/version', '/status', '/info', '/ping', '/pong', '/', '/favicon.ico',
        '/vercel.hive.celld.api.v1.Celld/Heartbeat', '/vercel.hive.celld.api.v1.Celld/Configure',
        '/celld', '/sandbox', '/sandboxes', '/cell', '/containers', '/rpc', '/grpc',
        '/vercel.celld.v1.Celld/Heartbeat', '/hive.celld.v1.Celld/Heartbeat',
        '/celld.v1.Celld/Heartbeat', '/api/celld', '/api/v1/celld', '/ws', '/websocket',
        '/connect', '/con', '/service', '/services', '/controller', '/agent', '/node',
        '/sock', '/socket', '/unix', '/healthcheck', '/hc', '/ready', '/init', '/boot',
        '/start', '/stop', '/spawn', '/exec', '/shell', '/console', '/attach', '/logs']
hits = []
for p in DICT:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(3)
        s.connect(('127.0.0.1', 23456))
        req = 'GET %s HTTP/1.1\r\nHost: 127.0.0.1:23456\r\nConnection: close\r\n\r\n' % p
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
        s.close()
        line = data.split(b'\r\n')[0].decode(errors='replace')
        if '404' not in line:
            hits.append((p, line, data[:200]))
            log('HIT %s -> %s' % (p, line))
    except Exception as e:
        log('dict %s -> EXC:%s' % (p, type(e).__name__))
    time.sleep(0.1)
log('dict tested: %d, non-404: %d' % (len(DICT), len(hits)))

log('HOSTPROBE3_DONE')
f.close()
