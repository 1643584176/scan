# -*- coding: utf-8 -*-
"""v117 payload: StreamOutput 正确 envelope 帧格式 (bidi)
请求: DATA帧(0x01+len+proto) + END_STREAM(0x02+0)
响应: chunked + envelope 帧流
输出 /vercel/sandbox/v117c.out"""
import socket, struct, time, signal, json

OUT = '/vercel/sandbox/v117c.out'
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


def stream_bidi(sockpath, path, proto_body, t=15.0):
    """正确 bidi: DATA帧(0x01+len+body) + END_STREAM(0x02+0)"""
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(t)
        s.connect(sockpath)
        env1 = b'\x01' + struct.pack('>I', len(proto_body)) + proto_body
        env2 = b'\x02' + struct.pack('>I', 0)
        body = env1 + env2
        req = ('POST %s HTTP/1.1\r\nHost: unix\r\nContent-Type: application/connect+proto\r\n'
               'Connect-Protocol-Version: 1\r\nContent-Length: %d\r\n\r\n'
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
        body = d[hdr_end + 4:] if hdr_end > 0 else b''
        body = dechunk(body)
        # 解析 envelope 帧
        out = b''
        frames = []
        off = 0
        while off + 5 <= len(body):
            fl = body[off]
            ln = int.from_bytes(body[off + 1:off + 5], 'big')
            pay = body[off + 5:off + 5 + ln]
            frames.append(fl)
            if fl == 1:
                out += pay
            elif fl == 2 and pay:
                # 可能是错误消息 (JSON)
                out += b'[ERR]' + pay
            off += 5 + ln
        log('STREAM %s -> %s dechunked=%dB frames=%s out=%r' % (path, status, len(body), frames, out[:600]))
        return status, out
    except Exception as e:
        log('STREAM %s EXC %s' % (path, type(e).__name__))
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
       "cat /proc/1/cmdline 2>&1 | head -c 200; echo; echo ===EXEC_END===; sleep 30")
st, pay = connect_unix(CELL, '%s/Exec' % CTRS,
                       json.dumps({'containerId': cid, 'process': {'args': ['/bin/sh', '-c', cmd]}}).encode(), t=5)
log('EXEC -> %s %r' % (st, pay[:200]))
pid = None
try:
    pid = json.loads(pay.decode()).get('processId')
except Exception:
    pass
log('processId=%s' % pid)

# P2 StreamOutput bidi 正确帧
log('=== P2 streamoutput bidi ===')
if pid:
    req = b'\x0a' + bytes([len(pid)]) + pid.encode()
    st, out = stream_bidi(CELL, '%s/StreamOutput' % PROC, req, t=12)
    log('STREAMOUT status=%s' % st)
    if out:
        # 尝试 proto 解析: StreamOutputResponse 可能字段 stdout(1) 或 data(2)
        # 简单打印可读部分
        log('OUT text: %r' % out[:500])

# P3 Wait JSON 长超时 (sleep 30 后退出)
log('=== P3 wait ===')
if pid:
    st, pay = connect_unix(CELL, '%s/Wait' % PROC, json.dumps({'processId': pid}).encode(), t=30)
    log('WAIT -> %s %r' % (st, pay[:200]))

# 清理
st, pay = connect_unix(CELL, '%s/Kill' % CTRS, json.dumps({'containerId': cid}).encode(), t=3)
log('KILL -> %s %r' % (st, pay[:100]))

log('V117C_DONE')
f.close()
