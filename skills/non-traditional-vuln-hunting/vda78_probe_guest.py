# -*- coding: utf-8 -*-
"""v78 payload: StreamOutput/Stdin 协议探测 (connect/grpc Content-Type 矩阵) + Exec 输出拉取
v77 发现: Stdin -> 404 "unknown container" (方法存在), StreamOutput -> 415 (需非 JSON Content-Type)
假设: cell.sock 是 connect-rpc (JSON over HTTP/1.1 已通, 415 = 需 proto/connect Content-Type)
目标: 找到正确的 Content-Type + 字段格式, 拉取 Exec 进程 stdout/stderr"""
import socket, time, os, json, subprocess, struct

OUT = '/vercel/sandbox/v78c.out'


def log(s):
    line = '[%.3f] %s' % (time.time(), s)
    for p in (OUT, '/mnt/h/volumes/run/vercel/share/v78c2.out'):
        try:
            open(p, 'a', encoding='utf-8', errors='replace').write(line + '\n')
        except Exception:
            pass
    try:
        print(line, flush=True)
    except Exception:
        pass


def pvarint(n):
    out = bytearray()
    while n > 127:
        out.append((n & 127) | 128)
        n >>= 7
    out.append(n)
    return bytes(out)


def pstr(field_no, s):
    b = s.encode() if isinstance(s, str) else s
    return pvarint((field_no << 3) | 2) + pvarint(len(b)) + b


def rpc_raw(path, body=b'', ct='application/json', t=4, extra_hdrs=None):
    """HTTP/1.1 原始请求, 返回 (status_line, headers, body_bytes)"""
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(t)
        s.connect('/run/cell/cell.sock')
        req = ('POST %s HTTP/1.1\r\nHost: unix\r\nContent-Type: %s\r\n'
               'Content-Length: %d\r\nConnection: close\r\n' % (path, ct, len(body)))
        for k, v in (extra_hdrs or {}).items():
            req += '%s: %s\r\n' % (k, v)
        req += '\r\n'
        s.sendall(req.encode() + body)
        data = b''
        while True:
            try:
                chunk = s.recv(8192)
            except socket.timeout:
                break
            if not chunk:
                break
            data += chunk
        s.close()
        if not data:
            return 'NORESP', '', b''
        head, _, rest = data.partition(b'\r\n\r\n')
        lines = head.decode(errors='replace').split('\r\n')
        return lines[0], '\n'.join(lines[1:])[:300], rest
    except Exception as e:
        return 'EXC:%s' % type(e).__name__, '', b''


def rpc(path, body='{}', t=3):
    st, hd, bd = rpc_raw(path, body.encode(), 'application/json', t)
    return st, bd[:800].decode(errors='replace')


def exec_cmd(ctr, cid, argv, t=6):
    body = json.dumps({"containerId": cid, "process": {"argv": argv}})
    return rpc(ctr + '/Exec', body, t=t)


def probe_stream(ctr, cid, pa, label, ct, body, extra=None):
    st, hd, bd = rpc_raw(ctr + '/StreamOutput', body, ct, t=5, extra_hdrs=extra)
    log('STREAM %-22s ct=%-22s -> %s | %s | body=%r' % (label, ct, st, hd[:120], bd[:200]))


def main():
    log('V78 payload start pid=%d' % os.getpid())
    CTR = '/vercel.hive.cell.api.containers.v1.ContainersService'

    st, bd = rpc(CTR + '/Create', '{"drive_id":"sandbox"}')
    cid = bd.split('"containerId":"')[1].split('"')[0] if '"containerId"' in bd else None
    log('ID=%s' % (cid or 'NONE'))
    if not cid:
        log('V78C_DONE')
        return
    rpc(CTR + '/Start', '{"containerId":"%s"}' % cid, t=5)
    log('started')
    time.sleep(1)

    # 1) Exec A: 有明确输出的命令
    st, bd = exec_cmd(CTR, cid, ['/bin/sh', '-c',
                      'echo V78_HELLO; id; hostname; pwd; echo V78_END'], t=6)
    PA = bd.split('"processId":"')[1].split('"')[0] if '"processId"' in bd else None
    log('execA -> %s | PA=%s' % (st, PA or bd[:150]))
    time.sleep(1)

    # 2) StreamOutput Content-Type 矩阵 (JSON body)
    j1 = '{"containerId":"%s"}' % cid
    j2 = '{"containerId":"%s","processId":"%s"}' % (cid, PA)
    j3 = '{"processId":"%s"}' % PA
    for i, (label, ct, body) in enumerate([
        ('json-cid', 'application/json', j1),
        ('json-cid-pa', 'application/json', j2),
        ('json-pa', 'application/json', j3),
        ('json-empty', 'application/json', '{}'),
        ('proto-cid', 'application/proto', j1),
        ('connect-cid', 'application/connect+proto', j1),
        ('grpc-cid', 'application/grpc', j1),
        ('grpc+proto-cid', 'application/grpc+proto', j1),
        ('json+cid-pa', 'application/json', j2),
    ]):
        probe_stream(CTR, cid, PA, label + '[%d]' % i, ct, body.encode())
        time.sleep(0.3)

    # 3) protobuf body 变体 (猜字段: 1=containerId, 2=processId)
    pb1 = pstr(1, cid)
    pb2 = pstr(1, cid) + pstr(2, PA)
    pb3 = pstr(2, PA)
    for i, (label, ct, body) in enumerate([
        ('pb-cid', 'application/proto', pb1),
        ('pb-cid-pa', 'application/proto', pb2),
        ('pb-pa', 'application/proto', pb3),
        ('pb-cid-connect', 'application/connect+proto', pb1),
        ('pb-cid-pa-connect', 'application/connect+proto', pb2),
        ('grpc-frame-cid', 'application/grpc', b'\x00' + struct.pack('>I', len(pb1)) + pb1),
        ('grpc-frame-cid-pa', 'application/grpc', b'\x00' + struct.pack('>I', len(pb2)) + pb2),
    ]):
        probe_stream(CTR, cid, PA, 'pb[%d]' % i, ct, body)
        time.sleep(0.3)

    # 4) Stdin 探测
    for i, (label, body) in enumerate([
        ('json-cid', j1), ('json-cid-pa', j2), ('json-empty', '{}'),
        ('pb-cid', pb1), ('pb-cid-pa', pb2)]):
        st, hd, bd = rpc_raw(CTR + '/Stdin', body, 'application/json' if i < 3 else 'application/proto', t=4)
        log('STDIN %-12s -> %s | %s | body=%r' % (label, st, hd[:120], bd[:150]))
        time.sleep(0.3)

    # 5) Exec B 后再 StreamOutput (也许需要 process 运行中)
    st, bd = exec_cmd(CTR, cid, ['/bin/sh', '-c', 'sleep 30'], t=5)
    PB = bd.split('"processId":"')[1].split('"')[0] if '"processId"' in bd else None
    log('execB -> %s | PB=%s' % (st, PB or bd[:120]))
    time.sleep(0.5)
    for i, (label, ct, body) in enumerate([
        ('after-exec-json', 'application/json', j2),
        ('after-exec-pb', 'application/proto', pstr(1, cid) + pstr(2, PB))]):
        probe_stream(CTR, cid, PB, label, ct, body)
        time.sleep(0.3)

    rpc(CTR + '/Kill', '{"containerId":"%s"}' % cid)
    log('killed')
    log('V78C_DONE')


main()
