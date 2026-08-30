# -*- coding: utf-8 -*-
"""host_probe: 沙箱内探测 host 侧服务(共享 netns)
Phase1: 监听表全览(tcp/tcp6 含 uid)
Phase2: 26661 指纹(HTTP/1.1 + h2c + 常见路径)  -- J566 遗留
Phase3: 23456 connect/gRPC 路径矩阵(非404=存在信号)
Phase4: 抽象 unix socket 枚举(@开头) + 连接测试  -- CHECK4/7 遗留
输出落盘 + 哨兵 HOSTPROBE_DONE"""
import socket, time, os, struct

OUT = '/vercel/sandbox/host_probe.out'
f = open(OUT, 'w', encoding='utf-8')


def log(s):
    f.write(str(s) + '\n')
    f.flush()


def http_req(port, method, path, body=None, ct=None, t=4, host='127.0.0.1'):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(t)
        s.connect(('127.0.0.1', port))
        req = '%s %s HTTP/1.1\r\nHost: %s:%d\r\nConnection: close\r\n' % (method, path, host, port)
        if ct:
            req += 'Content-Type: %s\r\n' % ct
        if body is not None:
            req += 'Content-Length: %d\r\n' % len(body)
        req += '\r\n'
        if body is not None:
            req += body
        s.sendall(req.encode())
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


log('=== PHASE1 listen table (uid) ===')
try:
    for fn in ['/proc/net/tcp', '/proc/net/tcp6']:
        for ln in open(fn).read().splitlines()[1:]:
            p = ln.split()
            if p[3] == '0A':
                port = int(p[1].split(':')[1], 16)
                uid = p[7]
                addr = p[1].split(':')[0]
                log('LISTEN %s:%d uid=%s' % (addr, port, uid))
except Exception as e:
    log('listen err %s' % e)

log('=== PHASE2 26661 fingerprint ===')
for m, p in [('GET', '/'), ('GET', '/healthz'), ('GET', '/metrics'), ('GET', '/debug/pprof/'),
             ('GET', '/ws/interactive'), ('POST', '/vercel.sandbox.spawn.v1.SpawnService/Ping'),
             ('POST', '/vercel.hive.celld.api.v1.Celld/Heartbeat')]:
    st, bd = http_req(26661, m, p)
    log('26661 %s %s -> %s | %s' % (m, p, st, bd[:200].replace('\n', ' ')))
    time.sleep(0.2)
# h2c 探测
try:
    import subprocess
    r = subprocess.run(['curl', '-s', '-m', '3', '--http2-prior-knowledge', '-i',
                        'http://127.0.0.1:26661/'], capture_output=True, text=True, timeout=8)
    log('26661 h2c: rc=%d %s' % (r.returncode, r.stdout[:200].replace('\n', ' ')))
except Exception as e:
    log('26661 h2c err %s' % e)

log('=== PHASE3 23456 path matrix ===')
PREFIXES = ['', '/vercel.sandbox.spawn.v1', '/vercel.hive.celld.api.v1',
            '/vercel.hive.celld.api.v1.Celld', '/vercel.hive.celld.api.v1.ContainersService',
            '/vercel.hive.celld.api.v1.ProcessService', '/hive-containers', '/sandbox-controller',
            '/api', '/internal', '/v1', '/grpc.health.v1.Health', '/grpc.health.v1']
METHODS = ['Spawn', 'Kill', 'Ping', 'SpawnInteractive', 'Heartbeat', 'Configure', 'RegisterPort',
           'SetWorkload', 'GetResourceUsage', 'StartContainer', 'StopContainer', 'WaitContainer',
           'Shutdown', 'Create', 'Start', 'Stop', 'Wait', 'Exec', 'Stdin', 'KillServer',
           'StreamOutput', 'CreateSnapshot', 'ListContainers', 'Check', 'GetProcess', 'ListPids',
           'ExecProcess', 'GetImageConfig', 'SetOCIImageConfig', 'Status']
cands = []
for pfx in PREFIXES:
    for m in METHODS:
        if pfx.endswith(m):
            continue
        cands.append('%s/%s' % (pfx, m))
# 去重保序
seen = set()
paths = []
for c in cands:
    if c not in seen:
        seen.add(c)
        paths.append(c)
hits = []
for p in paths:
    st, bd = http_req(23456, 'POST', p, '{}', 'application/json', t=3)
    if '404' not in st and not st.startswith('EXC') and st != 'NORESP':
        hits.append((p, st, bd))
        log('HIT %s -> %s | %s' % (p, st, bd[:300].replace('\n', ' ')))
    time.sleep(0.15)
log('paths tested: %d, non-404: %d' % (len(paths), len(hits)))
# gRPC content-type 变体(取所有路径的 /grpc. 前缀候选)
for p in ['/grpc.health.v1.Health/Check', '/grpc.health.v1.Health/Watch',
          '/grpc.reflection.v1alpha.ServerReflectionInfo/ServerReflectionInfo',
          '/grpc.reflection.v1.ServerReflectionInfo/ServerReflectionInfo']:
    st, bd = http_req(23456, 'POST', p, b'\x00\x00\x00\x00\x00', 'application/grpc', t=3)
    log('grpc %s -> %s | %s' % (p, st, bd[:200].replace('\n', ' ')))

log('=== PHASE4 abstract unix socket enum ===')
try:
    unix = open('/proc/net/unix').read().splitlines()[1:]
    abst = []
    for ln in unix:
        p = ln.split()
        if len(p) < 8:
            continue
        state = p[5]
        path = p[7]
        # 抽象 socket: @ 开头(内核显示为 @ 或 \0) 或空 path
        if path.startswith('@') or (len(p) == 7):
            abst.append((path, state))
    log('abstract sockets: %d' % len(abst))
    for path, state in abst[:40]:
        log('  %s state=%s' % (path, state))
except Exception as e:
    log('unix err %s' % e)

# 尝试连接抽象 socket(@name -> \0name)
try:
    for path, state in abst[:10]:
        name = '\0' + path[1:] if path.startswith('@') else '\0' + path
        try:
            s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            s.settimeout(2)
            s.connect(name)
            log('CONNECT OK %r' % name)
            s.close()
        except Exception as e:
            log('CONNECT %r -> %s' % (name, type(e).__name__))
except Exception as e:
    log('abstract conn err %s' % e)

log('HOSTPROBE_DONE')
f.close()
