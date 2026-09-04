# -*- coding: utf-8 -*-
"""v119 payload: StreamOutput 只发 DATA 帧 + shutdown(SHUT_WR) 结束请求流
v118 证明: END_STREAM 空帧会被当 JSON 错误解析 (unexpected end of JSON input)
结论: 客户端不能发 END_STREAM 帧, 用 EOF 结束请求流
C1: DATA帧 proto payload + connect+proto
C2: DATA帧 JSON payload + connect+json
输出 /vercel/sandbox/v119c.out"""
import socket, struct, time, signal, json

OUT = '/vercel/sandbox/v119c.out'
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


def stream_data(sockpath, path, payload, ctype, t=15.0):
    """只发 DATA帧(0x00+len+payload), shutdown(SHUT_WR) 结束请求流"""
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(t)
        s.connect(sockpath)
        env1 = b'\x00' + struct.pack('>I', len(payload)) + payload
        req = ('POST %s HTTP/1.1\r\nHost: unix\r\nContent-Type: %s\r\n'
               'Connect-Protocol-Version: 1\r\nContent-Length: %d\r\n\r\n'
               % (path, ctype, len(env1))).encode() + env1
        s.sendall(req)
        # 关键: 半关闭写端, 服务器读 body EOF -> 请求流结束
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
        log('STREAM %s [%s] -> %s dechunked=%dB frames=%s out=%r'
            % (ctype, path.split('/')[-1], status, len(body), frames, out[:700]))
        return status, out
    except Exception as e:
        log('STREAM %s [%s] EXC %s' % (ctype, path.split('/')[-1], type(e).__name__))
        return 'EXC', b''


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

cmd = ("echo ===EXEC_START===; id; hostname; pwd; echo; "
       "cat /proc/1/cmdline 2>&1 | head -c 200; echo; echo ===EXEC_END===; sleep 40")
st, pay = connect_unix(CELL, '%s/Exec' % CTRS,
                       json.dumps({'containerId': cid, 'process': {'args': ['/bin/sh', '-c', cmd]}}).encode(), t=5)
log('EXEC -> %s %r' % (st, pay[:200]))
pid = None
try:
    pid = json.loads(pay.decode()).get('processId')
except Exception:
    pass
log('processId=%s' % pid)

# P2 C1: DATA 帧 proto + shutdown
log('=== P2 C1 data-frame proto ===')
if pid:
    preq = b'\x0a' + bytes([len(pid)]) + pid.encode()
    st, out = stream_data(CELL, '%s/StreamOutput' % PROC, preq, 'application/connect+proto', t=15)
    log('C1 status=%s' % st)
    if out:
        try:
            txt = ''.join(chr(b) for b in out if 32 <= b < 127 or b in (10, 13))
            log('C1 ascii: %r' % txt[:500])
        except Exception:
            pass

# P3 C2: DATA 帧 JSON + shutdown
log('=== P3 C2 data-frame json ===')
if pid:
    jpay = json.dumps({'processId': pid}).encode()
    st, out = stream_data(CELL, '%s/StreamOutput' % PROC, jpay, 'application/connect+json', t=15)
    log('C2 status=%s' % st)
    if out:
        try:
            txt = ''.join(chr(b) for b in out if 32 <= b < 127 or b in (10, 13))
            log('C2 ascii: %r' % txt[:500])
        except Exception:
            pass

# P4 wait + 清理
log('=== P4 wait ===')
if pid:
    st, pay = connect_unix(CELL, '%s/Wait' % PROC, json.dumps({'processId': pid}).encode(), t=30)
    log('WAIT -> %s %r' % (st, pay[:200]))

st, pay = connect_unix(CELL, '%s/Kill' % CTRS, json.dumps({'containerId': cid}).encode(), t=3)
log('KILL -> %s %r' % (st, pay[:100]))

log('V119C_DONE')
f.close()
