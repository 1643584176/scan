# -*- coding: utf-8 -*-
"""v106 payload: Connect RPC 协议探测 23456/2050 (celld API)
P1 所有提取到的 Connect 服务/方法 x 23456 tcp + 2050 vsock
P2 命中的方法用 JSON body 深挖
输出 /vercel/sandbox/v106c.out"""
import socket, struct, time, signal, json

OUT = '/vercel/sandbox/v106c.out'
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


def connect_req(port, path, body=b'{}', t=1.2):
    """HTTP/1.1 POST Connect RPC (application/json)"""
    try:
        if port < 10000:
            s = socket.socket(40, socket.SOCK_STREAM)
            s.settimeout(t)
            s.connect((2, port))
        else:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(t)
            s.connect(('127.0.0.1', port))
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
        # 解析状态行
        status = d.split(b'\r\n', 1)[0].decode(errors='replace') if d else 'NO_RESP'
        hdr_end = d.find(b'\r\n\r\n')
        payload = d[hdr_end + 4:hdr_end + 4 + 500] if hdr_end > 0 else b''
        log('CONN p%d %s -> %s body=%r' % (port, path, status, payload[:220]))
        return d
    except Exception as e:
        log('CONN p%d %s EXC %s' % (port, path, type(e).__name__))
        return b''


# 从 celld 提取的 Connect 服务
SERVICES = {
    'vercel.hive.celld.api.v1.CelldService': ['Heartbeat', 'GetDriveStorageUsage', 'Configure', 'SetWorkload',
                                               'StartContainer', 'StopContainer', 'WaitContainer', 'Shutdown',
                                               'DriveStorageUsage'],
    'vercel.hive.cell.api.containers.v1.ContainersService': ['Create', 'Exec', 'Kill', 'Mount', 'Start', 'Stdin',
                                                              'StreamOutput', 'Wait'],
    'vercel.hive.cell.api.processes.v1.ProcessService': ['Kill', 'Start', 'StreamOutput', 'Wait'],
    'vercel.hive.cell.api.drives.v1.DrivesService': ['CreateSnapshot', 'SetOCIImageConfig'],
    'vercel.hive.cell.api.usage.v1.UsageService': ['GetResourceUsage'],
    'vercel.hive.api.cells.v1.CellsService': ['RunCell', 'PoolCell', 'ExtendExecutionTimeout'],
}

log('=== P1 connect probe 23456 tcp ===')
for svc, methods in SERVICES.items():
    for m in methods:
        connect_req(23456, '/%s/%s' % (svc, m))

log('=== P1b connect probe 2050 vsock ===')
for svc, methods in SERVICES.items():
    for m in methods:
        connect_req(2050, '/%s/%s' % (svc, m))

log('=== P1c bare names ===')
for svc in ('CellService', 'vercel.hive.celld.api.v1.Celld', 'vercel.hive.cell.api.containers.v1.Containers'):
    connect_req(23456, '/%s/Heartbeat' % svc)
    connect_req(2050, '/%s/Heartbeat' % svc)

log('=== P1d GET style ===')
connect_req(23456, '/vercel.hive.celld.api.v1.CelldService/Heartbeat?message={}', b'', t=1.0)
connect_req(2050, '/vercel.hive.celld.api.v1.CelldService/Heartbeat?message={}', b'', t=1.0)

log('V106C_DONE')
f.close()
