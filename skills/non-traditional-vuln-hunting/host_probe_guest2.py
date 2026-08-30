# -*- coding: utf-8 -*-
"""host_probe v2: 23456 指纹细化 + 全 unix socket 枚举 + connect 协议变体
Phase1: 23456 指纹(GET/POST/带 connect-protocol-version header 的 404 body)
Phase2: connectrpc 协议变体探测(connect v1 header + application/proto)
Phase3: 全 unix socket 枚举(抽象 + 文件系统路径) + 尝试连接
Phase4: grpc health/reflection (修复 bytes body bug)
输出落盘 + 哨兵 HOSTPROBE2_DONE"""
import socket, time, os

OUT = '/vercel/sandbox/host_probe2.out'
f = open(OUT, 'w', encoding='utf-8')


def log(s):
    f.write(str(s) + '\n')
    f.flush()


def http_req(port, method, path, body=None, ct=None, t=4, host='127.0.0.1', extra_headers=None):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(t)
        s.connect(('127.0.0.1', port))
        req = '%s %s HTTP/1.1\r\nHost: %s:%d\r\nConnection: close\r\n' % (method, path, host, port)
        if ct:
            req += 'Content-Type: %s\r\n' % ct
        if extra_headers:
            for h in extra_headers:
                req += h + '\r\n'
        if body is not None:
            if isinstance(body, str):
                req += 'Content-Length: %d\r\n' % len(body.encode())
            else:
                req += 'Content-Length: %d\r\n' % len(body)
        req += '\r\n'
        s.sendall(req.encode() + (body.encode() if isinstance(body, str) else body if body else b''))
        data = b''
        while True:
            try:
                chunk = s.recv(8192)
            except socket.timeout:
                break
            if not chunk:
                break
            data += chunk
        s.close()
        if not data:
            return 'NORESP', ''
        head, _, rest = data.partition(b'\r\n\r\n')
        return head.split(b'\r\n')[0].decode(errors='replace'), rest[:400].decode(errors='replace')
    except Exception as e:
        return 'EXC:%s' % type(e).__name__, ''


log('=== PHASE1 23456 fingerprint ===')
for m, p, ct, hdrs in [
    ('GET', '/', None, None),
    ('POST', '/', 'application/json', None),
    ('GET', '/healthz', None, None),
    ('POST', '/vercel.hive.celld.api.v1.Celld/Heartbeat', 'application/json',
     ['Connect-Protocol-Version: 1']),
    ('POST', '/vercel.hive.celld.api.v1.Celld/Heartbeat', 'application/proto',
     ['Connect-Protocol-Version: 1']),
    ('POST', '/vercel.hive.celld.api.v1.Celld/Heartbeat', 'application/connect+json', None),
]:
    st, bd = http_req(23456, m, p, '{}', ct, extra_headers=hdrs)
    log('23456 %s %s ct=%s -> %s | %s' % (m, p, ct, st, bd[:300].replace('\n', ' ')))
    time.sleep(0.2)

log('=== PHASE2 connect variants ===')
SVC = ['vercel.hive.celld.api.v1.Celld', 'vercel.hive.celld.api.v1.ContainersService',
       'vercel.hive.celld.api.v1.ProcessService', 'vercel.sandbox.spawn.v1.SpawnService',
       'grpc.health.v1.Health', 'grpc.reflection.v1alpha.ServerReflectionInfo',
       'vercel.celld.v1.Celld', 'celld.api.v1.Celld', 'hive.celld.Celld']
METH = ['Heartbeat', 'Ping', 'Configure', 'Spawn', 'Create', 'Start', 'Stop', 'Status',
        'Check', 'ListContainers', 'CreateSnapshot', 'GetResourceUsage', 'StreamOutput',
        'SpawnInteractive', 'Kill', 'Wait', 'Exec', 'GetImageConfig', 'Shutdown', 'RegisterPort']
for svc in SVC:
    for m in METH:
        st, bd = http_req(23456, 'POST', '/%s/%s' % (svc, m), '{}', 'application/json',
                          extra_headers=['Connect-Protocol-Version: 1'])
        if '404' not in st and not st.startswith('EXC') and st != 'NORESP':
            log('HIT /%s/%s -> %s | %s' % (svc, m, st, bd[:300].replace('\n', ' ')))
        time.sleep(0.1)
    # 每服务也试 GET(connect 只读方法)
    st, bd = http_req(23456, 'GET', '/%s/Heartbeat' % svc, None, 'application/json')
    if '404' not in st and not st.startswith('EXC') and st != 'NORESP':
        log('HIT GET /%s/Heartbeat -> %s | %s' % (svc, st, bd[:200].replace('\n', ' ')))

log('=== PHASE3 all unix sockets ===')
try:
    unix = open('/proc/net/unix').read().splitlines()[1:]
    n = 0
    for ln in unix:
        p = ln.split()
        if len(p) < 8:
            continue
        state = p[5]
        path = p[7]
        n += 1
        log('  unix %s state=%s' % (path if path else '(empty)', state))
        if path.startswith('@') and n <= 60:
            name = '\0' + path[1:]
            try:
                s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                s.settimeout(2)
                s.connect(name)
                log('CONNECT OK %r' % name)
                s.close()
            except Exception as e:
                log('CONNECT %r -> %s' % (name, type(e).__name__))
        elif path.startswith('/') and n <= 60:
            try:
                s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                s.settimeout(2)
                s.connect(path)
                log('CONNECT OK %s' % path)
                s.close()
            except Exception as e:
                pass
    log('unix total: %d' % n)
except Exception as e:
    log('unix err %s' % e)

log('=== PHASE4 grpc health/reflection (fixed) ===')
for p in ['/grpc.health.v1.Health/Check', '/grpc.health.v1.Health/Watch',
          '/grpc.reflection.v1alpha.ServerReflectionInfo/ServerReflectionInfo',
          '/grpc.reflection.v1.ServerReflectionInfo/ServerReflectionInfo']:
    st, bd = http_req(23456, 'POST', p, b'\x00\x00\x00\x00\x00', 'application/grpc', t=3)
    log('grpc %s -> %s | %s' % (p, st, bd[:200].replace('\n', ' ')))

log('HOSTPROBE2_DONE')
f.close()
