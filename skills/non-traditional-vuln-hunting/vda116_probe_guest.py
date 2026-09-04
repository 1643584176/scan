# -*- coding: utf-8 -*-
"""v116 payload: StreamOutput 请求体=纯 proto, 解析响应帧流
P1 Create->Start->Exec -> processId
P2 StreamOutput connect+proto (body=纯 proto, 响应=帧流)
P3 输出解析
输出 /vercel/sandbox/v116c.out"""
import socket, struct, time, signal, json

OUT = '/vercel/sandbox/v116c.out'
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


def stream_proto(sockpath, path, proto_body, t=15.0):
    """POST connect+proto, body=纯 proto, 响应=帧流"""
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(t)
        s.connect(sockpath)
        req = ('POST %s HTTP/1.1\r\nHost: unix\r\nContent-Type: application/connect+proto\r\n'
               'Connect-Protocol-Version: 1\r\nContent-Length: %d\r\n\r\n'
               % (path, len(proto_body))).encode() + proto_body
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
        # 解析帧流: 1B flags + 4B len + payload
        out = b''
        err = b''
        off = 0
        frames = []
        while off + 5 <= len(body):
            fl = body[off]
            ln = int.from_bytes(body[off + 1:off + 5], 'big')
            pay = body[off + 5:off + 5 + ln]
            frames.append(fl)
            if fl & 1:  # DATA
                # connect 数据消息: 内部又是 proto 或 JSON, 直接收
                out += pay
            off += 5 + ln
        log('STREAM %s -> %s body=%dB frames=%s out=%r' % (path, status, len(body), frames, out[:500]))
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

# P2 StreamOutput 纯 proto body
log('=== P2 streamoutput ===')
if pid:
    req = b'\x0a' + bytes([len(pid)]) + pid.encode()
    st, out = stream_proto(CELL, '%s/StreamOutput' % PROC, req, t=12)
    log('STREAMOUT status=%s' % st)
    # 解析 proto StreamOutputResponse: 可能是 {stdout: bytes} 或 {data: bytes}
    # 尝试直接看输出文本
    if out:
        log('RAW OUT: %r' % out[:400])

    # 也试 JSON body + connect+proto content type
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(10)
        s.connect(CELL)
        jb = json.dumps({'processId': pid}).encode()
        req = ('POST %s HTTP/1.1\r\nHost: unix\r\nContent-Type: application/connect+proto\r\n'
               'Connect-Protocol-Version: 1\r\nContent-Length: %d\r\n\r\n' % ('%s/StreamOutput' % PROC, len(jb))).encode() + jb
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
        hdr_end = d.find(b'\r\n\r\n')
        body = d[hdr_end + 4:] if hdr_end > 0 else b''
        log('STREAM json-body %dB %r' % (len(body), body[:300]))
    except Exception as e:
        log('STREAM json-body EXC %s' % type(e).__name__)

# P3 Wait 长超时 (进程 sleep 30 后退出)
log('=== P3 wait ===')
if pid:
    st, pay = connect_unix(CELL, '%s/Wait' % PROC, json.dumps({'processId': pid}).encode(), t=20)
    log('WAIT -> %s %r' % (st, pay[:200]))

# 清理
st, pay = connect_unix(CELL, '%s/Kill' % CTRS, json.dumps({'containerId': cid}).encode(), t=3)
log('KILL -> %s %r' % (st, pay[:100]))

log('V116C_DONE')
f.close()
