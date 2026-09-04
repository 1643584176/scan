# -*- coding: utf-8 -*-
"""v121 payload: StreamOutput 持续输出进程 + 长连接收数据
P_f2=1 证明 output_stream=1(STDOUT) 有效, 但需要进程持续输出
P1 Create->Start->Exec(持续输出 60s)
P2 StreamOutput f2=1 长连接 20s 收数据帧
P3 StreamOutput f2=2 10s
P4 再次 Exec 新进程 + StreamOutput f2=1
输出 /vercel/sandbox/v121c.out"""
import socket, struct, time, signal, json

OUT = '/vercel/sandbox/v121c.out'
f = open(OUT, 'w', encoding='utf-8', errors='replace')
signal.alarm(240)


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


def dechunk(d):
    """去除 HTTP chunked 编码"""
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


def stream_bidi_long(sockpath, path, payload, ctype, t=20.0):
    """DATA帧 + shutdown + 长 recv (不提前关闭, 收完所有数据帧)"""
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
        out = b''
        frames = []
        off = 0
        while off + 5 <= len(body):
            fl = body[off]
            ln = int.from_bytes(body[off + 1:off + 5], 'big')
            pay = body[off + 5:off + 5 + ln]
            frames.append(fl)
            out += pay
            off += 5 + ln
        return status, out, frames
    except Exception as e:
        return 'EXC %s' % type(e).__name__, b'', []


def pvarint(n):
    out = bytearray()
    while n > 127:
        out.append((n & 127) | 128)
        n >>= 7
    out.append(n)
    return bytes(out)


def dump_frames(out):
    """解析 StreamOutputResponse proto 帧: 尝试提取字段"""
    txt = ''.join(chr(b) for b in out if 32 <= b < 127 or b in (10, 13))
    return txt


CELL = '/run/cell/cell.sock'
CTRS = '/vercel.hive.cell.api.containers.v1.ContainersService'
PROC = '/vercel.hive.cell.api.processes.v1.ProcessService'
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

st, pay = connect_unix(CELL, '%s/Start' % CTRS, json.dumps({'containerId': cid}).encode(), t=8)
log('START -> %s' % st)

# 持续输出 60 秒
cmd = ("echo ===EXEC_START===; id; i=0; while [ $i -lt 60 ]; do "
       "echo TICK$i $(date +%s); i=$((i+1)); sleep 1; done; echo ===EXEC_END===")
st, pay = connect_unix(CELL, '%s/Exec' % CTRS,
                       json.dumps({'containerId': cid, 'process': {'args': ['/bin/sh', '-c', cmd]}}).encode(), t=5)
log('EXEC -> %s %r' % (st, pay[:200]))
pid = None
try:
    pid = json.loads(pay.decode()).get('processId')
except Exception:
    pass
log('processId=%s' % pid)

# P2 StreamOutput f2=1 stdout 长连接
log('=== P2 streamoutput stdout ===')
if pid:
    pb = pid.encode()
    payload = b'\x0a' + bytes([len(pb)]) + pb + b'\x10\x01'
    st, out, frames = stream_bidi_long(CELL, '%s/StreamOutput' % PROC, payload,
                                       'application/connect+proto', t=20)
    log('SO1 -> %s frames=%s raw=%dB' % (st, frames, len(out)))
    if out:
        log('SO1 text: %r' % dump_frames(out)[:800])
        if b'TICK' in out or b'EXEC_START' in out:
            log('!!!!! GOT STDOUT !!!!!')

# P3 StreamOutput f2=2 stderr 10s
log('=== P3 streamoutput stderr ===')
if pid:
    pb = pid.encode()
    payload = b'\x0a' + bytes([len(pb)]) + pb + b'\x10\x02'
    st, out, frames = stream_bidi_long(CELL, '%s/StreamOutput' % PROC, payload,
                                       'application/connect+proto', t=10)
    log('SO2 -> %s frames=%s raw=%dB' % (st, frames, len(out)))
    if out:
        log('SO2 text: %r' % dump_frames(out)[:400])

# P4 新 Exec + StreamOutput
log('=== P4 new exec ===')
st, pay = connect_unix(CELL, '%s/Exec' % CTRS,
                       json.dumps({'containerId': cid,
                                   'process': {'args': ['/bin/sh', '-c',
                                                        'echo HELLO_NEW_PROC; sleep 30']}}).encode(), t=5)
log('EXEC2 -> %s %r' % (st, pay[:200]))
pid2 = None
try:
    pid2 = json.loads(pay.decode()).get('processId')
except Exception:
    pass
log('processId2=%s' % pid2)
if pid2:
    pb = pid2.encode()
    payload = b'\x0a' + bytes([len(pb)]) + pb + b'\x10\x01'
    st, out, frames = stream_bidi_long(CELL, '%s/StreamOutput' % PROC, payload,
                                       'application/connect+proto', t=12)
    log('SO3 -> %s frames=%s raw=%dB' % (st, frames, len(out)))
    if out:
        log('SO3 text: %r' % dump_frames(out)[:400])
        if b'HELLO_NEW_PROC' in out or b'HELLO' in out:
            log('!!!!! GOT EXEC2 OUTPUT !!!!!')

# 清理
st, pay = connect_unix(CELL, '%s/Kill' % CTRS, json.dumps({'containerId': cid}).encode(), t=3)
log('KILL -> %s %r' % (st, pay[:100]))

log('V121C_DONE')
f.close()
