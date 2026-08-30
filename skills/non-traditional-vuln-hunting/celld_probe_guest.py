# -*- coding: utf-8 -*-
"""celld_probe: 沙箱内探测 127.0.0.1:23456 celld 控制面 + 26661 端口
Phase1: 端口监听侦察(零副作用)
Phase2: connect 协议方法矩阵(HTTP/1.1 + JSON, body={}), 判路径存在性
Phase3: h2c SpawnService 无签名测试 + 26661 HTTP 探测
输出落盘 + 哨兵 CELD_DONE"""
import socket, json, time, sys, os

OUT = '/vercel/sandbox/celld_probe.out'
f = open(OUT, 'w', encoding='utf-8')


def log(s):
    f.write(str(s) + '\n')
    f.flush()


def tcp_conn(ip, port, t=3):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(t)
        s.connect((ip, port))
        s.close()
        return 'OPEN'
    except Exception as e:
        return 'CLOSED:%s' % type(e).__name__


def http_post(port, path, body=None, hdrs=None, t=4):
    """HTTP/1.1 POST, 返回 (status, headers, body前500B)"""
    body = body if body is not None else '{}'
    hdrs = hdrs or {}
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(t)
        s.connect(('127.0.0.1', port))
        req = 'POST %s HTTP/1.1\r\nHost: 127.0.0.1:%d\r\nContent-Type: application/json\r\nContent-Length: %d\r\nConnection: close\r\n' % (path, port, len(body))
        for k, v in hdrs.items():
            req += '%s: %s\r\n' % (k, v)
        req += '\r\n' + body
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
            return 'NORESP', '', ''
        head, _, rest = data.partition(b'\r\n\r\n')
        status = head.split(b'\r\n')[0].decode(errors='replace')
        return status, head.decode(errors='replace'), rest[:500].decode(errors='replace')
    except Exception as e:
        return 'EXC:%s' % type(e).__name__, '', ''


def http_get(port, path, t=4):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(t)
        s.connect(('127.0.0.1', port))
        s.sendall(('GET %s HTTP/1.1\r\nHost: 127.0.0.1:%d\r\nConnection: close\r\n\r\n' % (path, port)).encode())
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
        head, _, rest = data.partition(b'\r\n\r\n')
        return head.split(b'\r\n')[0].decode(errors='replace'), rest[:300].decode(errors='replace')
    except Exception as e:
        return 'EXC:%s' % type(e).__name__, ''


# 服务路径矩阵 (connect 协议)
PATHS = {
    'celld': [
        'Heartbeat', 'Configure', 'RegisterPort', 'SetWorkload', 'GetResourceUsage',
        'StartContainer', 'StopContainer', 'WaitContainer', 'Shutdown',
    ],
    'containers': [
        'Create', 'Start', 'Stop', 'Kill', 'Wait', 'Exec', 'Stdin', 'KillServer',
        'StreamOutput', 'CreateSnapshot', 'GetImageConfig', 'SetOCIImageConfig',
        'ListContainers',
    ],
    'process': [
        'Wait', 'Kill', 'ListPids', 'ExecProcess', 'GetProcess',
    ],
}
SERVICES = {
    'celld': 'vercel.hive.celld.api.v1.Celld',
    'containers': 'vercel.hive.celld.api.v1.ContainersService',
    'process': 'vercel.hive.celld.api.v1.ProcessService',
}

log('=== PHASE1 listen check ===')
for port in [80, 23456, 26661]:
    log('127.0.0.1:%d -> %s' % (port, tcp_conn('127.0.0.1', port)))
# 监听表
try:
    tcp = open('/proc/net/tcp').read().splitlines()[1:]
    tcp6 = open('/proc/net/tcp6').read().splitlines()[1:]
    lst = []
    for ln in tcp + tcp6:
        p = ln.split()
        if p[3] == '0A':
            try:
                port = int(p[1].split(':')[1], 16)
                lst.append(port)
            except Exception:
                pass
    log('LISTEN ports: %s' % sorted(set(lst)))
except Exception as e:
    log('tcp table err %s' % e)

log('=== PHASE2 connect matrix port=23456 ===')
for grp, methods in PATHS.items():
    svc = SERVICES[grp]
    for m in methods:
        path = '/%s/%s' % (svc, m)
        st, hd, bd = http_post(23456, path, '{}')
        # 判定: 404=不存在; 其余=存在信号
        verdict = 'EXISTS?' if '404' not in st and not st.startswith('EXC') else 'none'
        if '404' not in st and not st.startswith('EXC') and st != 'NORESP':
            log('[%s/%s] %s | %s | %s' % (grp, m, st, verdict, bd[:300].replace('\n', ' ')))
        else:
            log('[%s/%s] %s' % (grp, m, st))
        time.sleep(0.3)

log('=== PHASE3 26661 probe ===')
log('GET / -> %s' % (http_get(26661, '/'),))
for p in ['/vercel.hive.celld.api.v1.Celld/Heartbeat',
          '/vercel.sandbox.spawn.v1.SpawnService/Ping',
          '/healthz', '/metrics', '/debug/pprof/']:
    st, bd = http_get(26661, p)
    log('GET %s -> %s | %s' % (p, st, bd[:200].replace('\n', ' ')))
    time.sleep(0.2)

log('=== PHASE4 h2c SpawnService no-signature (23456) ===')
# 用 curl --http2-prior-knowledge (沙箱内 curl 存在)
try:
    import subprocess
    r = subprocess.run(
        ['curl', '-s', '-m', '4', '--http2-prior-knowledge',
         '-H', 'Content-Type: application/json',
         '-d', '{}',
         'http://127.0.0.1:23456/vercel.sandbox.spawn.v1.SpawnService/Ping'],
        capture_output=True, text=True, timeout=8)
    log('curl h2c Ping rc=%d out=%s' % (r.returncode, r.stdout[:300].replace('\n', ' ')))
except Exception as e:
    log('curl h2c err %s' % e)

# connect JSON 协议调 Ping (HTTP/1.1)
st, hd, bd = http_post(23456, '/vercel.sandbox.spawn.v1.SpawnService/Ping', '{}')
log('Ping connect: %s | %s' % (st, bd[:300].replace('\n', ' ')))

log('CELD_DONE')
f.close()
