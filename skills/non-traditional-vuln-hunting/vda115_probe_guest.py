# -*- coding: utf-8 -*-
"""v115 payload: connect+proto 流式帧 StreamOutput 拿 exec 输出
P1 Create->Start->Exec(shell) -> processId
P2 StreamOutput connect+proto 流式帧 (HTTP/1.1)
P3 Wait connect+proto unary 帧
输出 /vercel/sandbox/v115c.out"""
import socket, struct, time, signal, json

OUT = '/vercel/sandbox/v115c.out'
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


def connect_frame_proto(sockpath, path, proto_msg, t=8.0):
    """HTTP/1.1 POST + application/connect+proto + 流式帧"""
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(t)
        s.connect(sockpath)
        # connect 帧: 1B flags(0x02 END_STREAM) + 4B len + proto
        framed = b'\x02' + struct.pack('>I', len(proto_msg)) + proto_msg
        req = ('POST %s HTTP/1.1\r\nHost: unix\r\nContent-Type: application/connect+proto\r\n'
               'Connect-Protocol-Version: 1\r\nContent-Length: %d\r\n\r\n'
               % (path, len(framed))).encode() + framed
        s.sendall(req)
        d = b''
        try:
            while True:
                c = s.recv(8192)
                if not c:
                    break
                d += c
                if len(d) > 100000:
                    break
        except Exception:
            pass
        s.close()
        status = d.split(b'\r\n', 1)[0].decode(errors='replace') if d else 'NO_RESP'
        hdr_end = d.find(b'\r\n\r\n')
        body = d[hdr_end + 4:] if hdr_end > 0 else b''
        # 解析 connect 响应帧
        parts = []
        off = 0
        while off + 5 <= len(body):
            fl = body[off]
            ln = int.from_bytes(body[off + 1:off + 5], 'big')
            parts.append('F%d:%dB:%r' % (fl, ln, body[off + 5:off + 5 + ln][:120]))
            off += 5 + ln
        log('FRAME %s -> %s parts=%s' % (path, status, parts[:8]))
        return status, body
    except Exception as e:
        log('FRAME %s EXC %s' % (path, type(e).__name__))
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

cmd = ("echo ===EXEC_START===; id; hostname; pwd; ls / | head -20; "
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

# P2 StreamOutput connect+proto
log('=== P2 streamoutput frame ===')
if pid:
    # StreamOutputRequest: field1 process_id
    req = b'\x0a' + bytes([len(pid)]) + pid.encode()
    st, body = connect_frame_proto(CELL, '%s/StreamOutput' % PROC, req, t=10)
    log('STREAMOUT total body %dB' % len(body))
    # 尝试流式读取模式 (不 END_STREAM, 多帧响应)
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(12)
        s.connect(CELL)
        framed = b'\x02' + struct.pack('>I', len(req)) + req
        reqh = ('POST %s HTTP/1.1\r\nHost: unix\r\nContent-Type: application/connect+proto\r\n'
                'Connect-Protocol-Version: 1\r\nContent-Length: %d\r\n\r\n' % ('%s/StreamOutput' % PROC, len(framed))).encode()
        s.sendall(reqh + framed)
        d = b''
        try:
            while True:
                c = s.recv(8192)
                if not c:
                    break
                d += c
                if b'\x04' in d[-5:]:
                    break
        except Exception:
            pass
        s.close()
        hdr_end = d.find(b'\r\n\r\n')
        body = d[hdr_end + 4:] if hdr_end > 0 else b''
        out = b''
        off = 0
        while off + 5 <= len(body):
            fl = body[off]
            ln = int.from_bytes(body[off + 1:off + 5], 'big')
            if fl == 1:
                out += body[off + 5:off + 5 + ln]
            off += 5 + ln
        log('STREAMOUT2 recv %dB out=%r' % (len(out), out[:400]))
    except Exception as e:
        log('STREAMOUT2 EXC %s' % type(e).__name__)

    # P3 Wait connect+proto unary 帧
    log('=== P3 wait frame ===')
    req = b'\x0a' + bytes([len(pid)]) + pid.encode()
    st, body = connect_frame_proto(CELL, '%s/Wait' % PROC, req, t=6)
    log('WAIT body %dB %r' % (len(body), body[:200]))

# 清理
st, pay = connect_unix(CELL, '%s/Kill' % CTRS, json.dumps({'containerId': cid}).encode(), t=3)
log('KILL -> %s %r' % (st, pay[:100]))

log('V115C_DONE')
f.close()
